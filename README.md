# todo-tex.py -- Add TODO tag to LaTeX file

This Python3 utility parses LaTeX source codes for TODO tags and print them 
up on terminal. Supported TODO tags are `todo`, `TODO`, `fixme`, `FIXME`,
`question`, `problem`, `continue here`, `continue later`, `continue ...`.

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

With command `todo-tex.py -c` under directory of `sample.tex`, the output is

```
./sample.tex
3:TODO:some text
4:TODO:forgot what to write now
```

(with color)

## Detailed Help

See `todo-tex.py --help`.

## How to add/remove supported TODO tags

Go to the Python3 source code and modify the dictionay `KEYWORDS_todo` and/or 
`KEYWORDS_done`. The keys of the former dictionary are the TODO tags in 
LaTeX source to parse, and the values are what to be shown on terminal, i.e. 
the content in the square bracket in the sample output. The keys of the 
latter dictionary are the DONE tags in LaTeX source to parse, the values 
the same as previously stated.

Scenario to use DONE tags includes notes to previously posed `question` tag.
Option `-D` can be used to suppress showing DONE tags.

## Optional dependencies

- `chardet`, used to safely open text files with unknown encodings.
- `colorama`, used to color the output under Windows.

## Dev dependencies

To run the tests in `todo-tex.py`, you'll need

- `pytest`
