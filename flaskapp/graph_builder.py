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

    def _get_node_outbound(self, nodes, batch_size=15):

        nodes = list(nodes)
        links = []
        for idx in range(0, len(nodes), batch_size):
            batch = nodes[idx: (idx + batch_size)]
            links += self.outbound_link_finder.get_payload({"nodes": batch})
        return links

    def _get_node_inbound(self, nodes, batch_size=5):
        nodes = list(nodes)
        links = []
        for idx in range(0, len(nodes), batch_size):
            batch = nodes[idx: (idx + batch_size)]
            links += self.inbound_link_finder.get_payload({"nodes": batch})
        return links

    def get_node_links(self, nodes, outbound=True, inbound=True):

        links = []

        if outbound:
            links.extend(self._get_node_outbound(nodes))

        if inbound:
            links.extend(self._get_node_inbound(nodes))

        return links

    def get_node_categories(self, nodes, batch_size=10):
        nodes = list(nodes)
        results = {}
        for idx in range(0, len(nodes), batch_size):
            batch = nodes[idx: (idx + batch_size)]
            results.update(
                self.cat_finder.get_payload({"nodes": batch})
            )
        return results

    def get_node_attrs(self, nodes, batch_size=10):
        nodes = list(nodes)
        results = {}
        for idx in range(0, len(nodes), batch_size):
            batch = nodes[idx: (idx + batch_size)]
            results.update(
                self.node_attr_finder.get_payload({"nodes": batch})
            )
        return results

class SqlLookupInterface(BaseLookupInterface):

    def __init__(self):
        self.inbound_link_finder = sql_interfaces.InLinkFinder()
        self.outbound_link_finder = sql_interfaces.OutLinkFinder()
        self.cat_finder = sql_interfaces.CategoryFinder()
        self.node_attr_finder = sql_interfaces.NodeAttributeFinder()


class SeedRegionGraph(object):
    """
        Graph of all articles surrounding a some 
        nodes that form a seed region
    """

    BAD_CATEGORIES = {
        'identifiers',
        'unique_identifiers',
        'iso_standards',
        'geocodes',
        'library_cataloging_and_classification',
    }

    BAD_CATEGORY_PREFIX = {
        'list',
    }

    _MAX_IN_DEGREE = 10000
    _MAX_OUT_DEGREE = 1000

    def __str__(self):
        output = "Region of {num_neighbors} nodes surrounding\n\t{seeds}"
        return output.format(
            num_neighbors=len(self.graph),
            seeds="\n\t".join(self.seed_nodes)
        )

    def __init__(self, lookup_interface):
        self.seed_nodes = set()
        self.graph = nx.DiGraph()
        self.node_attr = {}
        self.visited_nodes_ib = set()
        self.visited_nodes_ob = set()
        self.node_categories = {}
        self.lookup_interface = lookup_interface

    def add_seeds(self, nodes):
        self.seed_nodes.update(nodes)
        self.graph.add_nodes_from(nodes)
        self._update_categories()
        self._update_attr()
        self._remove_listy_nodes()
        return self

    def _remove_listy_nodes(self):

        listy_nodes = []
        for node, catlist in self.node_categories.items():

            catlist_clean = {c.lower() for c in catlist}

            if node.lower().startswith('list'):
                listy_nodes.append(node)
            elif catlist_clean.intersection(self.BAD_CATEGORIES):
                listy_nodes.append(node)
            elif any(c1.startswith(c2) for c1, c2 in itertools.product(catlist_clean, self.BAD_CATEGORY_PREFIX)):
                listy_nodes.append(node)

        for node, attr in self.node_attr.items():
            if node not in self.seed_nodes:
                if attr['in_degree'] > self._MAX_IN_DEGREE:
                    listy_nodes.append(node)
                elif attr['out_degree'] > self._MAX_OUT_DEGREE:
                    listy_nodes.append(node)

        self.graph.remove_nodes_from(listy_nodes)


    def _update_categories(self):
        nodes_missing_cats = {
            node
            for node in self.graph
            if node not in self.node_categories
        }

        new_node_cats = self.lookup_interface.get_node_categories(nodes_missing_cats)
        self.node_categories.update(new_node_cats)

    def _update_attr(self):
        nodes_missing_attr = {
            node
            for node in self.graph
            if node not in self.node_attr
        }

        new_node_attrs = self.lookup_interface.get_node_attrs(nodes_missing_attr)
        for page_title, (in_deg, out_deg) in new_node_attrs.items():
            self.node_attr[page_title] = {
                'in_degree': in_deg,
                'out_degree': out_deg
            }

    def dilate(self, inbound=True, outbound=True):

        if inbound and outbound:
            fully_visited_nodes = self.visited_nodes_ib.intersection(self.visited_nodes_ob)
            nodes_to_visit = set(self.graph.nodes) - fully_visited_nodes
        elif inbound:
            nodes_to_visit = set(self.graph.nodes) - self.visited_nodes_ib
        elif outbound:
            nodes_to_visit = set(self.graph.nodes) - self.visited_nodes_ob

        new_edges = self.lookup_interface.get_node_links(
            nodes_to_visit,
            outbound=outbound,
            inbound=inbound)

        self.graph.add_edges_from(new_edges)

        if inbound:
            self.visited_nodes_ib.update(nodes_to_visit)

        if outbound:
            self.visited_nodes_ob.update(nodes_to_visit)

        self._update_categories()
        self._update_attr()
        self._remove_listy_nodes()
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

        self.geo_lookup = sql_interfaces.NearbyFinder(**geo_kwargs)
        self.city_lookup = sql_interfaces.CityFinder(**geo_kwargs)

        self.link_lookup = SqlLookupInterface()
        self.origin = SeedRegionGraph(self.link_lookup)
        self.goal = SeedRegionGraph(self.link_lookup)

    def add_location_from_latlon(self, latitude, longitude, num_nearby, num_cities):
        nearby_nodes = self.geo_lookup.get_payload({
            "lat": latitude,
            "lon": longitude,
            "n": num_nearby
        })
        nearby_nodes += self.city_lookup.get_payload({
            "lat": latitude,
            "lon": longitude,
            "n": num_cities
        })
        self.origin.add_seeds(nearby_nodes)

    def add_location_from_text(self, origin_nodes):
        self.origin.add_seeds(origin_nodes)

    def add_goals(self, goal_nodes):
        self.goal.add_seeds(goal_nodes)

    def grow(self):
        print('dilating origins')
        self.origin.dilate(inbound=True, outbound=True)

        print('dilating goals')
        self.goal.dilate(inbound=True, outbound=True)

        return self

    def get_full_graph(self):

        full_graph = nx.compose(
            self.origin.graph,
            self.goal.graph
        )

        return full_graph
