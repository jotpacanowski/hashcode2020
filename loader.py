import sys
from collections import Counter
from dataclasses import dataclass


@dataclass
class Problem:
    # B = total number of books
    # L = total number of libraries
    # D = deadline
    B: int
    L: int
    D: int

    # S_i = score of book with ID i
    book_scores: list[int]

    # N_j = number of books in the library
    # T_j = sign-up time
    # M_j = books to scan per day
    library_signup_time: list[int]
    library_efficiency: list[int]
    library_book_ids: list[list[int]]

    def __post_init__(self):
        # Compute some statistics on this instance.
        self.signup_time_unique_values = len(set(self.library_signup_time))
        self.efficiency_unique_values = len(set(self.library_efficiency))

        #
        score_set = set(self.book_scores)
        self.every_book_has_equal_score = (len(score_set) == 1)
        if self.every_book_has_equal_score:
            print('Fact: Every book has the same score', file=sys.stderr)

        #
        ctr: Counter[int] = Counter()
        for ids in self.library_book_ids:
            ctr.update(ids)
        uniqueness = set(ctr.get(b, 0)
                         for b in range(self.B)
                         )
        self.is_every_book_unique = (len(uniqueness) == 1)
        if self.is_every_book_unique:
            print('Fact: Every book is unique', file=sys.stderr)

        self.upper_bound = sum(self.book_scores)
        print(f' Upper bound: {self.upper_bound:_}', file=sys.stderr)
        ub2 = 0
        for b in range(0, self.B):
            if ctr.get(b, 0) > 0:
                ub2 += self.book_scores[b]
        if ub2 < self.upper_bound and ub2 > 0:
            print(f'Better bound: {ub2:_}', file=sys.stderr)
            self.upper_bound = ub2


def read_input_file(filename: str):
    print(f'Reading file {filename}', file=sys.stderr)
    inp = open(filename).readlines()
    return read_lines(inp)


def read_lines(inp: list[str]):
    B, L, D = map(int, inp[0].split())

    books_scores = list(map(int, inp[1].split()))
    assert len(books_scores) == B

    libraries_signup_times = []
    libraries_efficiency = []
    libraries_book_ids = []
    for i, (ln1, ln2) in enumerate(zip(inp[2::2], inp[3::2])):
        n, signup_time, m = map(int, ln1.split())
        book_ids = list(map(int, ln2.split()))
        assert len(book_ids) == n

        libraries_signup_times.append(signup_time)
        libraries_efficiency.append(m)
        libraries_book_ids.append(book_ids)

    return Problem(
        B, L, D,
        books_scores,
        libraries_signup_times,
        libraries_efficiency,
        libraries_book_ids
    )
