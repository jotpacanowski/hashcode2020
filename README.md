# Google Hash Code 2020 Online Qualification Round - Book scanning

Final project for the Combinatorial Optimization course at PUT.

The main script is located in file `main_solver.py`.
We tested the code using Python 3.10 with numpy 1.24.

There is a bash script to run it on all problem instances
located in the `input/` folder.

```
$ python3 ./main_solver.py < input/a_example.txt > out.txt 2> err.txt
$ ./solution_test input/a_example.txt out.txt
Theoretical upper bound: 21
No problem found, final score: 21
$
$ ./test-solver.sh
Running a_example
 Upper bound: 21
score 21
The score is 100.00 % of upper bound
Theoretical upper bound: 21
No problem found, final score: 21
Running b_read_on
(...)
```

This program prints some information to standard error output (stderr),
but it can be disabled by redirecting it to `/dev/null` file.

Note: Python hashing algorithm, used for example in the `set` built-in structure,
is not deterministic.
We have seen computation time vary between subsequent runs on the same machine
due to Python hash seed being randomized by the interprer.
There is no way to set it in the code, because it was introduced for security.

On different machines computations can take 90 seconds instead of 45,
we do not know why.

In case of permission error please try to run `chmod +x`.
