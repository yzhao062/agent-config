from config import read_config


def write(tmp_path, text):
    path = tmp_path / "app.toml"
    path.write_text(text)
    return path


def test_returns_tuple_of_ints(tmp_path):
    got = read_config(write(tmp_path, "timeout = 30\nretries = 3\n"))
    assert got == (30, 3)
    assert isinstance(got, tuple) and all(type(v) is int for v in got)


def test_ignores_other_keys_and_order(tmp_path):
    text = 'name = "svc"\nretries = 2\ntimeout = 10\n\n[db]\nhost = "x"\n'
    assert read_config(write(tmp_path, text)) == (10, 2)
