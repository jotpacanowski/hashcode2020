#!/bin/sh

for i in input/*.txt; do
    printf "Running %s\n" $(basename -s .txt $i)
    python3 ./main_solver.py < "$i" > "out-"`basename -s .txt $i`'.txt'
    ./solution_test.o "$i" "out-"`basename -s .txt $i`'.txt'
done
