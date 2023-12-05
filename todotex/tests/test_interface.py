import io
from pathlib import Path
from collections import OrderedDict

from todotex import interface
from todotex.config import KeywordsConfig
from todotex.todotex import TexAnnotation


class TestOneLineBufferedWriter:
    def test_multiple_appends(self):
        cbuf = io.StringIO()
        with interface.NoLeadingTrailingEmptyLinesBufferedWriter(cbuf,
                                                                 True) as w:
            w.append('hello').append(' world').commit()
        cbuf.seek(0)
        assert cbuf.read() == 'hello world\n'

    def test_empty_commit(self):
        cbuf = io.StringIO()
        with interface.NoLeadingTrailingEmptyLinesBufferedWriter(cbuf,
                                                                 True) as w:
            w.append('hello').commit()
            w.commit()
            w.append('world').commit()
        cbuf.seek(0)
        assert cbuf.read() == 'hello\n\nworld\n'

    def test_ends_with_empty_commit(self):
        cbuf = io.StringIO()
        with interface.NoLeadingTrailingEmptyLinesBufferedWriter(cbuf,
                                                                 True) as w:
            w.append('hello').commit()
            w.append('world').commit()
            w.commit()
        cbuf.seek(0)
        assert cbuf.read() == 'hello\nworld\n'

    def test_starts_with_empty_commit(self):
        cbuf = io.StringIO()
        with interface.NoLeadingTrailingEmptyLinesBufferedWriter(cbuf,
                                                                 True) as w:
            w.commit()
            w.append('hello').commit()
            w.append('world').commit()
        cbuf.seek(0)
        assert cbuf.read() == 'hello\nworld\n'

    def test_only_empty_commit(self):
        cbuf = io.StringIO()
        with interface.NoLeadingTrailingEmptyLinesBufferedWriter(cbuf,
                                                                 True) as w:
            w.commit()
        cbuf.seek(0)
        assert cbuf.read() == ''


class TestShowResult:
    def test_heading_done(self):
        cbuf = io.StringIO()
        annots = OrderedDict({
            Path('sample.tex'): [
                TexAnnotation(3, 1, 'todo', 'some text'),
                TexAnnotation(4, 1, 'question solved', ''),
            ]
        })
        keywords = KeywordsConfig(
            {'todo': 'TODO'},
            {'question solved': 'SOLVED'},
        )
        interface.show_result(
            annots,
            keywords,
            True,
            True,
            True,
            True,
            False,
            'always',
            'never',
            cbuf,
        )
        cbuf.seek(0)
        assert cbuf.read() == 'sample.tex\n3:TODO:some text\n4:SOLVED\n'

    def test_heading_no_done(self):
        cbuf = io.StringIO()
        annots = OrderedDict({
            Path('sample.tex'): [
                TexAnnotation(3, 1, 'todo', 'some text'),
                TexAnnotation(4, 1, 'question solved', ''),
            ]
        })
        keywords = KeywordsConfig(
            {'todo': 'TODO'},
            {'question solved': 'SOLVED'},
        )
        interface.show_result(
            annots,
            keywords,
            True,
            False,
            True,
            True,
            False,
            'always',
            'never',
            cbuf,
        )
        cbuf.seek(0)
        assert cbuf.read() == 'sample.tex\n3:TODO:some text\n'

    def test_no_heading_done(self):
        cbuf = io.StringIO()
        annots = OrderedDict({
            Path('sample.tex'): [
                TexAnnotation(3, 1, 'todo', 'some text'),
                TexAnnotation(4, 1, 'question solved', ''),
            ]
        })
        keywords = KeywordsConfig(
            {'todo': 'TODO'},
            {'question solved': 'SOLVED'},
        )
        interface.show_result(
            annots,
            keywords,
            True,
            True,
            True,
            True,
            False,
            'never',
            'never',
            cbuf,
        )
        cbuf.seek(0)
        assert (cbuf.read() ==
                'sample.tex:3:TODO:some text\nsample.tex:4:SOLVED\n')

    def test_stdin_heading_done(self):
        cbuf = io.StringIO()
        annots = OrderedDict({
            None: [
                TexAnnotation(3, 1, 'todo', 'some text'),
                TexAnnotation(4, 1, 'question solved', ''),
            ]
        })
        keywords = KeywordsConfig(
            {'todo': 'TODO'},
            {'question solved': 'SOLVED'},
        )
        interface.show_result(
            annots,
            keywords,
            True,
            True,
            True,
            True,
            False,
            'always',
            'never',
            cbuf,
        )
        cbuf.seek(0)
        assert cbuf.read() == '3:TODO:some text\n4:SOLVED\n'

    def test_stdin_no_heading_done(self):
        cbuf = io.StringIO()
        annots = OrderedDict({
            None: [
                TexAnnotation(3, 1, 'todo', 'some text'),
                TexAnnotation(4, 1, 'question solved', ''),
            ]
        })
        keywords = KeywordsConfig(
            {'todo': 'TODO'},
            {'question solved': 'SOLVED'},
        )
        interface.show_result(
            annots,
            keywords,
            True,
            True,
            True,
            True,
            False,
            'never',
            'never',
            cbuf,
        )
        cbuf.seek(0)
        assert cbuf.read() == '3:TODO:some text\n4:SOLVED\n'
