import sys
import random
import tomli


def main(filename, B, L, D, score_d, score_u, signup_d, signup_u, eff_d, eff_u, bklib_d, bklib_u):
    # uniform distribution of book scores in the range [score_d, score_u]
    print(f'Generating instance {filename} with {B} books, {L} libraries, {D} days, {score_d} <= score <= {score_u}, {signup_d} <= signup <= {signup_u}, {eff_d} <= efficiency <= {eff_u}, {bklib_d} <= books per library <= {bklib_u}')
    book_scores = []
    libraries_signup_times = []
    libraries_efficiencies = []
    books_in_libraries = []
    for i in range(B):
        book_scores.append(random.randint(score_d, score_u))
    libraries_signup_times = []
    for i in range(L):
        libraries_signup_times.append(random.randint(signup_d, signup_u))
        libraries_efficiencies.append(random.randint(eff_d, eff_u))
        no_of_books = random.randint(bklib_d, bklib_u)
        books = []
        for j in range(no_of_books):
            books.append(random.randint(0, B-1))
        books_in_libraries.append(books)
    with open(filename, 'w') as f:
        f.write(f'{B} {L} {D} \n')
        f.write(" ".join(map(str, book_scores)) + ' \n')
        for i in range(L):
            f.write(f'{len(books_in_libraries[i])} {libraries_signup_times[i]} {libraries_efficiencies[i]} \n')
            f.write(" ".join(map(str, books_in_libraries[i])) + ' \n')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python instance_generator.py <params.toml>')
        exit(1)
    with open(sys.argv[1], 'rb') as f:
        params = tomli.load(f)
    main(**params)
