import gc
import itertools
from collections import Counter
from copy import deepcopy
from typing import Optional

import numpy as np

from .strategies import Problem, SimpleCandidate, Strategy, Submission

import our_timer
import sys


class GreedyBase(Strategy):
    def __init__(self, instance: Problem):
        super().__init__(instance)
        # sort libraries by increasing key (non-decreasing)
        self.libr_asc = True
        #
        self.book_asc = True

    def __call__(self) -> SimpleCandidate:
        L = self.instance.L
        signup_order = list(range(L))
        signup_order.sort(key=self.key_libr,
                          reverse=not self.libr_asc)

        books_in_library = []
        for list_of_book_ids in self.instance.library_book_ids:
            # list() vs .copy() - idk
            books = list(list_of_book_ids)
            books.sort(key=self.key_book, reverse=not self.book_asc)
            books_in_library.append(books)
            # NOTE: ignore the deadline for now,
            #       it will be useful for evolutionary programming

        return SimpleCandidate.new_without_copy(
            self.instance,
            signup_order,
            books_in_library)

    def key_libr(self, y: int):
        """key used to sort libraries"""
        # raise NotImplementedError('key_libr')
        return 0  # do not sort

    def key_book(self, b: int):
        """key function used to sort books"""
        return 0  # do not sort

# tags to make type checkers happy


class DummySorter(GreedyBase):
    ...


class LibrarySorter(GreedyBase):
    ...


class BookSorter(GreedyBase):
    ...

# greedy heuristics for libraries only


class GreedyByEfficiencyL(LibrarySorter):
    def __init__(self, instance: Problem):
        super().__init__(instance)
        self.libr_asc = True

    def key_libr(self, y: int):
        # lowest R_i are first
        return self.instance.library_efficiency[y]


class GreedyByEfficiencyH(GreedyByEfficiencyL):
    def __init__(self, instance: Problem):
        super().__init__(instance)
        # highest R_i are first
        self.libr_asc = False


class GreedyBySignupTime(LibrarySorter):
    def __init__(self, instance: Problem):
        super().__init__(instance)
        self.libr_asc = True

    def key_libr(self, y: int):
        return self.instance.library_signup_time[y]


class GreedyByLength(LibrarySorter):
    def __init__(self, instance: Problem):
        super().__init__(instance)
        self.libr_asc = False

    def key_libr(self, y: int):
        return len(self.instance.library_book_ids[y])


class GreedyByEfficiencyToSignup(LibrarySorter):
    def __init__(self, instance: Problem):
        super().__init__(instance)
        self.libr_asc = False

    def key_libr(self, y: int):
        M = self.instance.library_efficiency[y]  # higher better
        T = self.instance.library_signup_time[y]  # lower better
        return M / T

# greedy heuristics for book(s) only


class GreedyBookScore(BookSorter):
    def __init__(self, instance: Problem):
        super().__init__(instance)
        self.book_asc = False

    def key_book(self, b: int):
        return self.instance.book_scores[b]


class GreedyBookDuplicates(BookSorter):
    def key_book(self, b: int):
        return self.duplicate_count.get(b)

    def __init__(self, instance: Problem):
        super().__init__(instance)
        self.book_asc = True

        ctr: Counter[int] = Counter()
        for ids in self.instance.library_book_ids:
            ctr.update(ids)

        self.duplicate_count = dict(ctr)
        # : dict[int, int]


class GreedyBookScoreAndUniqueness(GreedyBookDuplicates):
    def __init__(self, instance: Problem):
        super().__init__(instance)
        self.book_asc = False  # order by higher score

    def key_book(self, b: int):
        # Better book is unique (little duplicates) and has high score.
        dupl = self.duplicate_count.get(b, 0)
        # unique book gets score * 10
        # with 1 duplicate (x=2) gets score * 90%
        # Limit the multiplier to 1 -- when x >= 10
        c = max(11 - 1 * dupl, 1)
        return c * self.instance.book_scores[b]

# greedy heuristics for both


class GreedyChooseLibrary(GreedyBase):
    def __init__(self, instance: Problem):
        super().__init__(instance)

    def __call__(self) -> Optional[SimpleCandidate]:
        if not self.instance.every_book_has_equal_score:
            return None

        L = self.instance.L
        signup_order = []
        days = self.instance.D
        libr_ids = list(range(L))  # list or set
        visited_books = np.zeros(self.instance.B, dtype=np.uint8)

        num_books_in_library = []
        books_in_library = []
        # These sets are updated later,
        # so that they contain only unseen books.
        books_in_lib_sets: list[set[int]] = []
        for list_of_book_ids in self.instance.library_book_ids:
            books = list(list_of_book_ids)
            books.sort(key=self.instance.book_scores.__getitem__,
                       reverse=True)  # descending scores
            num_books_in_library.append(len(books))
            books_in_library.append(books)
            books_in_lib_sets.append(set(books))

        stat_min_T = min(self.instance.library_signup_time)
        stat_max_M = max(self.instance.library_efficiency)
        stat_max_score = max(self.instance.book_scores)

        last_best_libr_fitness = float('+inf')

        def choose_best_library():
            """
            According to https://wiki.python.org/moin/TimeComplexity
            `s.difference_update(t)` is O(len(t))

            Complexity: O(L * B)
            """
            nonlocal last_best_libr_fitness
            bestkey = -1  # maximum number of new books
            bestlibr = -1
            # maximum possible score
            # area of rectangle days by books-per-day
            key_upper_bound = (
                (days - stat_min_T) * stat_max_M * stat_max_score
            )
            for i in libr_ids:
                if bestkey >= key_upper_bound or bestkey >= last_best_libr_fitness:
                    continue
                if num_books_in_library[i] <= bestkey:
                    continue
                T = self.instance.library_signup_time[i]
                if T > days or days <= 0:
                    continue

                thiskey = len(books_in_lib_sets[i])
                t = []
                for j in books_in_lib_sets[i]:
                    if visited_books[j] == 1:
                        t.append(j)
                        num_books_in_library[i] -= 1  # 2x faster
                        thiskey -= 1
                books_in_lib_sets[i].difference_update(t)
                thiskey = min(days - T, thiskey)

                if thiskey > bestkey:
                    bestkey = thiskey
                    bestlibr = i

            last_best_libr_fitness = bestkey
            return bestlibr

        # gc.disable()
        while days > 0 and libr_ids:
            # if days % 1000 == 999:
            if (L - len(libr_ids)) % 1000 == 20:
                if our_timer.get_cpu_time_left() <= 30:
                    return None  # 30 seconds left, start panicking
                # gc.collect()
                # print(gc.get_stats())

            # find the best library
            best_libr = choose_best_library()
            if best_libr == -1:
                break
            signup_order.append(best_libr)

            T = self.instance.library_signup_time[best_libr]
            limit = days - T
            # for b_id in books_in_lib_sets[best_libr]:
            # [: days - T]:
            for b_id in books_in_library[best_libr]:
                if limit <= 0:
                    break
                limit -= 1
                visited_books[b_id] = 1

            days -= T
            libr_ids.remove(best_libr)
            # gc.collect(0)

        # gc.enable()

        return SimpleCandidate.new_without_copy(
            self.instance,
            signup_order,
            books_in_library)


class GreedyDynamic(GreedyBase):
    def __init__(self, instance: Problem):
        super().__init__(instance)
        self.instance = instance
        self.books_in_libs = deepcopy(self.instance.library_book_ids)

    def get_best_library(self, time_left: int, libraries: set[int], used_books: set) -> int:
        # pair (score, lib_idx)
        best: tuple[float, Optional[int]] = (0.0, None)
        for lib in libraries:
            if self.instance.library_signup_time[lib] <= time_left:
                self.books_in_libs[lib].sort(
                    key=lambda x: self.instance.book_scores[x] if x not in used_books else 0, reverse=True)
                books_to_scan = (
                    time_left - self.instance.library_signup_time[lib]) * self.instance.library_efficiency[lib]
                score = sum(self.instance.book_scores[b]
                            for b in self.books_in_libs[lib][:books_to_scan])/(self.instance.library_signup_time[lib])
                if score > best[0]:
                    best = (score, lib)
        return best[1]

    def get_best_library_better(self, time_left: int, libraries: set[int], used_books: set) -> Optional[int]:
        best = (0, None)
        for lib in libraries:
            if self.instance.library_signup_time[lib] <= time_left:
                sorted_books = set(self.instance.library_book_ids[lib])
                intersection = sorted_books.intersection(used_books)
                sorted_books.difference_update(intersection)
                sorted_books: list = list(sorted_books)
                sorted_books.sort(key=lambda x: self.instance.book_scores[x],
                                  reverse=True)
                books_to_scan = (
                    time_left - self.instance.library_signup_time[lib]) * self.instance.library_efficiency[lib]
                score = sum(self.instance.book_scores[b]
                            for b in sorted_books[:books_to_scan])/(
                    self.instance.library_signup_time[lib]**0.92)  # TODO check 0.95 power and 1.15 or 1.05
                if score > best[0]:
                    best = (score, lib)
        return best[1]

    def __call__(self) -> Optional[SimpleCandidate]:
        time_left = self.instance.D
        libraries_not_signed_up = set(range(self.instance.L))
        library_signups = []
        used_books: set[int] = set()
        while time_left > 0 and len(libraries_not_signed_up) > 0:
            lib = self.get_best_library_better(
                time_left, libraries_not_signed_up, used_books)
            if lib is None:
                break
            library_signups.append(lib)
            used_books.update(self.instance.library_book_ids[lib])
            time_left -= self.instance.library_signup_time[lib]
            libraries_not_signed_up.remove(lib)
            if our_timer.get_cpu_time_left() <= 30:
                return None  # 30 seconds left, start panicking
        library_signups.extend(libraries_not_signed_up)
        output = SimpleCandidate(self.instance,
                                 library_signups, self.books_in_libs)
        return output


class GreedyFast(GreedyBase):
    def __init__(self, instance: Problem):
        super().__init__(instance)
        self.instance = instance
        self.POW = 1.0

    def score_lib(self, idx, POW=1.15):
        time_to_use = self.instance.D - self.instance.library_signup_time[idx]
        books_to_scan = time_to_use * self.instance.library_efficiency[idx]
        return sum(self.instance.book_scores[b] for b in self.instance.library_book_ids[idx][:books_to_scan])/((self.instance.library_signup_time[idx])**POW)

    def __call__(self) -> SimpleCandidate:
        libraries = list(range(self.instance.L))
        libraries.sort(key=lambda x: self.score_lib(x, self.POW), reverse=True)
        output = []
        for lib in libraries:
            output.append(lib)
        return SimpleCandidate(self.instance,
                               output, self.instance.library_book_ids)

# list of all greedy algorithms in this module


ALL_LIBR_GREEDY: list[type[LibrarySorter]] = [
    GreedyByEfficiencyL,
    GreedyByEfficiencyH,
    GreedyBySignupTime,
    GreedyByEfficiencyToSignup,
    GreedyByLength,
]

ALL_BOOK_GREEDY: list[type[BookSorter]] = [
    GreedyBookScore,
    GreedyBookDuplicates,
    GreedyBookScoreAndUniqueness,
]


def enumerate_two_sorter_combinations():
    def create_new(grr1: type[LibrarySorter], grr2: type[BookSorter]):
        class GRR(grr1, grr2):  # type:ignore
            @classmethod
            def get_strategy_name(cls) -> str:
                return f'({grr1.__name__} and {grr2.__name__})'
        return GRR

    for grr1, grr2 in itertools.product(ALL_LIBR_GREEDY, ALL_BOOK_GREEDY):
        yield create_new(grr1, grr2)


ALL_LIBR_BOOK_PAIRS = list(enumerate_two_sorter_combinations())
# pprint([ x.get_strategy_name() for x in ALL_LIBR_BOOK_PAIRS] )


# heuristics which combine knowledge
# about libraries and books inside them
ALL_COMBINED_GREEDY: list[type[GreedyBase]] = [
    GreedyChooseLibrary,
    GreedyDynamic,
]

ALL_GREEDY_STRATEGIES: list[type[GreedyBase]] = [
]

ALL_GREEDY_STRATEGIES.extend(ALL_LIBR_GREEDY)
ALL_GREEDY_STRATEGIES.extend(ALL_BOOK_GREEDY)
# ALL_GREEDY_STRATEGIES.extend(ALL_LIBR_BOOK_PAIRS)
ALL_GREEDY_STRATEGIES.extend(ALL_COMBINED_GREEDY)
