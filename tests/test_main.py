from src.main import should_ignore_file


def test_ignore_python_cache_directory():
    assert should_ignore_file("src/__pycache__/main.pyc") is True


def test_ignore_compiled_python_file():
    assert should_ignore_file("src/module.pyc") is True


def test_keep_python_source_file():
    assert should_ignore_file("src/main.py") is False


def test_ignore_virtual_environment():
    assert should_ignore_file(".venv/Lib/site-packages/example.py") is True


def test_keep_readme():
    assert should_ignore_file("README.md") is False


from src.main import find_hotspots


def test_find_hotspots():
    changes = {
        "src/main.py": 5,
        "README.md": 2,
        "src/utils.py": 3,
    }

    assert find_hotspots(changes) == {
        "src/main.py": 5,
        "src/utils.py": 3,
    }


def test_no_hotspots_below_threshold():
    changes = {
        "README.md": 1,
        "src/main.py": 2,
    }

    assert find_hotspots(changes) == {}


def test_custom_hotspot_threshold():
    changes = {
        "src/main.py": 4,
        "README.md": 2,
    }

    assert find_hotspots(changes, threshold=2) == changes
