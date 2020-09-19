#!/usr/bin/env python3

from typing import FrozenSet, Tuple, Iterator, Dict, Set, Optional, List, Union
from collections import defaultdict
from pprint import pprint
import itertools
import json
import sys

import networkx as nx
from networkx.algorithms import bipartite

# YOU WIN NETWORKX FINE. ILL USE YOUR DISGUSTING ALGORITHM.
from networkx.algorithms.matching import max_weight_matching

"""
Yihao's code. We decided to use this over Davis's after review
"""

def search_list_to_sexpr(usage):
    sexpr = "(set "
    for s in usage:
        sexpr += "(set "
        for col in s:
            sexpr += str(col)
            sexpr += " "
        sexpr += ")"
        sexpr += " "
    sexpr += ")"
    return sexpr

def total_to_sexpr(total):
    sexpr = "(set "
    for i in range(total):
        sexpr += f" {i} "
    sexpr += ")"
    return sexpr

class Search:
    """
    A search is a single search in a clause's body, with grounded variables positions.
    so in the body if we see S0(x), then the clause will have
    R(x, y) :- S0(x,y,1) S1(y,y,_)
    `name = S0` and `parameters = ['x', 'y', '1']`, total = 3
    `name = S1` and `parameters = ['y', '_']`, total = 3
    Parameters is not a set because we dont have the positions yet,
    So after we figure out what is joined, we can then use sets, as we will be dealing
    with 0-indexed positions, not values that can appear anywhere.
    """

    def __init__(self, name: str, parameters: Set[str], total: int):
        self.name = name
        self.parameters = parameters
        self.total = total

    def __str__(self):
        return f"Search<name:{self.name},parameters:{self.parameters},total:{self.total}>"
    __repr__ = __str__


def form_search(raw_search: str) -> Search:
    """
    Takes something like "S0(x,y)", returns a Search object: Search('S0'. {'x','y'})
    """
    name_end = raw_search.find('(')
    name = raw_search[:name_end]

    raw_params = raw_search[name_end+1:-1] # take out the parens.
    params = [rp.strip() for rp in raw_params.split(',')]

    return Search(name, params, len(params))


def form_searches(line: str) -> Iterator[Search]:
    """
    Takes a Horn Clause and extracts relevant info.
    """
    body = line.split(":-")[1].strip()

    return [form_search(s) for s in body.split()]


def get_usages_in_line(searches: List[Search]) -> Dict[str, List[Tuple[Tuple[int, ...], int]]]:
    """
    Takes a single line of searches, and constructs, for each search, which variables are used (by position 0-indexed).
    If the variable is used in a join with another column, then

    Returns a dict from a searches name to a a usage-structure:
    The first element of the tuple is the usages themselves, by 0-index.
    The second element is the number of columns in the search (not number used). This is a bit repetitive, as we only need
        One length per name, but we can normalize it later.
    """
    usages = defaultdict(list)
    for search in searches:
        # Dont need to worry about searches that are only unused params.
        if search.parameters == {'_'}:
            continue

        uses = set()
        amt = search.total
        for i, param in enumerate(search.parameters):
            if param == '_':
                continue
            if param.isdigit():
                uses.add(i)
                continue
            # need to see if the param is being used in a join! Expensive!
            for other_search in searches:
                if param in other_search.parameters:
                    uses.add(i)
                    break
        usages[search.name].append((tuple(uses), amt))
    return usages

def get_search_usages(program: str) -> Dict[str, Tuple[Set[Tuple[int, ...]], int]]:
    """
    Doesnt work the way we want it to, switch to using `get_usages_in_line`!
    """
    usages_per_line = [get_usages_in_line(form_searches(c)) for c in program.split('\n')]
    total_usages = {}
    # Normalize so we only have 1 amt for each rel,
    # And also add all the usages for each line together.
    for line in usages_per_line:
        for rel, uses in line.items():
            if not total_usages.get(rel):
                total_usages[rel] = ({t[0] for t in uses}, uses[0][1])
            else:
                total_usages[rel][0].update({t[0] for t in uses})
    return total_usages

def create_graph(searches) -> ('graph', 'u_edges'):
    '''
    create a biparite graph, for a search U V are just replicate set of searches
    there is a edge if someone in V is a a proper subset of U
    in order to distinguish them, I use different tag name for U, V
    '''
    u_edges = set()
    graph = nx.Graph()
    # add node
    graph.add_nodes_from((("U", s) for s in searches), bipartite=0)
    graph.add_nodes_from((("V", s) for s in searches), bipartite=1)
    for u in searches:
        for v in searches:
            if set(u) < set(v):
                graph.add_edge(("U", u), ("V", v))
                u_edges.add(("U", u))
    return (graph, u_edges)


def min_chain_coverage(searches):
    '''
    calculate the minimum chain coverage of a graph.
    return Set(List(Tuple))
    '''
    (g, u_edges) = create_graph(searches)
    M_with_label = bipartite.matching.maximum_matching(g, u_edges)
    # remove tag in M
    M = []
    for m_key in M_with_label.keys():
        if m_key[0] == "U":
            node_from = m_key[1]
            node_to = M_with_label[m_key][1]
            M.append((node_from, node_to))
    # print("maximum matching is {}".format(M))
    C = set()

    def no_prev(u1, M):
        '''∀ u1 ∈ S, ∄(u0, u1) ∈ M'''
        for m in M:
            if u1 == m[1]:
                return False
        return True

    def no_next(u1, M):
        '''∀ u1 ∈ S, ∄(u1, u') ∈ M'''
        for m in M:
            if u1 == m[0]:
                return False
        return True

    def find_next(u1, M):
        for m in M:
            if u1 == m[0]:
                return m[1]
        return None

    def find_path(u, M):
        ''' find maximal path (u1, u2), (u2, u3), (uk-1 uk) ⊆ M '''
        path = [u]
        current = u
        while not no_next(current, M):
            current = find_next(current, M)
            path.append(current)
        return tuple(path)

    for u1 in searches:
        if no_prev(u1, M):
            C.add(find_path(u1, M))
    return C

def min_index(searches):
    '''
    convert chain coverage into index selection
    '''
    # C is Iterable[Tuple[Tuple[int, ...], ...]]
    C = min_chain_coverage(searches)
    indexes = []
    for chain in C:
        index = list(chain[0])
        for i in range(1, len(chain)):
            index += set(chain[i]) - set(chain[i - 1])
        indexes.append(tuple(index))
    return indexes

def fill_indexes(indexes: List[Tuple[int, ...]], num_columns: int) -> List[Tuple[int, ...]]:
    """
    Indexes need to have all columns in them, so we backfill each index with leftover elements, that arent used
    In searches using that index.
    """
    findexes = []
    for index in indexes:
        sindex = set(index) # treat as set for the purposes of this.
        to_add = [i for i in range(num_columns) if i not in sindex]
        findexes.append(tuple(list(index) + to_add))
    return findexes

def indexes_for_program(program):
    usages = get_search_usages(program)
    indexes = {}
    for rel, use in usages.items():
        # sexpr = search_list_to_sexpr(use[0])
        # totexpr = total_to_sexpr(use[1])
        # print(f"{rel}: (indices-from-selections {sexpr}  {totexpr})")
        index = min_index(use[0])
        filled_indexes = fill_indexes(index, use[1])
        indexes[rel] = filled_indexes
        # print(f"USES: {use[0]}\nINDEX: {index}")
    return indexes

def main():
    if len(sys.argv) == 2:
        with open(sys.argv[1], 'r') as file:
            program = file.read().strip()
            indexes = indexes_for_program(program)
            print(indexes)
    else:
        print("Usage: `python index_selection.py <file>")

if __name__ == '__main__':
    main()
