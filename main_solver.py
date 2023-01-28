#!/usr/bin/env python3

import itertools
import sys
import time
from datetime import datetime as dt

import loader
import our_timer
import strategies.greedy as greedy
from loader import Problem
from strategies.genetic import Genetic
from strategies.greedy import ALL_LIBR_BOOK_PAIRS, ALL_LIBR_GREEDY
from strategies.strategies import SimpleCandidate, Strategy
from submission import Submission


def solve_for_this_instance(instance: Problem, only_greedy=False) -> Submission:
    """Run the algorithm(s) on this `instance`."""

    greedy_solutions: list[SimpleCandidate] = []
    # t1 = dt.now()
    t1 = our_timer.process_time_ns()
    _bk_sorters = ALL_LIBR_BOOK_PAIRS
    if instance.every_book_has_equal_score:
        # why would we even sort these books
        _bk_sorters = ALL_LIBR_GREEDY

    # example b) how many stars have to align:
    # 1. Same score
    # 2. unique, one (or zero) copies
    # 3. every library has
    # 4. N_j > D (or D/M)  for all libraries
    _b_type_instance = False
    if instance.every_book_has_equal_score and instance.is_every_book_unique:
        M_max = max(instance.library_efficiency)
        M_min = min(instance.library_efficiency)
        if M_max == M_min and all(
            (len(instance.library_book_ids[y]) >= (instance.D * M_max))
                for y in range(instance.L)):
            _b_type_instance = True
    for GRR in _bk_sorters:
        gr_solver = GRR(instance)
        out = gr_solver()
        if out is not None:
            out.books_improver()
            greedy_solutions.append(out)

    # check if the solution already is an upper bound
    # (for example in input "a")
    for i in greedy_solutions:
        out_sub = out.to_submission()
        sc = out_sub.get_submission_score()
        if sc == instance.upper_bound:
            # early exit
            return out_sub

    # additional heuristics which are separate
    # from the Cartesian product above
    # if instance.L <= 1_001:
    #     print('both', file=sys.stderr)
    #     for grr3 in [
    #         greedy.GreedyChooseLibrary,
    #         greedy.GreedyDynamic,
    #     ]:
    #         gr_solver = grr3(instance)
    #         out = gr_solver()
    #         if out is not None:
    #             out.books_improver()
    #             greedy_solutions.append(out)
    if instance.L <= 10_001:  # <-- limit z c)
        print('only dynamic', file=sys.stderr)
        solver_m = greedy.GreedyDynamic(instance)
        out = solver_m()
        if out is not None:
            out.books_improver()
            greedy_solutions.append(out)

    elif (instance.L <= 30_002  # <-- (d) only
          and instance.every_book_has_equal_score
          and max(len(x) for x in instance.library_book_ids) < 30):
        print('only choose-library', file=sys.stderr)
        solver_j = greedy.GreedyChooseLibrary(instance)
        out = solver_j()
        if out is not None:
            # it takes duplicates into account
            # out.books_improver()
            greedy_solutions.append(out)
    else:
        print(f'L = {instance.L}', file=sys.stderr)
        ...  # O(L^2 * ...) is too bad for those

    greedy.GreedyFast.POW = 1.05
    gr = greedy.GreedyFast(instance)
    out = gr()
    out.books_improver()
    greedy_solutions.append(out)

    t2 = our_timer.process_time_ns()
    print(f'greedy part took {(t2-t1)*1e-9:.2f}', file=sys.stderr)
    if only_greedy:
        print('best greedy solution', file=sys.stderr)
        return max((x.to_submission() for x in greedy_solutions),
                   key=lambda x: x.get_submission_score())

    solver = Genetic(instance, )
    solver.sub_to_cand(greedy_solutions)
    final = solver()
    return final


def main():
    """
    Entry point for the final project
    """
    instance = loader.read_lines(sys.stdin.readlines())
    sub = solve_for_this_instance(instance)
    sub.write(file=sys.stdout)
    # the process CPU time should be less than 5 minutes = 300 seconds
    print(f'process_time: {time.process_time()} s', file=sys.stderr)
    score = sub.get_submission_score()
    print(f'score {score}', file=sys.stderr)

    # not sure if 80% of bound is good...
    s = (100*score / instance.upper_bound)
    if s >= 80:
        print(f'The score is {s:5.2f} % of upper bound',
              file=sys.stderr)


if __name__ == '__main__':
    main()
