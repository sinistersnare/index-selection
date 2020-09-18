#!/usr/bin/env python3

from typing import Set, List, Iterator
import itertools

import networkx as nx
from networkx.algorithms import bipartite

# YOU WIN NETWORKX FINE. ILL USE YOUR DISGUSTING ALGORITHM.
from networkx.algorithms.matching import max_weight_matching


"""Yihao's code. We decided to use this over Davis's after review"""


class Search:
    """TODO: Docs! DO TESTS ALSO!
    A search is a single search in a clause's body, with grounded variables positions.
    so in the body if we see S0(x), then the clause will have
    R(x, y) :- S0(x, y, 1) S1(1, y, x)
    `name = S0` and `parameters = {0, 1}`
    `name = S1` and `parameters = {1, 2}`
    """

    def __init__(self, name, parameters):
        self.name = name
        self.parameters = parameters

    def __str__(self):
        return "Search<name:{},parameters:{}>".format(
            self.name, self.parameters)
    __repr__ = __str__


def form_search(raw_search: str) -> Search:
    """DOCS! tESTs!
    Takes something like "S0(x,y)", returns a Search object.
    """
    name_end = raw_search.find('(')
    name = raw_search[:name_end]
    raw_params = raw_search[name_end+1:-1]
    # Do we need to take parameters into account that are used
    # in other parts of the join?
    # R0(x,2) :- S1(y, x) S0(x, y) S2(q, 3)
    # does y matter in S0? Why does `y` matter but not `q`.
    params = []
    for rp in raw_params.split(','):
        params.append(rp.strip())
    return Search(name, params)


def form_searches(line: str) -> Iterator[Search]:
    """dOcS! TESTSSSSSS!!!
    Takes a Horn Clause and extracts relevant info.
    """
    body = line.split(":-")[1].strip()

    return list(form_search(s) for s in body.split())


def isProperSubset(a: Set, b: Set):
    '''
    check if a is a proper subset of b
    '''
    return a.issubset(b) and a != b


def get_search_usages(program: str) -> None:
    """DOCS! AND TESTS??!?!?!?"""
    # I dont think that clauses really need to exist,
    # Since I ensure only bound variables are used in the form_search
    # function. So maybe we juts need a Set[Search] and union
    # all the searches in each line?
    # Maybe it was bad to remove info early, because now we dont have the info
    # on constants used and such.
    searches = list(form_searches(c) for c in program.split('\n'))
    search_usages = {}
    for rule_search in searches:
        # get all used meta var in a rule
        used_var = {}
        for s in rule_search:
            for p in s.parameters:
                if p in used_var.keys():
                    used_var[p] = used_var[p] + 1
                else:
                    used_var[p] = 1
        for search in rule_search:
            usage = []
            for i in range(len(search.parameters)):
                if used_var[search.parameters[i]] > 1:
                    # have join here
                    usage.append(i)
            if search.name in search_usages.keys():
                search_usages[search.name].add(tuple(usage))
            else:
                search_usages[search.name] = {tuple(usage)}
    return search_usages


def create_graph(searchs):
    '''
    create a biparite graph, for a search U V are just replicate set of searchs
    there is a edge if someone in V is a a proper subset of U
    in order to distinguish them, I use different tag name for U, V
    '''
    graph = nx.Graph()
    # add node
    graph.add_nodes_from(map(lambda s: ("U", s), searchs), bipartite=0)
    graph.add_nodes_from(map(lambda s: ("V", s), searchs), bipartite=1)
    for u in searchs:
        for v in searchs:
            if isProperSubset(set(u), set(v)):
                graph.add_edge(("U", u), ("V", v))
    return graph


def min_chain_coverage(searchs):
    '''
    calculate the minimum chain coverage of a graph.
    return Set(List(Tuple))
    '''
    g = create_graph(searchs)
    M_with_label = bipartite.matching.maximum_matching(
        g, map(lambda s: ("U", s), searchs))
    # remove tag in M
    M = []
    for m_key in M_with_label.keys():
        if m_key[0] == "U":
            node_from = m_key[1]
            node_to = M_with_label[m_key][1]
            M.append((node_from, node_to))
    print("maximum matching is {}".format(M))
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

    for u1 in searchs:
        if no_prev(u1, M):
            C.add(find_path(u1, M))
    return C


def min_index(searches):
    '''
    convert chain coverage problem into index selection problem
    '''
    C = min_chain_coverage(searches)
    print("min chain coverage: {}".format(C))
    L = set()
    for c in C:
        if len(c) == 1:
            L.add(tuple(c[0]))
            continue
        index = [c[0]]
        for i in range(1, len(c)):
            index.append(tuple(set(c[i]) - set(c[i-1])))
        L.add(tuple(index))
    return L


def main():
    datalog = """
P0(y) :- Role(x,y,z) P0(x)
P1(y,z) :- Role(x,y,z) P1(x,y)
P2(x,y) :- Role(x,y,z) P2(x,z)
P3(x,z,y) :- Role(x,y,z) P3(x,z,y)
Role(x,y,z) :- P3(x,y,z)
""".strip()

    # IDK if this function is useful for the actual work,
    # But its helpful to show usages at least.
    usages = get_search_usages(datalog)

    from pprint import pprint
    pprint(usages)
    # print("{}".format(list(clauses)[1]))
    # print(datalog)
    # calculate max_index
    for relation in usages.keys():
        index = min_index(usages[relation])
        print("index of {} is {}".format(relation, index))


if __name__ == '__main__':
    main()
