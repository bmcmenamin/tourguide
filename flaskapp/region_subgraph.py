"""
    Assemble a graph from API calls
"""
import abc
import collections
import logging
import string

import networkx as nx
import special_nodes
import wikidata_interfaces


logging.basicConfig(level=logging.INFO)


class RegionSubGraph(abc.ABC):
    """
        Biuld a subgraph around a set of seed nodes
    """

    def __str__(self):

        print_nodes = [str(i) for i in sorted(self.seed_nodes)[:20]]
        if len(self.seed_nodes) > 20:
            print_nodes.append("...")

        return f"Region of {len(self.graph)} nodes surrounding\n\t{"\n\t".join(print_nodes)}"

    def __init__(self):
        self.seed_nodes = set()
        self.graph = nx.DiGraph()

        self.visited_nodes_ib = set()
        self.visited_nodes_ob = set()

        self.inbound_link_finder = wikidata_interfaces.InLinkFinder()
        self.outbound_link_finder = wikidata_interfaces.OutLinkFinder()

    def add_seeds(self, nodes: List[int]):
        nodes = {n for n in nodes}
        self.seed_nodes.update(nodes)
        self.graph.add_nodes_from(nodes)
        return self

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
            new_edges = [
                (ed['x0'], ed['x1'])
                for ed in self.outbound_link_finder.get_payload(nodes_to_visit)
            ]
            self.graph.add_edges_from(new_edges)
            self.visited_nodes_ob.update(nodes_to_visit)

        if inbound:
            new_edges = [
                (ed['x1'], ed['x0'])
                for ed in self.inbound_link_finder.get_payload(nodes_to_visit)
            ]
            self.graph.add_edges_from(new_edges)
            self.visited_nodes_ib.update(nodes_to_visit)

        new_nodes = set(self.graph.nodes) - orig_nodes
        return self


class RegionSubGraphByName(RegionSubGraph):
    """
        Build a subgraph around a set of seed nodes
    """

    def __init__(self, seed_nodes):
        super().__init__()
        self.add_seeds(seed_nodes)


class RegionSubGraphByNearby(RegionSubGraph):
    """
        Biuld a subgraph around a set of seed nodes but also
        include the ability for filtering out nodes by distance
    """

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

    def __init__(self, latlon, num_nearby):
        super().__init__()

        self.dist_finder = wikidata_interfaces.CoordinateFinder()
        self.geo_finder = wikidata_interfaces.NearbyFinder()

        self.latlon = latlon
        self.node_dists = {}

        nearby = self._lookup_nearby(num_nearby)
        self.add_seeds(nearby)
