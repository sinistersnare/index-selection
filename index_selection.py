#!/usr/bin/env python3

from typing import Set

class Search:
    """TODO: Docs! DO TESTS ALSO!
    A search is a single search in a clause's body.
    so in the body if we see S0(x), then the clause will have
    `name = S0` and `parameters = {x}`
    """
    def __init__(self, name: str, parameters: Set[str]):
        self.name = name
        self.parameters = parameters

    def __str__(self):
        return "Search<name:{},parameters:{}>".format(
            self.name, self.parameters)
    __repr__ = __str__

class Clause:
    """TODO: DOCS! AND TESTS!!!
    A clause is a stripped down version of:
    C(x, y, z) :- S0(x) S1(y, z) S2(x z)
    Where bindings are {x, y, z}
    and searches are {S0(x) , S1(y, z) , S2(x, z)}
    see Search class for info on a search object.
    TODO: the bindings list doesnt need to be ordered does it???
    """
    def __init__(self, bindings: Set[str], searches: Set[Search]):
        self.bindings = bindings
        self.searches = searches

    def __str__(self):
        return "Clause<bindings:{},searches:{}>".format(
            self.bindings, self.searches)
    __repr__ = __str__

def form_search(raw_search: str, bindings: Set[str]) -> Search:
    """DOCS! tESTs!
    Takes something like "S0(x,y)", returns a Search object.
    """
    name_end = raw_search.find('(')
    name = raw_search[:name_end]
    raw_params = raw_search[name_end+1:-1]
    # Do we need to take parameters into account that are used
    # in other parts of the join?
    # R0(x,_) :- S0(x, y) S1(y, x)
    # does y matter in S0?
    params = {p for p in map(lambda x: x.strip(), raw_params.split(','))
                      if p in bindings}
    return Search(name, params)

def form_clause(line: str) -> Clause:
    """dOcS! TESTSSSSSS!!!
    Takes a Horn Clause and extracts relevant info.
    """
    headbody = line.split(":-")
    head, body = headbody[0].strip(), headbody[1].strip()
    binding_start = head.find('(') + 1
    raw_bindings = head[binding_start:-1]
    # TODO: Make sure all constants are taken out properly.
    bindings = {b for b in (x.strip() for x in raw_bindings.split(','))
                        if not b.isdecimal()}
    searches = {form_search(rs, bindings) for rs in body.split()}
    return Clause(bindings, searches)

def get_search_usages(program: str) -> None:
    """DOCS! AND TESTS??!?!?!?"""

    # I dont think that clauses really need to exist,
    # Since I ensure only bound variables are used in the form_search
    # function. So maybe we juts need a Set[Search] and union
    # all the searches in each line?
    # Maybe it was bad to remove info early, because now we dont have the info
    # on constants used and such.
    clauses = (form_clause(c) for c in program.split('\n'))
    search_usages = {}
    for clause in clauses:
        for search in clause.searches:
            if search.name in search_usages:
                search_usages[search.name].append(search.parameters)
            else:
                search_usages[search.name] = [search.parameters]
    return search_usages


def main():
    datalog = """
R0(x,y) :- R1(x,y) R2(x,z)
R0(x,y) :- R1(x,y) R3(y,x)
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
    usages = get_search_usages(pathological_lex)

    from pprint import pprint
    pprint(usages)
    # print("{}".format(list(clauses)[1]))
    # print(datalog)

if __name__ == '__main__':
    main()
