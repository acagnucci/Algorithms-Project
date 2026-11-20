"""Tests for crypto_algorithms. Run with: python -m pytest"""

import os
import random
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crypto_algorithms import (  # noqa: E402
    Record,
    correlated_cryptos_at_lvl_k,
    crypto_stats,
    get_max_value,
    merge_sort,
    min_correlation_pathways,
    nodes_at_level,
    pearson_correlation,
    read_file,
    search,
    sort_data,
)


def make_records(prices_by_name):
    """Build records from {name: [price on day 1, price on day 2, ...]}."""
    return [
        Record(name, day, price, 0.0)
        for name, prices in prices_by_name.items()
        for day, price in enumerate(prices, start=1)
    ]


# --- read_file -------------------------------------------------------------


def test_read_file_parses_each_field(tmp_path):
    path = tmp_path / "data.txt"
    path.write_text("Alpha,3,1.5,100.0\nbeta coin,1,0.25,7\n\n")
    assert read_file(str(path)) == [
        Record("Alpha", 3, 1.5, 100.0),
        Record("beta coin", 1, 0.25, 7.0),
    ]


def test_read_file_keeps_commas_inside_names(tmp_path):
    path = tmp_path / "data.txt"
    path.write_text("Coin, Inc,2,1.0,5.0\n")
    assert read_file(str(path)) == [Record("Coin, Inc", 2, 1.0, 5.0)]


def test_read_file_reports_the_bad_line(tmp_path):
    path = tmp_path / "data.txt"
    path.write_text("Alpha,1,1.0,1.0\nAlpha,two,1.0,1.0\n")
    with pytest.raises(ValueError, match="line 2"):
        read_file(str(path))


# --- crypto_stats ----------------------------------------------------------


def test_crypto_stats_uses_only_the_interval():
    data = make_records({"Alpha": [10.0, 2.0, 4.0, 100.0], "Beta": [999.0, 999.0]})
    assert crypto_stats(data, "Alpha", (2, 3)) == (2.0, 3.0, 4.0)


def test_crypto_stats_interval_may_exceed_the_data():
    data = make_records({"Alpha": [1.0, 3.0]})
    assert crypto_stats(data, "Alpha", (-50, 5000)) == (1.0, 2.0, 3.0)


def test_crypto_stats_without_data_returns_zeros():
    data = make_records({"Alpha": [1.0, 3.0]})
    assert crypto_stats(data, "Missing", (1, 2)) == (0.0, 0.0, 0.0)
    assert crypto_stats(data, "Alpha", (10, 20)) == (0.0, 0.0, 0.0)


# --- merge_sort and sort_data ----------------------------------------------


def test_merge_sort_matches_builtin_sort_on_random_input():
    generator = random.Random(0)
    for size in [0, 1, 2, 3, 10, 257, 1000]:
        values = [generator.randint(-50, 50) for _ in range(size)]
        assert merge_sort(values, key=lambda value: value) == sorted(values)


def test_merge_sort_is_stable_and_does_not_modify_input():
    pairs = [(1, "a"), (0, "b"), (1, "c"), (0, "d"), (1, "e")]
    original = list(pairs)
    assert merge_sort(pairs, key=lambda pair: pair[0]) == [
        (0, "b"),
        (0, "d"),
        (1, "a"),
        (1, "c"),
        (1, "e"),
    ]
    assert pairs == original


def test_sort_data_orders_by_name_then_day():
    data = [
        Record("beta", 2, 4.0, 0.0),
        Record("Alpha", 2, 2.0, 0.0),
        Record("beta", 1, 3.0, 0.0),
        Record("1inch", 1, 0.5, 0.0),
        Record("Alpha", 1, 1.0, 0.0),
    ]
    assert sort_data(data) == [
        ("1inch", 0.5),
        ("Alpha", 1.0),
        ("Alpha", 2.0),
        ("beta", 3.0),
        ("beta", 4.0),
    ]


# --- get_max_value ---------------------------------------------------------


def test_get_max_value_looks_only_at_the_requested_month():
    prices = [1.0] * 60
    prices[9] = 5.0  # day 10, month 1
    prices[44] = 9.0  # day 45, month 2
    data = make_records({"Alpha": prices})
    assert get_max_value(data, "Alpha", 1) == (10, 5.0)
    assert get_max_value(data, "Alpha", 2) == (45, 9.0)


def test_get_max_value_returns_earliest_day_on_ties():
    data = [
        Record("Alpha", 7, 3.0, 0.0),
        Record("Alpha", 2, 3.0, 0.0),
        Record("Alpha", 5, 1.0, 0.0),
    ]
    assert get_max_value(data, "Alpha", 1) == (2, 3.0)


def test_get_max_value_without_data():
    data = make_records({"Alpha": [1.0, 2.0]})
    assert get_max_value(data, "Alpha", 12) == (-1, -1.0)
    assert get_max_value(data, "Alpha", 0) == (-1, -1.0)
    assert get_max_value(data, "Alpha", -1) == (-1, -1.0)
    assert get_max_value(data, "Missing", 1) == (-1, -1.0)


# --- search ----------------------------------------------------------------


def test_search_finds_exact_and_closest_price():
    data = make_records({"Alpha": [1.0, 4.0, 9.0], "Beta": [5.0]})
    assert search(data, 4.0, "Alpha") == (2, 4.0)
    assert search(data, 5.1, "Alpha") == (2, 4.0)
    assert search(data, 1000.0, "Alpha") == (3, 9.0)


def test_search_returns_earliest_day_on_ties():
    data = [
        Record("Alpha", 9, 6.0, 0.0),
        Record("Alpha", 3, 4.0, 0.0),
        Record("Alpha", 6, 6.0, 0.0),
    ]
    # 4.0 and 6.0 are equally close to 5.0; day 3 is the earliest.
    assert search(data, 5.0, "Alpha") == (3, 4.0)
    assert search(data, 6.0, "Alpha") == (6, 6.0)


def test_search_for_unknown_crypto():
    data = make_records({"Alpha": [1.0]})
    assert search(data, 1.0, "Missing") == (-1, -1.0)


# --- pearson_correlation ---------------------------------------------------


def test_pearson_correlation_known_values():
    assert pearson_correlation([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)
    assert pearson_correlation([1, 2, 3], [6, 4, 2]) == pytest.approx(-1.0)
    assert pearson_correlation([1, 2, 3, 4], [1, 3, 2, 4]) == pytest.approx(0.8)


def test_pearson_correlation_edge_cases():
    assert pearson_correlation([], []) is None
    assert pearson_correlation([1.0], [2.0]) is None
    assert pearson_correlation([1, 1, 1], [1, 2, 3]) == 0.0
    with pytest.raises(ValueError):
        pearson_correlation([1, 2], [1, 2, 3])


# --- min_correlation_pathways ----------------------------------------------


def edges_of(tree):
    return [(parent, child) for parent, children in tree.items() for child in children]


def kruskal_total_weight(names, weight):
    """Independent minimum spanning tree weight, to check Prim's result."""
    parent = {name: name for name in names}

    def find(name):
        while parent[name] != name:
            parent[name] = parent[parent[name]]
            name = parent[name]
        return name

    pairs = [(a, b) for index, a in enumerate(names) for b in names[index + 1 :]]
    total = 0.0
    for a, b in sorted(pairs, key=lambda pair: weight(*pair)):
        root_a, root_b = find(a), find(b)
        if root_a != root_b:
            parent[root_a] = root_b
            total += weight(a, b)
    return total


def test_tree_on_a_small_hand_checked_example():
    data = make_records(
        {
            "Up": [1.0, 2.0, 3.0, 4.0],
            "AlsoUp": [2.0, 4.0, 6.0, 8.0],  # correlation with Up: +1
            "Down": [4.0, 3.0, 2.0, 1.0],  # correlation with Up: -1
        }
    )
    # From Up the cheapest edge is to Down (-1). AlsoUp then also attaches
    # to Down (-1) rather than to Up (+1).
    assert min_correlation_pathways(data, "Up", (1, 4)) == {
        "Up": ["Down"],
        "Down": ["AlsoUp"],
        "AlsoUp": [],
    }


def test_tree_spans_all_cryptos_with_minimum_total_weight():
    generator = random.Random(1)
    prices = {
        f"coin{index}": [generator.uniform(1, 100) for _ in range(40)]
        for index in range(12)
    }
    data = make_records(prices)
    generator.shuffle(data)
    names = sorted(prices)

    def weight(a, b):
        return pearson_correlation(prices[a], prices[b])

    for root in ["coin0", "coin7"]:
        tree = min_correlation_pathways(data, root, (1, 40))
        edges = edges_of(tree)

        assert sorted(tree) == names
        assert len(edges) == len(names) - 1
        children = [child for _, child in edges]
        assert len(set(children)) == len(children) and root not in children

        total = sum(weight(parent, child) for parent, child in edges)
        assert total == pytest.approx(kruskal_total_weight(names, weight))


def test_tree_respects_the_interval_and_missing_root():
    data = make_records({"Alpha": [1.0, 2.0, 3.0], "Beta": [3.0, 1.0, 2.0]})
    data.append(Record("Late", 50, 1.0, 0.0))
    data.append(Record("Late", 51, 2.0, 0.0))

    assert sorted(min_correlation_pathways(data, "Alpha", (1, 3))) == ["Alpha", "Beta"]
    assert min_correlation_pathways(data, "Alpha", (100, 200)) == {}
    assert min_correlation_pathways(data, "Missing", (1, 3)) == {}


def test_tree_leaves_out_cryptos_without_shared_days():
    data = make_records({"Alpha": [1.0, 2.0, 3.0], "Beta": [2.0, 1.0, 3.0]})
    data.append(Record("Lonely", 3, 5.0, 0.0))  # shares one day only
    tree = min_correlation_pathways(data, "Alpha", (1, 3))
    assert sorted(tree) == ["Alpha", "Beta"]


# --- nodes_at_level and correlated_cryptos_at_lvl_k ------------------------


def test_nodes_at_level_walks_the_tree_breadth_first():
    tree = {"a": ["b", "c"], "b": ["d"], "c": ["e", "f"], "d": [], "e": ["g"], "f": [], "g": []}
    assert nodes_at_level(tree, "a", 0) == ["a"]
    assert nodes_at_level(tree, "a", 1) == ["b", "c"]
    assert nodes_at_level(tree, "a", 2) == ["d", "e", "f"]
    assert nodes_at_level(tree, "a", 3) == ["g"]
    assert nodes_at_level(tree, "a", 4) == []
    assert nodes_at_level(tree, "a", -1) == []
    assert nodes_at_level(tree, "missing", 1) == []


def test_correlated_cryptos_at_lvl_k_returns_tree_and_level():
    data = make_records(
        {
            "Up": [1.0, 2.0, 3.0, 4.0],
            "AlsoUp": [2.0, 4.0, 6.0, 8.0],
            "Down": [4.0, 3.0, 2.0, 1.0],
        }
    )
    tree, level_two = correlated_cryptos_at_lvl_k(data, "Up", 2, (1, 4))
    assert tree == min_correlation_pathways(data, "Up", (1, 4))
    assert level_two == ["AlsoUp"]
