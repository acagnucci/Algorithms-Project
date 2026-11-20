"""Algorithms over a cryptocurrency price dataset, written without library helpers.

Each line of the dataset describes one cryptocurrency on one day::

    name,day,price,volume

The module covers three groups of tasks:

1. Reading the file and computing price statistics.
2. Sorting (merge sort, no built-in sort) and searching.
3. Building a minimum spanning tree over price correlations (Prim's
   algorithm) and walking it level by level (breadth-first search).

Only the Python standard library is used.
"""

from __future__ import annotations

from collections import deque
from math import sqrt
from typing import Callable, Dict, List, NamedTuple, Optional, Sequence, Tuple, TypeVar

T = TypeVar("T")

DAYS_PER_MONTH = 30


class Record(NamedTuple):
    """One observation: a cryptocurrency on one day."""

    name: str
    day: int
    price: float
    volume: float


# ---------------------------------------------------------------------------
# Part 1 - reading and statistics
# ---------------------------------------------------------------------------


def read_file(file_path: str) -> List[Record]:
    """Read the dataset into a list of records, in file order.

    The name is everything before the last three commas, so a name that
    itself contains a comma is still read correctly.

    Raises ValueError, naming the line, if a line cannot be parsed.
    Time: O(n) for n lines.
    """
    records: List[Record] = []
    with open(file_path, encoding="utf-8") as dataset:
        for line_number, raw_line in enumerate(dataset, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                name, day, price, volume = line.rsplit(",", 3)
                records.append(Record(name, int(float(day)), float(price), float(volume)))
            except ValueError as error:
                raise ValueError(
                    f"{file_path}, line {line_number}: cannot parse {line!r}"
                ) from error
    return records


def crypto_stats(
    data: Sequence[Record], crypto_name: str, interval: Tuple[int, int]
) -> Tuple[float, float, float]:
    """Return (minimum, mean, maximum) price of one crypto within [start, end].

    The interval is inclusive and may extend beyond the days that were
    actually recorded. Returns (0.0, 0.0, 0.0) when there is no data.
    Time: O(n). Extra space: O(1).
    """
    start, end = interval
    count = 0
    total = 0.0
    lowest = float("inf")
    highest = float("-inf")
    for record in data:
        if record.name == crypto_name and start <= record.day <= end:
            count += 1
            total += record.price
            lowest = min(lowest, record.price)
            highest = max(highest, record.price)
    if count == 0:
        return (0.0, 0.0, 0.0)
    return (lowest, total / count, highest)


# ---------------------------------------------------------------------------
# Part 2 - sorting and searching
# ---------------------------------------------------------------------------


def merge_sort(items: Sequence[T], key: Callable[[T], object]) -> List[T]:
    """Return a new list with the items sorted by key, using merge sort.

    The sort is stable: items with equal keys keep their original order.
    The input is not modified.
    Time: O(n log n). Extra space: O(n).
    """
    if len(items) <= 1:
        return list(items)

    middle = len(items) // 2
    left = merge_sort(items[:middle], key)
    right = merge_sort(items[middle:], key)

    merged: List[T] = []
    i = j = 0
    while i < len(left) and j < len(right):
        # "<=" takes from the left half on ties, which keeps the sort stable.
        if key(left[i]) <= key(right[j]):
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def sort_data(data: Sequence[Record]) -> List[Tuple[str, float]]:
    """Sort by crypto name, then by day, and return (name, price) pairs.

    Names are compared as plain strings, so digits come before capitals
    and capitals before lowercase letters.
    Time: O(n log n).
    """
    ordered = merge_sort(data, key=lambda record: (record.name, record.day))
    return [(record.name, record.price) for record in ordered]


def get_max_value(data: Sequence[Record], crypto: str, month: int) -> Tuple[int, float]:
    """Return (day, price) of the highest price of a crypto in a given month.

    Months are 30 days long and numbered from 1, so month 13 is the first
    month of the second year. If the highest price occurs on several days,
    the earliest day is returned. Returns (-1, -1.0) when there is no data
    or the month is not positive.
    Time: O(n).
    """
    if month < 1:
        return (-1, -1.0)

    first_day = (month - 1) * DAYS_PER_MONTH + 1
    last_day = month * DAYS_PER_MONTH

    best_day = -1
    best_price = -1.0
    for record in data:
        if record.name != crypto or not first_day <= record.day <= last_day:
            continue
        is_higher = record.price > best_price
        is_same_but_earlier = record.price == best_price and record.day < best_day
        if best_day == -1 or is_higher or is_same_but_earlier:
            best_day = record.day
            best_price = record.price
    return (best_day, best_price)


def search(data: Sequence[Record], value: float, crypto: str) -> Tuple[int, float]:
    """Return (day, price) of the price of a crypto closest to a target value.

    If several days are equally close, the earliest day is returned.
    Returns (-1, -1.0) when the crypto does not appear in the data.
    Time: O(n). The data is not assumed to be sorted, so a linear scan is
    used rather than binary search.
    """
    best_day = -1
    best_price = -1.0
    best_difference = float("inf")
    for record in data:
        if record.name != crypto:
            continue
        difference = abs(value - record.price)
        is_closer = difference < best_difference
        is_same_but_earlier = difference == best_difference and record.day < best_day
        if is_closer or is_same_but_earlier:
            best_day = record.day
            best_price = record.price
            best_difference = difference
    return (best_day, best_price)


# ---------------------------------------------------------------------------
# Part 3 - correlation tree
# ---------------------------------------------------------------------------


def pearson_correlation(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    """Return the Pearson correlation of two equally long series.

    Returns None when there are fewer than two observations, because the
    correlation is then undefined. Returns 0.0 when either series is
    constant, treating a price that never moves as uncorrelated.
    Time: O(n).
    """
    if len(xs) != len(ys):
        raise ValueError("the two series must have the same length")
    n = len(xs)
    if n < 2:
        return None

    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    covariance = 0.0
    variance_x = 0.0
    variance_y = 0.0
    for x, y in zip(xs, ys):
        dx = x - mean_x
        dy = y - mean_y
        covariance += dx * dy
        variance_x += dx * dx
        variance_y += dy * dy

    if variance_x == 0.0 or variance_y == 0.0:
        return 0.0
    correlation = covariance / sqrt(variance_x * variance_y)
    # Rounding can push the result a hair outside [-1, 1].
    return max(-1.0, min(1.0, correlation))


def _prices_by_day(
    data: Sequence[Record], interval: Tuple[int, int]
) -> Dict[str, Dict[int, float]]:
    """Group prices as {crypto name: {day: price}}, keeping days in the interval."""
    start, end = interval
    series: Dict[str, Dict[int, float]] = {}
    for record in data:
        if start <= record.day <= end:
            series.setdefault(record.name, {})[record.day] = record.price
    return series


def _correlation_between(
    first: Dict[int, float], second: Dict[int, float]
) -> Optional[float]:
    """Correlate two cryptos over the days on which both have a price."""
    common_days = sorted(first.keys() & second.keys())
    return pearson_correlation(
        [first[day] for day in common_days],
        [second[day] for day in common_days],
    )


def min_correlation_pathways(
    data: Sequence[Record], crypto: str, interval: Tuple[int, int]
) -> Dict[str, List[str]]:
    """Build a minimum spanning tree of price correlations, rooted at a crypto.

    Every pair of cryptos is joined by an edge whose weight is the Pearson
    correlation of their prices over the days they share inside the
    interval. Prim's algorithm grows the tree from the root, always adding
    the lowest-weight edge that reaches a new crypto, so the tree links the
    least correlated pairs. Ties are broken by name, which makes the result
    deterministic.

    Pairs with fewer than two days in common have no edge. Cryptos that
    cannot be reached from the root are left out of the tree.

    Returns the tree as {parent: [children]}; every crypto in the tree is a
    key, and leaves map to an empty list. Returns {} when the root has no
    data in the interval.

    Time: O(n + V^2 * D) for V cryptos and D days in the interval. The
    graph is complete, so this version of Prim's algorithm, which scans an
    array of best edges instead of using a heap, is the efficient choice.
    """
    series = _prices_by_day(data, interval)
    if crypto not in series:
        return {}

    tree: Dict[str, List[str]] = {crypto: []}
    # For every crypto not yet in the tree: the cheapest edge into the tree,
    # stored as (weight, parent).
    cheapest_edge: Dict[str, Tuple[float, str]] = {}
    newest = crypto

    while True:
        # Edges from the crypto just added may be cheaper than those known.
        for candidate in series:
            if candidate in tree:
                continue
            weight = _correlation_between(series[newest], series[candidate])
            if weight is None:
                continue
            known = cheapest_edge.get(candidate)
            if known is None or (weight, newest) < known:
                cheapest_edge[candidate] = (weight, newest)

        if not cheapest_edge:
            break

        next_crypto = min(
            cheapest_edge, key=lambda name: (cheapest_edge[name][0], name)
        )
        _, parent = cheapest_edge.pop(next_crypto)
        tree[parent].append(next_crypto)
        tree[next_crypto] = []
        newest = next_crypto

    return tree


def nodes_at_level(tree: Dict[str, List[str]], root: str, level: int) -> List[str]:
    """Return the nodes exactly `level` edges below the root, using BFS.

    Level 0 is the root itself. Returns [] when the root is not in the
    tree or the level is negative.
    Time: O(V).
    """
    if root not in tree or level < 0:
        return []

    found: List[str] = []
    queue = deque([(root, 0)])
    visited = {root}
    while queue:
        node, depth = queue.popleft()
        if depth == level:
            found.append(node)
            continue  # nodes below this one are deeper than requested
        for child in tree.get(node, []):
            if child not in visited:
                visited.add(child)
                queue.append((child, depth + 1))
    return found


def correlated_cryptos_at_lvl_k(
    data: Sequence[Record], crypto: str, level: int, interval: Tuple[int, int]
) -> Tuple[Dict[str, List[str]], List[str]]:
    """Return the correlation tree and the cryptos at a given level of it.

    The tree is the one built by min_correlation_pathways. It is returned
    together with the list because the assignment asked for both.
    """
    tree = min_correlation_pathways(data, crypto, interval)
    return (tree, nodes_at_level(tree, crypto, level))
