from dataclasses import dataclass
from sys import stdout

from loader import Problem


@dataclass(frozen=True)  # TODO: make tuples from lists
class Submission:
    instance: Problem

    # order of libraries to sign up
    library_signups: list[int]

    # map i-th library (in order) -> list of book IDs
    books_to_scan: list[list[int]]
    # books_to_scan: dict[int, list[int]]

    def write(self, file=stdout):
        print(len(self.library_signups), file=file)
        for i, j in enumerate(self.library_signups):
            print(f'{j} {len(self.books_to_scan[i])}', file=file)
            print(*self.books_to_scan[i], sep=' ', file=file)

    def get_submission_score(self) -> int:
        """
        Compute the final score for this submission.
        """
        B, L, D = self.instance.B, self.instance.L, self.instance.D

        A = len(self.library_signups)
        assert 0 <= A <= L
        assert (len(set(self.library_signups))
                == len(self.library_signups))

        final_score = 0
        book_visited = set()
        signup_days = 0
        for i, Y in enumerate(self.library_signups):
            # Y - library ID, index in problem instance
            # i - index in `self`
            assert 0 <= Y < L
            signup_days += self.instance.library_signup_time[Y]
            if signup_days > D:
                break  # past deadline

            # NOTE: these assertions below can be safely commented out,
            #       they are there just as a sanity check.
            # we want to scan something
            assert len(self.books_to_scan[i]) > 0
            # check library idx - subset
            assert set(self.books_to_scan[i]) <= set(
                set(self.instance.library_book_ids[Y]))

            capacity = (self.instance.library_efficiency[Y]
                        * (D - signup_days))
            if capacity <= 0:
                continue
            for k in self.books_to_scan[i][:capacity]:
                assert 0 <= k < B  # book ID
                if k in book_visited:
                    continue
                book_visited.add(k)
                final_score += self.instance.book_scores[k]

        return final_score
