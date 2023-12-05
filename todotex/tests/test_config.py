from pathlib import Path

from todotex import config


def test_read_config():
    keywords = config.read_cfg(Path('todotex.example.toml'))
    assert keywords.todo == {
        'todo': 'TODO',
        'TODO': 'TODO',
        'fixme': 'TODO',
        'FIXME': 'TODO',
        'question': 'QUESTION',
        'problem': 'PROBLEM',
        'continue here': 'TODO',
        'continue later': 'TODO',
        r'continue ?\.{3,}': 'TODO',
    }
    assert keywords.done == {
        'question solved': 'SOLVED',
        'problem solved': 'SOLVED',
        'done': 'DONE',
    }
