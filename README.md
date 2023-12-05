# todotex -- Add TODO tag to LaTeX file

This Python3 utility parses LaTeX source codes for TODO tags and print them up on terminal.
Supported TODO tags are `todo`, `TODO`, `fixme`, `FIXME`, `question`, `problem`, etc.
You may modify the example configuration `todotex.example.toml` to your like and place it at `~/.config/todotex/todotex.toml` (see `--help` for detail).

## Sample Usage

`sample.tex`:

```
\documentclass{article}
\begin{document}
% todo some text
Superchiasmatic neucleus is the primary clock % continue later: forgot
                                              %   what to write now
\end{document}
```

With command `python3 -m todotex -c .` under directory of `sample.tex`, the output is

```
sample.tex
3:TODO:some text
4:TODO:forgot what to write now
```

(with color)

## Installation

Simply add `todotex` to your `PYTHONPATH`.

For example, suppose that all dependencies has been installed to `~/miniconda3/envs/hello/bin/python3`, and that this repo has been cloned to `/path/to/todo-tex`.
You may run the utility via:

```bash
PYTHONPATH=/path/to/todo-tex ~/miniconda3/envs/hello/bin/python3 -m todotex --help
```

Or you may put the following text to a shell script, and call the shell script with arguments:

```bash
PYTHONPATH=/path/to/todo-tex ~/miniconda3/envs/hello/bin/python3 -m todotex "$@"
```

## Detailed Help

See `python3 -m todotex --help`.

## The configuration file

Each `key` refers to the TODO/DONE tags in TeX source to parse, and each `label` refers to what to be shown in terminal.
The `todo` list collects all TODO tags and labels.
The `done` list collects all DONE tags and labels.

Scenario to use DONE tags includes notes to previously posed `question` tag.
Option `-D` can be used to suppress showing DONE tags.

An example configuration is provided at `todotex.example.toml`.

## Dependencies

- [`tomli`](https://github.com/hukkin/tomli): used to parse configuration file

### Optional dependencies

- [`chardet`](https://github.com/chardet/chardet) (relevant only under Windows): used to safely open text files with unknown encodings
- [`colorama`](https://github.com/tartley/colorama), used to color the output under Windows

### Dev dependencies

To run the tests in `todotex`, you'll need [`pytest`](https://docs.pytest.org/en/7.4.x/):

```bash
pytest todotex/tests
```
