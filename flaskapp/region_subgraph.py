"""
    Assemble a graph from API calls
"""

import collections
import logging
import string

import networkx as nx
import special_nodes
import wikidata_interfaces


logging.basicConfig(level=logging.DEBUG)


class RegionSubGraph(object):
    """
        Biuld a subgraph around a set of seed nodes
    """

    def __str__(self):
        output = "Region of {num_neighbors} nodes surrounding\n\t{seeds}"

        print_nodes = [str(i) for i in sorted(self.seed_nodes)[:20]]
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

        self.add_seeds(seed_nodes)

    def add_seeds(self, nodes):
        nodes = {
            n.replace(" ", "_")
            for n in nodes
        }
        self.seed_nodes.update(nodes)
        self.graph.add_nodes_from(nodes)
        return self

    def filter_nodes_by_blacklist(self):

        bl_nodes = {
            n
            for n in self.graph.nodes
            if n in special_nodes.NODE_BLACKLIST
        }

        list_nodes = {
            n
            for n in self.graph.nodes
            if n.startswith('List_')
        }

        nonchar_nodes = {
            n
            for n in self.graph.nodes
            if not any(c in n for c in string.ascii_letters)
        }

        bad_nodes = set.union(
            bl_nodes,
            list_nodes,
            nonchar_nodes
        )

        self.graph.remove_nodes_from(bad_nodes - self.seed_nodes)

    def dilate(self, inbound=True, outbound=True):

        orig_nodes = set(self.graph.nodes)
        nodes_to_visit = set()
        if inbound and outbound:
            fully_visited_nodes = self.visited_nodes_ib.intersection(
                self.visited_nodes_ob
            )
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
        return self


class RegionSubGraphPlusDistanceFilter(RegionSubGraph):
    """
        Biuld a subgraph around a set of seed nodes but also
        include the ability for filtering out nodes by distance
    """

    def __init__(self, lat, lon, num_nearby=10):
        self.dist_finder = wikidata_interfaces.CoordinateFinder()
        self.geo_finder = wikidata_interfaces.NearbyFinder()
        self.latlon = (lat, lon)
        self.node_dists = {}
        super().__init__(self._lookup_nearby(num_nearby))

    def _lookup_nearby(self, num_nearby):
        return self.geo_finder.get_payload(*self.latlon, num_nearby)

    def _update_dists(self):

        nodes_without_dists = set(self.graph.nodes) - set(self.node_dists)
        node_dists = self.dist_finder.get_payload(
            nodes_without_dists, self.latlon
        )

        page_dists = collections.defaultdict(list)
        for node, dist in node_dists:
            page_dists[node].append(dist)

        min_dists = {node: -1 for node in nodes_without_dists}

        for key, val in page_dists.items():
            min_dists[key] = min(val) if val else -1

        self.node_dists.update(min_dists)

        return nodes_without_dists

    def filter_nodes_by_distance(self, max_dist=5000):
        nodes_with_new_dists = self._update_dists()

        bad_nodes = {
            n
            for n in nodes_with_new_dists
            if self.node_dists.get(n, -1) > max_dist
        }

        self.graph.remove_nodes_from(bad_nodes - self.seed_nodes)
