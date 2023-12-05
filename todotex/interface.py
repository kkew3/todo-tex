import argparse
from pathlib import Path
import sys
import collections
import typing as ty

from todotex.todotex import TexAnnotation
from todotex.config import KeywordsConfig


class Colors:
    purple = '\33[0;35m'
    green = '\33[0;32m'
    bold_red = '\33[1;31m'
    reset = '\33[0m'


def make_parser():
    parser = argparse.ArgumentParser(
        description='List TODO and DONE messages in TeX documents.',
        prog='todotex')
    parser.add_argument(
        '-C',
        '--config',
        type=Path,
        help=('the configuration file to use; default to '
              './.todotex.toml, ~/.config/todotex/todotex.toml, '
              '~/.todotex.toml, read in that order, and stop once success'))
    parser.add_argument(
        '-c',
        dest='allow_continuation',
        action='store_true',
        help=('allow continuation of todo/done message on next lines by '
              'prefixing message with extra spaces'))
    parser.add_argument(
        '-r',
        dest='recursive',
        action='store_true',
        help='search recursively into directories if provided as PATH')
    layout = parser.add_argument_group(
        title='optional layout arguments',
        description='options controlling the layout of the command output')
    layout.add_argument(
        '-L',
        dest='print_linenumber',
        action='store_false',
        help='suppress printing line numbers')
    layout.add_argument(
        '-D',
        dest='print_done',
        action='store_false',
        help='suppress printing entries of `done\' keyword')
    layout.add_argument(
        '-B',
        dest='print_label',
        action='store_false',
        help='suppress printing the label of the entry keywords')
    layout.add_argument(
        '-M',
        dest='print_message',
        action='store_false',
        help='suppress printing messages')
    layout.add_argument(
        '-a',
        action='store_true',
        dest='absolute_path',
        help=('show the matched TeX files in absolute path whenever '
              'possible; this will also resolve any symbolic links and `..\''))
    layout.add_argument(
        '--heading',
        choices=['never', 'auto', 'always'],
        default='auto',
        help=('choose `always\' to always group the output and put filename '
              'in heading; choose `never\' to always put filename as a '
              'prefix; otherwise, make filename a prefix if not atty else as '
              'heading. Default to `%(default)s\''))
    layout.add_argument(
        '--color',
        choices=['never', 'auto', 'always'],
        default='auto',
        help='when to show color. Default to `%(default)s\'')
    parser.add_argument(
        'files_or_dirs',
        metavar='PATH',
        nargs='*',
        help=('specify TeX files and/or directories under which TeX files '
              'are to be searched. If none is provided, stdin will be read '
              'for TeX file content'))
    return parser


class NoLeadingTrailingEmptyLinesBufferedWriter:
    """
    A buffered text writer that never echos leading/trailing newlines.
    It's recommended to use as context manager so as not to forget closing the
    writer.

    Example use: see tests.
    """
    def __init__(
        self,
        outfile: ty.TextIO,
        append_newline_when_commit: bool,
    ) -> None:
        """
        :param outfile: the caller is responsible to close this handler
        :param append_newline_when_commit: whether to append newline character
               to current line on each ``commit`` (more complicated than this)
        """
        self._prev_lines: ty.Deque[ty.List[str]] = collections.deque()
        self._curr_line: ty.List[str] = []
        self._outfile = outfile
        self._append_newline_when_commit = append_newline_when_commit

    def append(self, *s: str) -> 'NoLeadingTrailingEmptyLinesBufferedWriter':
        """Append token(s) to current line."""
        self._curr_line.extend(s)
        return self

    def commit(self) -> 'NoLeadingTrailingEmptyLinesBufferedWriter':
        """Write current line and prepare next line."""
        if self._curr_line:
            at_least_one_nonempty = False
            # flush the previous lines
            while self._prev_lines:
                lines = self._prev_lines.popleft()
                if lines:
                    at_least_one_nonempty = True
                if not at_least_one_nonempty:
                    continue
                suffix = ['\n'] if self._append_newline_when_commit else []
                self._outfile.write(''.join(lines + suffix))
            self._prev_lines.append(self._curr_line)
        else:
            self._prev_lines.append(self._curr_line)
        self._curr_line = []
        return self

    def close(self) -> None:
        # only two cases are possible:
        # 1) empty, empty, empty, ...;
        # 2) nonempty, empty, emtpy, empty, ...
        if self._prev_lines:
            lines = self._prev_lines.popleft()
            if lines:
                suffix = ['\n'] if self._append_newline_when_commit else []
                self._outfile.write(''.join(lines + suffix))

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        self.close()


def show_result(
    per_file_annots: ty.OrderedDict[ty.Optional[Path], ty.List[TexAnnotation]],
    keywords: KeywordsConfig,
    print_linenumber: bool,
    print_done: bool,
    print_label: bool,
    print_message: bool,
    absolute_path: bool,
    heading: ty.Literal['always', 'never', 'auto'],
    color: ty.Literal['always', 'never', 'auto'],
    # only set when debugging
    _out_buff: ty.TextIO = None,
) -> None:
    outfile = _out_buff if _out_buff else sys.stdout
    heading: bool = {
        'always': True,
        'never': False,
        'auto': sys.stdout.isatty(),
    }[heading]
    color: bool = {
        'always': True,
        'never': False,
        'auto': sys.stdout.isatty(),
    }[color]

    def to_show_annot(_a: TexAnnotation) -> bool:
        return (_a.key in keywords.todo
                or (print_done and _a.key in keywords.done))

    with NoLeadingTrailingEmptyLinesBufferedWriter(outfile, True) as w:
        if heading:
            for texfile, annots in per_file_annots.items():
                if texfile is not None:
                    if absolute_path:
                        texfile = texfile.resolve()
                    if color:
                        w.append(Colors.purple, str(texfile), Colors.reset)
                    else:
                        w.append(str(texfile))
                    w.commit()

                if print_linenumber or print_label or print_message:
                    a: TexAnnotation
                    for a in filter(to_show_annot, annots):
                        sbuf: ty.List[str] = []
                        if print_linenumber:
                            if color:
                                sbuf.append(
                                    f'{Colors.green}{a.ln}{Colors.reset}')
                            else:
                                sbuf.append(f'{a.ln}')
                        if print_label:
                            try:
                                label = keywords.todo[a.key]
                            except KeyError:
                                label = keywords.done[a.key]
                            if color:
                                sbuf.append(
                                    f'{Colors.bold_red}{label}{Colors.reset}')
                            else:
                                sbuf.append(label)
                        if print_message and a.msg:
                            sbuf.append(a.msg)
                        line = ':'.join(sbuf)
                        w.append(line).commit()
        else:
            for texfile, annots in per_file_annots.items():
                if texfile is not None:
                    if absolute_path:
                        texfile = texfile.resolve()
                a: TexAnnotation
                for a in filter(to_show_annot, annots):
                    sbuf: ty.List[str] = []
                    if texfile is not None:
                        if color:
                            sbuf.append(
                                f'{Colors.purple}{texfile}{Colors.reset}')
                        else:
                            sbuf.append(str(texfile))
                    if print_linenumber:
                        if color:
                            sbuf.append(f'{Colors.green}{a.ln}{Colors.reset}')
                        else:
                            sbuf.append(str(a.ln))
                    if print_label:
                        try:
                            label = keywords.todo[a.key]
                        except KeyError:
                            label = keywords.done[a.key]
                        if color:
                            sbuf.append(
                                f'{Colors.bold_red}{label}{Colors.reset}')
                        else:
                            sbuf.append(label)
                    if print_message and a.msg:
                        sbuf.append(a.msg)
                    line = ':'.join(sbuf)
                    if line:
                        w.append(line).commit()
