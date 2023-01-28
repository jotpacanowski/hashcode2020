try:
    from rich.pretty import pprint
except ImportError:
    from pprint import pprint  # type: ignore

import itertools
from pathlib import Path

from loader import Problem, read_input_file
import strategies.greedy as greedy
from strategies.genetic import Genetic
from strategies.random_solver import Random
from strategies.strategies import Strategy, SimpleCandidate
from submission import Submission

import main_solver
import our_timer


def try_strategy(strategy: type[Strategy], instance, subfn='') -> int:
    solver = strategy(instance)
    out = solver()
    if isinstance(out, SimpleCandidate):
        out = out.to_submission()
    score = out.get_submission_score()
    # if subfn:
    #     # print('writing submission to ', subfn)
    #     with open(subfn, 'w') as f:
    #         ...  # out.write(file=f)
    return score


def test_strategy_on_all(strategy: type[Strategy], *, tries=1):
    """try `strategy` on all example instances"""
    wd = Path.cwd()
    files = [str(x.relative_to(wd)) for x in wd.glob('input/*')]
    # pprint([x.name for x in files])

    print('\ntesting strategy:', strategy.get_strategy_name())
    for fn in files:
        print('')
        scores = []
        instance = read_input_file(fn)
        for it in range(tries):
            # if 'c_' in fn:
            #     sfn = f'out_c_{strategy.get_strategy_name()}'
            # else:
            sfn = ''
            score = try_strategy(strategy, instance, subfn=sfn)
            scores.append(score)
        if min(scores) == max(scores):
            print(f' score : \x1b[32;1m{min(scores):9_}\x1b[0m')
        else:
            print(
                f' scores: \x1b[32;1m{min(scores):10_} .. {max(scores):10_}\x1b[0m')


def test_reading_writing():
    """test reading problem instance and writing submissions"""
    instance = read_input_file('input/a_example.txt')

    if instance.B < 10 and instance.D < 20:
        pprint(instance)
    else:
        print(f'B,D,L: {instance.B} {instance.D} {instance.L}')

    # test
    s = Submission(instance, [1, 0], [
        [5, 2, 3],
        [0, 1, 2, 3, 4],
    ])
    # pprint(s)
    s.write()
    assert 16 == s.get_submission_score()


def run_solver_on_every_input(only_greedy=False):
    wd = Path.cwd()
    files = [str(x.relative_to(wd)) for x in wd.glob('input/*')]
    print(f'{len(files)} inputs to try')
    # pprint([x.name for x in files])

    scores_sum = 0

    for fn in files:
        instance = read_input_file(fn)

        our_timer.reset_countdown_timer()
        our_timer.tic()
        out = main_solver.solve_for_this_instance(instance,
                                                  only_greedy=only_greedy)

        score = out.get_submission_score()
        print(f' final score: \x1b[32;1m  {score:9_}  \x1b[0m')
        print(f'CPU time: {our_timer.tac():.3f} s')
        # not sure if 80% of bound is good...
        s = (100*score / instance.upper_bound)
        if s >= 80:
            print(f'The score is {s:5.2f} % of upper bound')

        print('')
        scores_sum += score
    print(f'Sum of all scores is \x1b[32;1m  {scores_sum:9_}  \x1b[0m')


if __name__ == '__main__':
    # test_reading_writing()
    # test_strategy_on_all(Random, tries=32)
    run_solver_on_every_input(only_greedy=False)
