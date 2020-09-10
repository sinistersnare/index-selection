# Project I: Automatic Index Selection for Datalog

## Team Notes ##

To run

```
$ pip install networkx
$ run the thing with input (TODO!)
```

( I wrote this in a separate repo, then realized I should just fork this).

Index Selection Algorithm based on

P. Subotić, H. Jordan, L. Chang, A. Fekete, and B. Scholz, “Automatic index selection for large-scale datalog computation,” Proc. VLDB Endow., vol. 12, no. 2, pp. 141–153, Oct. 2018, doi: 10.14778/3282495.3282500.

find here: http://www.vldb.org/pvldb/vol12/p141-subotic.pdf

This project:

https://github.com/kmicinski/index-selection

this class:

https://kmicinski.com/cis700-f20/

TODO:
    * Get MIT license authorization from everyone in class.

## END TEAM NOTES! ##


### CIS 700, Syracuse U, Fall 2020
### Instructor: Kris Micinski

For this project, you may work in groups of up to three students.

This project will have you implement the automatic index selection
algorithm from the paper "Automatic Index Selection for Large-Scale
Datalog Computation."

http://www.vldb.org/pvldb/vol12/p141-subotic.pdf

Note that I am not providing starter code for this project. I am
providing only sample inputs. Like a research project, it is your job
to architect a solution from scratch, using whatever tools your group
finds most expedient and enabling to collaboration.

### Project Description

As we discussed in class, trie-based Datalog engines rely on storing
multiple copies of each relations, one for each necessary index. For
example, consider the following program:

```
R0(x,y) :- R1(x,y) R2(x,z)
R0(x,y) :- R1(x,y) R3(y,x)
R3(x,1) :- R0(x,y)
```

The first rule is a join of `R1` and `R2` on the first column. An
efficient implementation of this rule requires that `R1` be indexed on
its first column, and the same for `R2`. The second rule is a join
between `R1` and `R3`, and requires that both are indexed on both of
their columns. The last rule selects from its first column and ignores
the second.

For each relation `R` with arity `n`, an "index" for `R` is an
ordering of `R`'s columns, i.e., an n-tuple consisting of values in
the range `[0-n)`. You will calculate minimal necessary set of indices
for each relation using the algorithm discussed in the above paper.

Although a naive implementation may keep two separate indices for `R1`
in the above example (`(0)` and `(0,1)`), an efficient implementation
will recognize that the second index overlaps the first. Thus, it is
more efficient to store only the second.

A reasonable solution would output the following indices for each
relation:

- `R0` -- `{(0,1)}`. This index is rather arbitrary, since `R0` is never
  used in a join. But it is used in a selection / iteration, so it
  makes sense to put 0 first.
- `R1` -- `{(0,1)}`, as discussed above
- `R2` -- `{(0,1)}`, as `R2` is indexed on the first column. `{(0,1)}` would also be acceptable.
- `R3` -- `{(0,1)}`, for the same reason as `R0` needs `(0,1)`.

For examples that would generate more than one index, look at Table 1
in the paper.

#### Sample inputs

Given in this directory. `ex0` is the one above. `ex1` is the one from
the paper. `ex2` is another one I made up.

#### Deliverables

- A program, written in any language you want, that accepts one
  command-line argument corresponding to the input file.

- Your program will output a set of indices for each relation.

#### Input Format

The input is a Datalog program consisting of the following:

- The program is a sequence of nonempty lines.

- Each line contains a Datalog rule consisting of a head and body.

- Rules have the format `H(a,...) :- B0(a,...) B1(a,...)` where each a
  is either a variable or a literal integer. There will be no spaces
  in between the arguments to relations.

- Note that the input will not contain underscores, as in the
  paper. Instead, it will contain variables which are unused in the
  head clause. For example:

```
R0(x,y) :- R1(x,y,z)
```

- The head clause is of the form `R(x,y,...)` where each argument is
  either an alphanumeric variable name (grounded in the body) or a
  nonnegative integer.

- Rules with zero bodies are facts, and must be fully ground. For
  example, the following is a fact:

```
R(1,2,3) :-
```

- Note that facts still contain the `:-` symbol to make parsing fairly
  uniform.

- Each rule has precisely one head, but zero or more bodies.

- The body consists of a join of a number of relations of the form
  `R(x,y,...)` where each of the arguments to the relation is either a
  variable or a literal integer.

- Every variable used in the head must be grounded in the body. For
  example, the following rule is unacceptable because `y` is not
  ground in the body:

```
R0(x,y) :- R1(x,z) R2(z,x)
```

- I realize I may not have gotten everything here. Please ask
  questions as you have them. I want to make this easy for you, so I'm
  happy to change stuff if it makes more superficial aspects of the
  assignment easier.

#### Output and Grading

You will output, for each relation, a set of indices. I do not care
how this is rendered. For example, you might write out JSON, you might
pretty-print an S-expression, or you might simply write output to the
terminal. For example, this would be a reasonable implementation:

```
R0 -- 2 indices
(0, 3, 1, 2, 4)
(2, 4, 0, 1, 3)
...
```

I will not be using automated tests to grade this project. I will
instead grade based on the following criteria:

- For each of the examples given, did you get the correct answer (you
  need to figure that out, too, by the way, but please feel free to
  work this out and ask)?

- Did you also test your project on larger, more complicated cases?

- Did you have some thoughtful testing methodology to ensure your
  algorithm is correct? For example, if you used maximal matching, did
  you validate this in some way (against, say, a reference
  implementation using random testing)? I'm not expecting anything
  specific here, I just want to make sure your code is decently
  robust.

- Do I feel like everyone in your group got to contribute and learn
  something? I don't want one person to do the assignment. It's
  absolutely fine, however, if group members have varying amounts of
  skill-level (and thus contribute differently) in tasks like
  programming. But each group member should be checked in to the
  technical aspects of the project. Ideally, you should try to do
  pair-programming to the extent possible.

I hope to award full credit on this assignment, based on your working
with me to deliver a satisfactory answer from your group. However, I
will grade based on my own inspection of your code, along with running
it on several examples of my own. I will not be a big stickler on code
quality, though I do want you to be thoughtful programmers, and I will
ask you questions and give advice if you implemented things in a way I
find confusing.
