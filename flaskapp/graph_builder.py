"""
    Assemble a graph from API calls
"""
import abc
import collections
import functools
import itertools
import re

import networkx as nx
import special_nodes
import wikidata_interfaces


REGEX_STRING_LIST = re.compile(r"\blist(s)?\b", re.IGNORECASE)


class SeedRegionGraph(object):
    """
        Seed region subgraph
    """

    def __str__(self):
        output = "Region of {num_neighbors} nodes surrounding\n\t{seeds}"

        print_nodes = [str(i) for i in  sorted(self.seed_nodes)[:20]]
        if len(self.seed_nodes) > 20:
            print_nodes.append("...")

        return output.format(
            num_neighbors=len(self.graph),
            seeds="\n\t".join(print_nodes)
        )

    def __init__(self, seed_nodes):
        self.seed_nodes = set()
        self.graph = nx.DiGraph()

        self.visited_nodes_ib = set()
        self.visited_nodes_ob = set()

        self.inbound_link_finder = wikidata_interfaces.InLinkFinder()
        self.outbound_link_finder = wikidata_interfaces.OutLinkFinder()
        self.cat_finder = wikidata_interfaces.CategoryFinder()
        self.dist_finder = wikidata_interfaces.CoordinateFinder()

        self.node_cats = {}
        self.node_dists = {}
        self.latlon = None

        self.add_seeds(seed_nodes)

    def _update_categories(self):

        nodes_without_cats = set(self.graph.nodes) - set(self.node_cats)
        node_cats = self.cat_finder.get_payload(nodes_without_cats)

        new_cats = collections.defaultdict(list)
        for node, cat in node_cats:
            if cat.startswith('Category:'):
                cat = cat[9:]
            new_cats[node].append(cat)

        self.node_cats.update(new_cats)

        return nodes_without_cats

    def _update_dists(self):

        nodes_without_dists = set(self.graph.nodes) - set(self.node_dists)
        node_dists = self.dist_finder.get_payload(nodes_without_dists, self.latlon)

        new_dists = {}
        for node, dist in node_dists:
            if node not in new_dists:
                new_dists[node] = dist
            else:
                new_dists[node] = min(new_dists[node], dist)

        self.node_dists.update(new_dists)

        return nodes_without_dists

    def _filter_nodes(self, use_category_fitlering=False, use_distance_filtering=False):
        bad_nodes = special_nodes.NODE_BLACKLIST.intersection(self.graph.nodes)
        for n in self.graph.nodes:
            if n.startswith('List '):
                bad_nodes.add(n)

        self.graph.remove_nodes_from(bad_nodes)

        if use_category_fitlering:
            self._filter_nodes_by_category()

        if use_distance_filtering:
            self._filter_nodes_by_distance()

    def _filter_nodes_by_category(self):
        nodes_with_new_cats = self._update_categories()
        bad_nodes = set()
        for n in nodes_with_new_cats:
            node_cats = self.node_cats.get(n, [])
            if any(REGEX_STRING_LIST.search(cat) for cat in node_cats):
                bad_nodes.add(n)

        self.graph.remove_nodes_from(bad_nodes)

    def _filter_nodes_by_distance(self, max_dist=10000):
        nodes_with_new_dists = self._update_dists()

        bad_nodes = {
            n
            for n in nodes_with_new_dists
            if self.node_dists.get(n, -1) > max_dist
        }

        self.graph.remove_nodes_from(bad_nodes)

    def dilate(self, inbound=True, outbound=True):

        orig_nodes = set(self.graph.nodes)
        nodes_to_visit = set()
        if inbound and outbound:
            fully_visited_nodes = self.visited_nodes_ib.intersection(self.visited_nodes_ob)
            nodes_to_visit = orig_nodes - fully_visited_nodes
        elif inbound:
            nodes_to_visit = orig_nodes - self.visited_nodes_ib
        elif outbound:
            nodes_to_visit = orig_nodes - self.visited_nodes_ob

        if outbound:
            new_edges = self.outbound_link_finder.get_payload(nodes_to_visit)
            self.graph.add_edges_from(new_edges)
            self.visited_nodes_ob.update(nodes_to_visit)

        if inbound:
            new_edges = self.inbound_link_finder.get_payload(nodes_to_visit)
            self.graph.add_edges_from(new_edges)
            self.visited_nodes_ib.update(nodes_to_visit)

        new_nodes = set(self.graph.nodes) - orig_nodes

        self._filter_nodes()
        return self

    def set_latlon(self, lat, lon):
        self.latlon = (lat, lon)

    def add_seeds(self, nodes):
        nodes = {
            n.replace(" ", "_")
            for n in nodes
        }
        self.seed_nodes.update(nodes)
        self.graph.add_nodes_from(nodes)
        self._filter_nodes()
        return self


class ArticleGraph(object):

    def __str__(self):
        out_str = "FROM/NEARBY:\n{}\n\nTO/TARGET:\n{}".format(
            self.nearby,
            self.target
        )
        return out_str

    def __init__(self, *args, **kwargs):
        self.geo_lookup = wikidata_interfaces.NearbyFinder()
        self.nearby = None
        self.target = None

        self.all_paths = {}
        self.path_graphs = {}

    def add_nearby(self, lat, lon, num_nearby=10):
        nearby_nodes = self.geo_lookup.get_payload(lat, lon, num_nearby=num_nearby)
        self.nearby = SeedRegionGraph(nearby_nodes)
        self.nearby.set_latlon(lat, lon)
        return self

    def add_targets(self, target_nodes):
        self.target = SeedRegionGraph(target_nodes)
        return self

    def grow(self):
        print('dilating nearby')
        self.nearby.dilate(inbound=True, outbound=False)

        print('dilating targets')
        self.target.dilate(inbound=True, outbound=True)

        return self

    def _get_full_graph(self):

        full_graph = nx.compose(
            self.nearby.graph,
            self.target.graph
        )

        return full_graph

    def _get_paths_to_target(self, graph, end_node):

        seeds = self.nearby.seed_nodes.union(self.target.seed_nodes)
        inter_nodes = set(graph.nodes) - seeds

        paths = []
        for start_node in self.nearby.seed_nodes:
            _graph = graph.subgraph(inter_nodes.union({start_node, end_node}))
            _paths = nx.algorithms.simple_paths.all_simple_paths(
                _graph,
                start_node,
                end_node,
                cutoff=2
            )
            paths.extend(_paths)

        return paths

    def find_all_paths(self):

        full_graph = self._get_full_graph()
        full_graph_undir = (
            full_graph.
            to_undirected(reciprocal=False, as_view=False)
        )

        print('finding paths')
        self.all_paths = {
            targ: self._get_paths_to_target(full_graph_undir, targ)
            for targ in self.target.seed_nodes
        }

        print('building pathgraphs')
        self.path_graphs = {}
        for targ, paths in self.all_paths.items():
            path_nodes = {node for path in paths for node in path}
            self.path_graphs[targ] = full_graph.subgraph(path_nodes)

        return self
