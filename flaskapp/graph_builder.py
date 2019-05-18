"""
    Assemble a graph from API calls
"""
import abc
import collections
import functools
import itertools

import networkx as nx
import sql_interfaces
import wikidata_interfaces


class BaseLookupInterface(abc.ABC):

    def __init__(self):
        self.inbound_link_finder = None
        self.outbound_link_finder = None
        self.cat_finder = None

    @functools.lru_cache(maxsize=10000)
    def _get_node_outbound(self, node):
        links = self.outbound_link_finder.get_payload(node)
        return links

    @functools.lru_cache(maxsize=10000)
    def _get_node_inbound(self, node):
        links = self.inbound_link_finder.get_payload(node)
        return links

    def get_node_links(self, node, outbound=True, inbound=True):

        links = []

        if outbound:
            links.extend(
                (node, ol) for ol in self._get_node_outbound(node)
            )

        if inbound:
            links.extend(
                (il, node) for il in self._get_node_inbound(node)
            )

        return links

    def get_multinode_links(self, nodes, outbound=True, inbound=True):
        results_per_node = []
        for node in nodes:
            results_per_node.extend(
                self.get_node_links(node, outbound=outbound, inbound=inbound)
            )
        
        return results_per_node

    @functools.lru_cache(maxsize=10000)
    def get_node_categories(self, node):
        return {node: self.cat_finder.get_payload(node)}

    def get_multinode_categories(self, nodes):
        categories_per_node = collections.ChainMap(
            self.get_node_categories(node)
            for node in nodes
        )
        return dict(categories_per_node)


class ApiLookupInterface(BaseLookupInterface):

    def __init__(self):
        self.inbound_link_finder = wikidata_interfaces.InLinkFinder()
        self.outbound_link_finder = wikidata_interfaces.OutLinkFinder()
        self.cat_finder = wikidata_interfaces.CategoryFinder()


class SqlLookupInterface(BaseLookupInterface):

    def __init__(self):
        self.inbound_link_finder = sql_interfaces.InLinkFinder()
        self.outbound_link_finder = sql_interfaces.OutLinkFinder()
        self.cat_finder = wikidata_interfaces.CategoryFinder() #sql_interfaces.CategoryFinder()


class SeedRegionGraph(object):
    """
        Graph of all articles surrounding a some 
        nodes that form a seed region
    """

    _EXCLUDE_NODE_CATEGORIES = {
        'category:identifiers',
        'category:unique identifiers',
        'category:iso standards',
        'category:geocodes',
        'category:library cataloging and classification',
    }

    _EXCLUDE_NODE_CATEGORY_SUBSTRINGS = {
        'category:list',
    }

    _IGNORE_CATEGORIES = {}
    _IGNORE_CATEGORY_SUBSTRINGS = {
        "wiki",
        "article",
        "cs1",
        "pages",
        "redirect",
        "infobox",
        "link",
        "deprecated",
        "template",
        "list"
    }

    def __str__(self):
        output = "Region of {num_neighbors} nodes surrounding\n\t{seeds}"
        return output.format(
            num_neighbors=len(self.graph),
            seeds="\n\t".join(self.seed_nodes)
        )

    def __init__(self, lookup_interface):
        self.seed_nodes = set()
        self.graph = nx.DiGraph()
        self.visited_nodes_ib = set()
        self.visited_nodes_ob = set()
        self.node_categories = {}
        self.lookup_interface = lookup_interface
        self.category_summary = collections.Counter()

    def _remove_and_bypass_node(self, node):
        inbound_nodes = [e[0] for e in self.graph.in_edges(node)]
        outbound_nodes = [e[1] for e in self.graph.out_edges(node)]
        new_edges = itertools.product(inbound_nodes, outbound_nodes)
        self.graph.add_edges_from(new_edges)
        self.graph.remove_node(node)

    def add_seeds(self, nodes):
        self.seed_nodes.update(nodes)
        self.graph.add_nodes_from(nodes)
        self._update_categories()
        self._update_category_summary()
        return self

    @staticmethod
    def _filter_categories(input_values, exclude_match, exclude_substrings):
        output_values = []
        for input_value in input_values:
            lower_value = input_value.lower()
            bad_value = lower_value in exclude_match or any(s in lower_value for s in exclude_substrings)
            if not bad_value:
                output_values.append(input_value)
        return output_values

    def _check_node_is_redirect(self, node):
        return (
            node in self.graph and
            node not in self.seed_nodes and 
            self.graph.out_degree[node] == 1
        )

    def _update_categories(self):
        nodes_missing_cats = {
            node
            for node in self.graph
            if node not in self.node_categories
        }

        new_node_categories = self.lookup_interface.get_multinode_categories(nodes_missing_cats)

        filtered_node_categories = {
            node: self._filter_categories(
                cats,
                self._IGNORE_CATEGORIES,
                self._IGNORE_CATEGORY_SUBSTRINGS)
            for node, cats in new_node_categories.items() 
        }

        self.node_categories.update(filtered_node_categories)        

    def _update_category_summary(self):
        self.category_summary = collections.Counter(
            cat
            for node in self.graph
            for cat in self.node_categories[node]
        )

    def _remove_listy_nodes(self):

        listy_nodes = []
        for node, catlist in self.node_categories.items():
            clean_catlist = self._filter_categories(catlist,
                self._EXCLUDE_NODE_CATEGORIES,
                self._EXCLUDE_NODE_CATEGORY_SUBSTRINGS)

            if node.startswith('List'):
                listy_nodes.append(node)
            elif clean_catlist != catlist:
                listy_nodes.append(node)

        self.graph.remove_nodes_from(listy_nodes)

    def _prune(self):
        self._update_categories()
        self._remove_listy_nodes()

        isolated_nodes = nx.isolates(self.graph)
        self.graph.remove_nodes_from(isolated_nodes)

        fully_visited_nodes = self.visited_nodes_ib.intersection(self.visited_nodes_ob)
        nodes_to_check = set(self.graph.nodes) - fully_visited_nodes
        for node in nodes_to_check:
            if self._check_node_is_redirect(node):
                self._remove_and_bypass_node(node)

        self._update_category_summary()

    def dilate(self, inbound=True, outbound=True):

        if inbound and outbound:
            fully_visited_nodes = self.visited_nodes_ib.intersection(self.visited_nodes_ob)
            nodes_to_visit = set(self.graph.nodes) - fully_visited_nodes
        elif inbound:
            nodes_to_visit = set(self.graph.nodes) - self.visited_nodes_ib
        elif outbound:
            nodes_to_visit = set(self.graph.nodes) - self.visited_nodes_ob

        new_edges = self.lookup_interface.get_multinode_links(
            nodes_to_visit, outbound=outbound, inbound=inbound)

        self.graph.add_edges_from(new_edges)

        if inbound:
            self.visited_nodes_ib.update(nodes_to_visit)

        if outbound:
            self.visited_nodes_ob.update(nodes_to_visit)

        self._prune()
        return self


class ArticleGraph(object):

    def __str__(self):
        out_str = "FROM/ORIGIN:\n{}\n\nTO/GOAL:\n{}".format(
            self.origin,
            self.goal
        )
        return out_str

    def __init__(self, geo_kwargs=None):

        geo_kwargs = {} if not isinstance(geo_kwargs, dict) else geo_kwargs

        self.geo_lookup = api_interfaces.NearbyFinder(**geo_kwargs)
        self.link_lookup = ApiLookupInterface()

        self.origin = SeedRegionGraph(self.link_lookup)
        self.goal = SeedRegionGraph(self.link_lookup)

    def add_location_from_latlon(self, latitude, longitude):
        nearby_nodes = self.geo_lookup.get_payload(latitude, longitude)
        self.origin.add_seeds(nearby_nodes)

    def add_location_from_text(self, origin_nodes):
        self.origin.add_seeds(origin_nodes)

    def add_goals(self, goal_nodes):
        self.goal.add_seeds(goal_nodes)

    def grow(self):
        print('dilating origins')
        self.origin.dilate(inbound=True, outbound=True)
        #print('dilating origins forward only')
        #self.origin.dilate(inbound=False, outbound=True)

        print('dilating goals')
        self.goal.dilate(inbound=True, outbound=True)
        #print('dilating goals forward only')
        #self.goal.dilate(inbound=False, outbound=True)

        return self

    def get_full_graph(self):

        full_graph = nx.compose(
            self.origin.graph,
            self.goal.graph
        )

        return full_graph
