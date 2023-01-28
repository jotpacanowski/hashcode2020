import random

# import numpy as np

# from .strategies import *
from .strategies import Problem, Strategy, Submission


class Random(Strategy):
    def __init__(self, instance: Problem):
        super().__init__(instance)

    def __call__(self) -> Submission:
        signup_seq, books = self.random_solution()
        return Submission(self.instance, signup_seq, books)

    def random_solution(self):
        signup_seq = list(range(self.instance.L))
        random.shuffle(signup_seq)

        # day (starting from 0) when the library
        # becomes available
        lib_avail_times: list[int] = []
        d = 0
        for j in signup_seq:
            d += self.instance.library_signup_time[j]
            if d >= self.instance.D:
                # no more time to register
                signup_seq = signup_seq[:len(lib_avail_times)]
                break
            lib_avail_times.append(d)
        del d
        # if len(signup_seq) < 20:
        #     print('random order of libs:', signup_seq)
        #     print('library registed days:', lib_avail_times)

        to_scan = []
        for idx, j in enumerate(signup_seq):
            to_choose = (
                self.instance.library_efficiency[j]
                * (self.instance.D - lib_avail_times[idx])
            )
            if False:
                bset = self.instance.library_book_ids[j]
                # Assign books until the capacity is zero
                if len(bset) < to_choose:
                    seq = bset.copy()
                else:
                    seq = random.choices(bset.copy(), k=to_choose)
            else:
                # We don't care if we select books past the deadline.
                seq = self.instance.library_book_ids[j].copy()
                random.shuffle(seq)
                # seq = seq[:to_choose]
            to_scan.append(seq)
        return signup_seq, to_scan
