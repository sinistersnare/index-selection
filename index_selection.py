#!/usr/bin/env python3

from typing import FrozenSet, Tuple, Iterator, Dict, Set, Optional, List, Union
import itertools
import json

import networkx as nx

class Node:
    """
    A node in a bipartite graph, that distinguishes if its on the left or right.
    """
    def __init__(self, right: bool, value: Tuple[int]):
        self.right = right
        self.value = value

    def __str__(self):
        return "<Node:{}.{}>".format("right" if self.right else "left", self.value)
    __repr__ = __str__

    # A node is less than another node if its a lexicographic subset
    # (0,2) is not a lex-ss of (0,1,2),
    # (0,) and (0,1) are.
    # (0,2) is a lex-ss of (0,2,3).
    # (0,2) is not a lex-ss of (0,2), must be a proper subset.
    def __lt__(self, other):
        return set(self.value) < set(other.value)

    def __hash__(self):
        return (self.right, self.value).__hash__()

    def __eq__(self, other):
        return self.right == other.right and self.value == other.value


class Search:
    """TODO: Docs! DO TESTS ALSO!
    A search is a single search in a clause's body, with grounded variables positions.
    so in the body if we see S0(x), then the clause will have
    R(x, y) :- S0(x, y, 1) S1(1, y, x)
    `name = S0` and `parameters = {0, 1}`
    `name = S1` and `parameters = {1, 2}`
    """
    def __init__(self, name: str, parameters: List[int]):
        self.name = name
        self.parameters = parameters

    def __str__(self):
        return "Search<name:{},parameters:{}>".format(
            self.name, self.parameters)
    __repr__ = __str__

def form_search(raw_search: str) -> Search:
    """TODO: DOCS! tESTs!
    Takes something like "S0(x,y)", returns a Search object.
    """
    name_end = raw_search.find('(')
    name = raw_search[:name_end]
    raw_params = raw_search[name_end+1:-1]
    raw_list = raw_params.split(',')
    # Take everything except `_` into account of the join.
    params = sorted([idx for (idx, p) in enumerate((x.strip() for x in raw_list))
                                                                if p != '_'])
    return Search(name, params)

def get_search_usages(searches: List[Search]) -> Dict[str, List[Tuple[int]]]:
    """TODO: DOCS! AND TESTS??!?!?!?"""
    search_usages = {}
    for search in searches:
        params = tuple(search.parameters)
        if search.name in search_usages:
            if params not in search_usages[search.name]:
                search_usages[search.name].append(params)
        else:
            search_usages[search.name] = [params]
    return search_usages

def find_max_match(usages: List[Tuple[int]]) -> Union[Dict[Node, Node], List[Tuple[int]]]:
    graph = nx.Graph()
    left_nodes = set()
    for useout in usages:
        for usein in usages:
            left = Node(False, usein)
            right = Node(True, useout)
            if left < right:
                if left not in graph.nodes:
                    # Keep a set of left nodes for the MaxMatch algorithm
                    # This method may produce a disconnected graph in some cases
                    # so we need to tell the algorithm which set is the left side.
                    left_nodes.add(left)
                    graph.add_node(left, bipartite=0)
                if right not in graph.nodes:
                    graph.add_node(right, bipartite=1)
                graph.add_edge(left, right)
    if not graph.nodes:
        # No max-match possible,
        # I think this is a completely disjoint set here,
        # So we just use the given usages as the indexes wholesale.
        return usages
    else:
        # Only take left->right directed edges.
        return {k: v for k,v in nx.bipartite.hopcroft_karp_matching(graph, left_nodes).items()
                        if not k.right}

def construct_largest_chain(cur_chain: List[Tuple[int]], all_searches: List[Tuple[int]]):
    best = cur_chain
    for search in all_searches:
        end_cur = cur_chain[-1]
        if set(end_cur) < set(search):
            all_without = all_searches[:]
            all_without.remove(search)

            new_with = cur_chain[:]
            new_with.append(search)
            with_test = construct_largest_chain(new_with, all_without)
            without_test = construct_largest_chain(cur_chain, all_without)
            best = max((best, with_test, without_test), key=len)
    return best

def min_chain_cover(usages: List[Tuple[int]],
                    max_matches: Union[Dict[Node, Node],
                                       List[Tuple[int]]]) -> List[List[Tuple[int]]]:
    if isinstance(max_matches, list):
        # progagating the disjoint list that we are using as indexes.
        # But wrap it in a list because thats the return type, a list of chains.
        return [[x] for x in max_matches]

    # Get all starting nodes, nothing that is at least second in a max-match.
    max_values = max_matches.values()
    chains = sorted((construct_largest_chain([u], usages) for u in usages
                            if Node(True, u) not in max_values),
                    key=len, reverse=True)

    return chains

def indexify(chains: List[List[Tuple[int]]]) -> List[Tuple[int]]:
    def single_index(chain: List[Tuple[int]]) -> Tuple[int]:
        ordering = [chain[0]]
        index = []
        for i in range(1, len(chain)):
            ordering.append(set(chain[i]) - set(chain[i-1]))
        for o in ordering:
            index += list(o)
        return tuple(index)
    return [single_index(c) for c in chains]

def indexes_for_program(program: str) -> List[Tuple[int]]:
    searches = []
    for line in program.split('\n'):
        headbody = [x.strip() for x in line.split(":-")]
        if len(headbody) == 1:
            # no searches in a clause without a body!
            continue
        searches += [form_search(s) for s in headbody[1].split()]

    usages = get_search_usages(searches)
    max_matches = {k: find_max_match(v) for k, v in usages.items()}
    min_chains = {k: min_chain_cover(usages[k], v) for k, v in max_matches.items()}
    return {k: indexify(v) for k,v in min_chains.items()}

def main():
    simple = """
R0(x,y) :- R1(x,y) R2(x,z)
R0(x,y) :- R1(x,_) R3(y,x)
R3(x,1) :- R0(x,y)
""".strip()

    # Lex should be `z < y < x` here!
    # `x < y < z` gives 2 indexes with 5 columns used
    # `z < y < x` gives 2 indexes with 4 columns used!
    # The problem as states is min(|S|) some index-set S.
    # but i feel like this is a useful metric too? Am I wrong?
    # TODO: construct a pathological case that changing lex order
    #       will make the |S| smaller.
    pathological_lex = """
R0(x,y,z) :- S0(x,_,_)
R0(x,y,z) :- S0(_,y,z)
R0(x,y,z) :- S0(x,y,z)
""".strip()

# similar to Figure 1b in the index-selection paper, changes made cause
# our input syntax is simpler.
    role_example = """
Err(s,e) :- Src(uid,s) Path(s,e) Sink(e,_,con) Role(uid,_,_)
Err(s,e) :- Src(uid,s) Path(s,e) Sink(e,dbid,op) Zone(dbid,doctor) Access(l,op) Role(uid,l,_)
Err(s,e) :- Src(uid,s) Path(S,e) Sink(e,dbid,op) Zone(dbid,patient) Access(l,op) Role(uid,_,l)
Err(s,e) :- Src(uid,s) Path(s,e) Sink(e,dbid,priv) Priveleged(l1,l2) Role(uid,l1,l2)
""".strip()

    failure = "Start(...) :- NewThing(w,_,y,_) NewThing(_,x,_,z) NewThing(_,x,y,z) NewThing(w,x,y,_)"

    quick = "Q0(x,y,z) :- S0(x,_,z) S0(x,y,z)"

    print(json.dumps(indexes_for_program(failure)))

if __name__ == '__main__':
    main()
