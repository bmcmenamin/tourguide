"""
    Assemble a graph from API calls
"""
import collections
import logging
from typing import List, Dict, Any, Tuple, Self

import networkx as nx

from region_subgraph import RegionSubGraphByName, RegionSubGraphByNearby


logging.basicConfig(level=logging.INFO)


def lols_to_dods(lols: List[List[Any]]) -> Dict[Any, Dict[Any, Any]]:
    temp_dict = collections.defaultdict(list)
    for l in lols:
        if len(l) == 1:
            temp_dict[l[0]].append([])
        elif len(l) > 1:
            temp_dict[l[0]].append(l[1:])

    if temp_dict:
        return {
            key: lols_to_dods(val)
            for key, val in temp_dict.items()
        }

    return sorted([l[0] for l in lols if len(l) == 1])


def dod_to_nestedlists(in_dod: Dict[Any, Dict[Any, Any]]) -> List[Tuple[Any, List[Any]]]:

    if isinstance(in_dod, list):
        return in_dod

    return [
        [key, dod_to_nestedlists(val)]
        for key, val in in_dod.items()
    ]


class ArticleNetwork(object):

    def __str__(self):
        return f"FROM/NEARBY:\n{self.nearby}\n\nTO/TARGET:\n{self.topics}"

    def __init__(self,  latlon: Tuple[float, float], **kwargs):
        self.latlon = latlon
        self.nearby = None
        self.topics = None
        self.all_paths = None

    def add_nearby(self, num_nearby: int = 10) -> Self:
        self.nearby = RegionSubGraphByNearby(self.latlon, num_nearby)
        return self

    def add_topics(self, topic_nodes: List[str]) -> Self:
        self.topics = RegionSubGraphByName(topic_nodes)
        return self

    def grow(self) -> Self:
        logging.info("dilating nearby")
        self.nearby.dilate(inbound=True, outbound=True)
        self.nearby.filter_nodes_by_blacklist()
        self.nearby.filter_nodes_by_distance()

        logging.info("dilating topics")
        self.topics.dilate(inbound=True, outbound=True)
        self.topics.filter_nodes_by_blacklist()

        return self

    def _get_paths_to_topic(self, graph: nx.DiGraph, end_node: str) -> List[List[str]]:

        seeds = self.nearby.seed_nodes.union(self.topics.seed_nodes)
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

    def find_all_paths(self) -> Self:

        full_graph = nx.compose(
            self.nearby.graph,
            self.topics.graph
        )

        full_graph_undir = (
            full_graph.
            to_undirected(reciprocal=False, as_view=False)
        )

        logging.info("Looking for paths")
        self.all_paths = {
            topics: self._get_paths_to_topic(full_graph_undir, topics)
            for topics in self.topics.seed_nodes
        }
        return self

    def get_nested_paths(self) -> Dict[str, List[List[Any]]]:

        responses = {
            "nested_lists_by_nearby": dod_to_nestedlists(
                lols_to_dods(
                    path
                    for pathlist in self.all_paths.values()
                    for path in pathlist
                )
            ),

            "nested_lists_by_topic": dod_to_nestedlists(
                lols_to_dods(
                    path[::-1]
                    for pathlist in self.all_paths.values()
                    for path in pathlist
                )
            )
        }

        return responses

    def path_status(self) -> str:

        if isinstance(self.all_paths, dict):
            has_a_path = any(len(pl) > 0 for pl in self.all_paths.values())
            if has_a_path:
                return 'has_paths'
            return 'no_paths'
        return 'unknown'
