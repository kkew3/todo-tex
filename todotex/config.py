import dataclasses
import typing as ty
from pathlib import Path

import tomli


@dataclasses.dataclass
class KeywordsConfig:
    todo: ty.Dict[str, str]
    done: ty.Dict[str, str]


def _parse_cfg_obj(o):
    d = {}
    for m in o:
        d[m['key']] = m['label']
    return d


def read_cfg(config_path: Path = None):
    read_order = [
        config_path,
        Path.cwd() / '.todotex.toml',
        Path('~/.config/todotex/todotex.toml').expanduser(),
        Path('~/.todotex.toml').expanduser(),
    ]
    for path in read_order:
        if path:
            try:
                with open(path, 'rb') as infile:
                    cfg = tomli.load(infile)
                return KeywordsConfig(
                    _parse_cfg_obj(cfg.get('todo', [])),
                    _parse_cfg_obj(cfg.get('done', [])))
            except FileNotFoundError:
                pass
    return KeywordsConfig({}, {})
