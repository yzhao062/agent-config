import copy

from merge import deep_merge


def test_override_wins_scalar():
    assert deep_merge({"a": 1}, {"a": 2}) == {"a": 2}


def test_recursive():
    assert deep_merge({"a": {"x": 1, "y": 2}}, {"a": {"y": 3, "z": 4}}) == {"a": {"x": 1, "y": 3, "z": 4}}


def test_dict_replaced_by_scalar():
    assert deep_merge({"a": {"x": 1}}, {"a": 5}) == {"a": 5}


def test_scalar_replaced_by_dict():
    assert deep_merge({"a": 5}, {"a": {"x": 1}}) == {"a": {"x": 1}}


def test_keys_from_both_sides():
    assert deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}


def test_inputs_not_mutated():
    base = {"a": {"x": 1}, "l": [1]}
    over = {"a": {"y": 2}}
    b0, o0 = copy.deepcopy(base), copy.deepcopy(over)
    out = deep_merge(base, over)
    assert base == b0 and over == o0
    out["a"]["x"] = 99
    assert base["a"]["x"] == 1
