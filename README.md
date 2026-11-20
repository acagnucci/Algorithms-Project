# Algorithms Project: Cryptocurrency Price Analysis

Group project for the **Algorithms 2022/2023** course of the BSc in Management and Computer Science at LUISS Guido Carli (Rome).

The assignment was to analyse a dataset of daily cryptocurrency prices using algorithms written by hand, in plain Python, without pandas or the built-in sort.

**Team:** Antonio Cagnucci, Santiago Cuesta, Gianfranco Pizzuto, Peter Jelusic

## What is implemented

`n` is the number of records, `V` the number of cryptocurrencies and `D` the number of days in the chosen interval.

| Function | What it does | Approach | Time |
|---|---|---|---|
| `read_file` | Loads the dataset | Line-by-line parsing | O(n) |
| `crypto_stats` | Minimum, mean and maximum price in a time interval | Single pass | O(n) |
| `sort_data` | Sorts by name, then by day | Merge sort written from scratch | O(n log n) |
| `get_max_value` | Highest price in a given 30-day month | Single pass | O(n) |
| `search` | Day whose price is closest to a target value | Linear scan | O(n) |
| `min_correlation_pathways` | Tree linking the least correlated cryptocurrencies | Pearson correlation and Prim's minimum spanning tree | O(n + V²·D) |
| `correlated_cryptos_at_lvl_k` | Cryptocurrencies at a given depth of that tree | Breadth-first search | O(V) |

## Repository layout

```
original/group0.py          The group's code from May 2023
crypto_algorithms.py        Cleaned-up version (2026)
tests/                      Tests for the cleaned-up version
```

### `original/group0.py`

The code as the group wrote it during the course. The task descriptions that came with the course template were removed because they belong to the course staff. The code itself is unchanged.

### `crypto_algorithms.py`

A 2026 revision of the original. It keeps the same seven functions and the same algorithms, and changes the following:

- Records are parsed into a named tuple, and a malformed line raises an error that names the line.
- `crypto_stats` returns `(0.0, 0.0, 0.0)` when there is no data. The original raised an error.
- The merge sort is stable, leaves its input untouched and sorts once on `(name, day)`. The original sorted in two passes and modified the input.
- `get_max_value` and `search` return the earliest day when several days tie, as the assignment asks. The original returned whichever came first in the file.
- `min_correlation_pathways` returns `{parent: [children]}`, the format the assignment specifies. The original returned nested dictionaries with edge weights.
- Prim's algorithm keeps the cheapest known edge for each cryptocurrency, which takes O(V²) steps. The original rescanned every edge at each step, which takes O(V³).
- Pairs of cryptocurrencies with fewer than two days in common are skipped. The original divided by zero when two cryptocurrencies shared no days.
- The breadth-first search uses a queue with O(1) removal (`collections.deque`).

## Running the tests

```
pip install pytest
python -m pytest
```

The tests use small made-up datasets, so they run without the course data. They include a check of Prim's result against an independent implementation of Kruskal's algorithm.

The cleaned-up version was also run through the course's public grader with the course datasets. It passes every test in parts 1 and 2. In part 3 the grader checks the output format, that the tree has no cycles and that the level search agrees with the tree, and those checks pass too. The grader looks names up in lowercase in part 3, so names were lowercased for that run only.

## Data

The datasets are not included here because they belong to the course. They are in the course repository linked below, under `data/`. Each line has the form `name,day,price,volume`:

```python
from crypto_algorithms import read_file, crypto_stats, min_correlation_pathways

data = read_file("data/dataset_small.txt")
print(crypto_stats(data, "Algorand", (1, 5)))
print(min_correlation_pathways(data, "Algorand", (2, 25)))
```

## Credits

The assignment, starter template, datasets and grader were written by the course staff and are available at [flaat/Algorithms-2022-2023-Project](https://github.com/flaat/Algorithms-2022-2023-Project). This repository contains only the group's own code.
