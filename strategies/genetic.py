import random
from copy import deepcopy
from sys import stderr
from typing import Optional

import our_timer
from .strategies import Problem, SimpleCandidate, Strategy, Submission


class Candidate(SimpleCandidate):
    def __init__(self, instance: Problem, libraries: Optional[list[int]], books_in_library: Optional[list[list[int]]]):
        # shuffle the order of libraries
        self.instance = instance

        if libraries is None:
            self.libraries = list(range(instance.L))
            random.shuffle(self.libraries)
        else:
            self.libraries = libraries

        if books_in_library is None:
            self.books_in_library = deepcopy(instance.library_book_ids)
            for library in self.books_in_library:
                random.shuffle(library)
        else:
            self.books_in_library = deepcopy(books_in_library)

    def clone(self):
        """Clone this Candidate (deep copy)"""
        # the same naming as in Rust :)
        return Candidate(self.instance,
                         self.libraries.copy(),
                         deepcopy(self.books_in_library)
                         )

    def fitness(self) -> int:
        time_to_alloc = self.instance.D
        score = 0
        seen_books = set()
        for library in self.libraries:
            time_to_alloc -= self.instance.library_signup_time[library]
            if time_to_alloc <= 0:
                break
            for bookidx in range(min(time_to_alloc * self.instance.library_efficiency[library], len(self.books_in_library[library]))):
                if self.books_in_library[library][bookidx] not in seen_books:
                    seen_books.add(self.books_in_library[library][bookidx])
                    score += self.instance.book_scores[self.books_in_library[library][bookidx]]
        return score

    @staticmethod
    def from_submission(subm: Submission):
        lookup_library = dict()
        for i, Y in enumerate(subm.library_signups):
            lookup_library[Y] = i
        r = Candidate(subm.instance,
                      list(subm.library_signups),
                      [
                          # Submission stores books in the order of sign-ups
                          subm.books_to_scan[lookup_library[i]]
                          if i in lookup_library
                          else list(subm.instance.library_book_ids[i])
                          for i in range(subm.instance.L)
                      ]
                      )
        return r

    def mutate(self):
        RATE = 0.4
        for i in range(len(self.libraries)):
            if random.random() < RATE:
                j = random.randint(0, len(self.libraries) - 1)
                self.libraries[i], self.libraries[j] = self.libraries[j], self.libraries[i]
        return self


class Genetic(Strategy):
    def __init__(self, instance: Problem, population_size: int = 20, mutation_rate: float = 0.7, crossover_rate: float = 0.3, tournament_size: int = 3, max_generations: int = 10, max_stagnation: int = 50):
        super().__init__(instance)
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.tournament_size = tournament_size
        self.max_generations = max_generations
        self.max_stagnation = max_stagnation
        self.elitism_no = 5
        self.initial_pop: list[Candidate] = []

    def sub_to_cand(self, sub_list: list[SimpleCandidate]):
        for it in sub_list:
            self.initial_pop.append(
                Candidate(it.instance, it.libraries, it.books_in_library))

    def crossover(self, candidate1: Candidate, candidate2: Candidate):
        child_libraries1, child_libraries2 = [], []
        to_fill1, to_fill2 = set(), set()
        for i in range(len(candidate1.libraries)):
            add_to_child1 = candidate1.libraries[i] if i % 2 == 0 else candidate2.libraries[i]
            add_to_child2 = candidate2.libraries[i] if i % 2 == 0 else candidate1.libraries[i]
            if add_to_child1 not in child_libraries1:
                child_libraries1.append(add_to_child1)
            if add_to_child2 not in child_libraries2:
                child_libraries2.append(add_to_child2)
            if add_to_child1 not in child_libraries2:
                to_fill2.add(add_to_child1)
            if add_to_child2 not in child_libraries1:
                to_fill1.add(add_to_child2)
        for i in range(len(candidate1.libraries)):
            if len(to_fill1) == 0:
                break
            if candidate1.libraries[i] in to_fill1:
                child_libraries1.append(candidate1.libraries[i])
                to_fill1.remove(candidate1.libraries[i])
        for i in range(len(candidate2.libraries)):
            if len(to_fill2) == 0:
                break
            if candidate2.libraries[i] in to_fill2:
                child_libraries2.append(candidate2.libraries[i])
                to_fill2.remove(candidate2.libraries[i])
        child_books1 = deepcopy(candidate1.books_in_library)
        child_books2 = deepcopy(candidate2.books_in_library)
        return Candidate(self.instance, child_libraries1, child_books1), Candidate(self.instance, child_libraries2, child_books2)

    def tournament_selection(self, population: list[Candidate]) -> Candidate:
        best: Candidate = None  # type: ignore
        # mypy suggested Optional[Candidate]
        for _ in range(self.tournament_size):
            candidate = random.choice(population)
            if best is None or candidate.fitness() > best.fitness():
                best = candidate
        return best

    def __call__(self):
        stagnation = 0
        best: Candidate = None  # type: ignore
        population = [Candidate(self.instance, None, None)
                      for _ in range(self.population_size)]
        population.extend(self.initial_pop)
        print('initial best fitness: ', max(x.fitness()
              for x in population), file=stderr)

        for generation in range(self.max_generations):
            population.sort(key=lambda x: x.fitness(), reverse=True)
            if best is None or population[0].fitness() > best.fitness():
                best = population[0].clone()  # copy (!)
                stagnation = 0
            else:
                stagnation += 1
            if stagnation > self.max_stagnation:
                break
            if our_timer.get_cpu_time_left() <= 20:
                break  # 30 seconds left
            print(f"Generation {generation}: {population[0].fitness()}, "
                  f"mean: {sum([x.fitness() for x in population]) / len(population)}", file=stderr)

            new_population = []
            for i in range(self.elitism_no):
                new_population.append(population[i])
            for i in range(self.population_size - self.elitism_no):
                candidate1 = self.tournament_selection(population)
                candidate2 = self.tournament_selection(population)
                if 10 < self.crossover_rate:
                    child1, child2 = self.crossover(candidate1, candidate2)
                    new_population.append(child1)
                    new_population.append(child2)
                else:
                    new_population.append(candidate1)
                    new_population.append(candidate2)
            for candidate in new_population:
                if random.random() < self.mutation_rate:
                    candidate.mutate()
            population = new_population
        print(f"Best: {best.fitness()}", file=stderr)
        return best.to_submission()
