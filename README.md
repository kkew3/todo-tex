# todo-tex -- Add TODO tag to LaTeX file

This Python3 utility parses LaTeX source codes for TODO tags and print them 
up on terminal. Supported TODO tags are `todo`, `TODO`, `question`, 
`problem`, `continue here`, `continue later`, `continue ...`.

## Sample Usage

myfile.tex:

	\documentclass{article}
	\begin{document}
	Superchiasmatic neucleus is the primary clock % continue later: forgot what to write now
	\end{document}

With command `todo-tex -lm` under directory of `myfile.tex`, the output is

	./myfile.tex
	    [TODO] line 3: forgot what to write now

## Detailed Help

See `todo-tex --help`.

## How to add/remove supported TODO tags

Go to the Python3 source code and modify the dictionay `KEYWORDS_todo` and/or 
`KEYWORDS_done`. The keys of the former dictionary are the TODO tags in 
LaTeX source to parse, and the values are what to be shown on terminal, i.e. 
the content in the square bracket in the sample output. The keys of the 
latter dictionary are the DONE tags in LaTeX source to parse, the values 
the same as previously stated.

Scenario to use DONE tags includes notes to previously posed `question` tag.
Option `-D` can be used to suppress showing DONE tags.
For example: `todo-tex -Dlm`.

## Optional dependencies

- `chardet`, used to safely open text files with unknown encodings.
