#!/usr/bin/env python3

from typing import Set, List, Iterator
import itertools

# YOU WIN NETWORKX FINE. ILL USE YOUR DISGUSTING ALGORITHM.
from networkx.algorithms.matching import max_weight_matching

class Search:
    """TODO: Docs! DO TESTS ALSO!
    A search is a single search in a clause's body, with grounded variables positions.
    so in the body if we see S0(x), then the clause will have
    R(x, y) :- S0(x, y, 1) S1(1, y, x)
    `name = S0` and `parameters = {0, 1}`
    `name = S1` and `parameters = {1, 2}`
    """
    def __init__(self, name: str, parameters: Set[int]):
        self.name = name
        self.parameters = parameters

    def __str__(self):
        return "Search<name:{},parameters:{}>".format(
            self.name, self.parameters)
    __repr__ = __str__

# TODO FUCK THIS FUNCTION.
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
    params = {idx for (idx, p) in enumerate((x.strip() for x in raw_params.split(','))) if p != '_'}
    return Search(name, params)

# TODO FUCK THIS ONE TOO
def form_searches(line: str) -> Iterator[Search]:
    """dOcS! TESTSSSSSS!!!
    Takes a Horn Clause and extracts relevant info.
    """
    body = line.split(":-")[1].strip()

    return (form_search(s) for s in body.split())

def get_search_usages(program: str) -> None:
    """DOCS! AND TESTS??!?!?!?"""
    # I dont think that clauses really need to exist,
    # Since I ensure only bound variables are used in the form_search
    # function. So maybe we juts need a Set[Search] and union
    # all the searches in each line?
    # Maybe it was bad to remove info early, because now we dont have the info
    # on constants used and such.
    searches = (form_searches(c) for c in program.split('\n'))
    search_usages = {}
    for search in itertools.chain(*searches):
        if search.name in search_usages:
            if search.parameters not in search_usages[search.name]:
                search_usages[search.name].append(search.parameters)
        else:
            search_usages[search.name] = [search.parameters]
    return search_usages


def main():
    datalog = """
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

    # IDK if this function is useful for the actual work,
    # But its helpful to show usages at least.
    usages = get_search_usages(datalog)

    from pprint import pprint
    pprint(usages)
    # print("{}".format(list(clauses)[1]))
    # print(datalog)

if __name__ == '__main__':
    main()
