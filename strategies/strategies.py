from loader import Problem
from submission import Submission


class Strategy(object):
    def __init__(self, instance: Problem):
        self.instance = instance

    def __call__(self) -> 'Submission | SimpleCandidate':
        # here child classes should implement the strategy
        raise NotImplementedError()  # abstract class

    @classmethod
    def get_strategy_name(cls) -> str:
        return cls.__name__


class SimpleCandidate:
    def __init__(self, instance: Problem, libraries: list[int], books_in_library: list[list[int]]):
        self.instance = instance
        self.libraries = list(libraries)
        self.books_in_library = [list(x) for x in books_in_library]

    @staticmethod
    def new_without_copy(instance: Problem, libraries: list[int], books_in_library: list[list[int]]):
        """Construct new SimpleCandidate without unnecessary copies"""
        s = SimpleCandidate(None, [], [])  # type: ignore
        s.instance = instance
        s.libraries = libraries
        s.books_in_library = books_in_library
        return s

    def to_submission(self) -> Submission:
        time_to_alloc = self.instance.D
        libs = []
        books = []
        for library in self.libraries:
            time_to_alloc -= self.instance.library_signup_time[library]
            if time_to_alloc <= 0:
                break
            libs.append(library)
            books.append(self.books_in_library[library][:(
                time_to_alloc * self.instance.library_efficiency[library]
            )])
        return Submission(self.instance, libs, books)

    def books_improver(self):
        scanned_books = set()
        for library in self.libraries:
            self.books_in_library[library].sort(
                key=lambda x: self.instance.book_scores[x]
                if x not in scanned_books else 0,
                reverse=True)
            scanned_books.update(self.books_in_library[library])
