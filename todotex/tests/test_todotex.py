from todotex import config
from todotex import todotex


class TestPatterns:
    def test_key(self):
        cfg = config.KeywordsConfig({'question': 'QUESTION'},
                                    {'question solved': 'SOLVED'})
        p = todotex.Patterns(cfg)

        doc = 'blah blah blah % question how to elaborate this?'
        matchobj = p.key.search(doc)
        assert matchobj is not None
        assert matchobj.group('key') == 'question'
        assert matchobj.group('pfx_space') == ' '
        assert matchobj.group('msg') == 'how to elaborate this?'

        doc = 'blah blah blah % question solved how to elaborate this?'
        matchobj = p.key.search(doc)
        assert matchobj is not None
        assert matchobj.group('key') == 'question solved'
        assert matchobj.group('pfx_space') == ' '
        assert matchobj.group('msg') == 'how to elaborate this?'


class TestScanTexDoc:
    def test_two_lines_no_cont(self):
        lines = [
            'test test test % todo message message\n',
            '      %      message2 message2 message2\n',
        ]
        p = todotex.Patterns(config.KeywordsConfig({'todo': 'TODO'}, {}))
        annots = todotex.scan_tex_doc(lines, False, p)
        assert len(annots) == 1
        assert annots[0].ln == 1
        assert annots[0].pfxlen == 1
        assert annots[0].key == 'todo'
        assert annots[0].msg == 'message message'

    def test_two_lines_cont(self):
        lines = [
            'test test test % todo message message\n',
            '      %      message2 message2 message2\n',
        ]
        p = todotex.Patterns(config.KeywordsConfig({'todo': 'TODO'}, {}))
        annots = todotex.scan_tex_doc(lines, True, p)
        assert len(annots) == 1
        assert annots[0].ln == 1
        assert annots[0].pfxlen == 1
        assert annots[0].key == 'todo'
        assert annots[0].msg == 'message message message2 message2 message2'

    def test_three_lines_cont(self):
        lines = [
            'test test test % todo message message\n',
            '      %      message2 message2\n',
            '      %    m3 m3\n',
        ]
        p = todotex.Patterns(config.KeywordsConfig({'todo': 'TODO'}, {}))
        annots = todotex.scan_tex_doc(lines, True, p)
        assert len(annots) == 1
        assert annots[0].ln == 1
        assert annots[0].pfxlen == 1
        assert annots[0].key == 'todo'
        assert annots[0].msg == 'message message message2 message2 m3 m3'

    def test_two_lines_two_keys(self):
        lines = [
            'test test test % todo message message\n',
            '      % question     message2 message2 message2\n',
        ]
        p = todotex.Patterns(
            config.KeywordsConfig({
                'todo': 'TODO',
                'question': 'TODO'
            }, {}))
        annots = todotex.scan_tex_doc(lines, False, p)
        assert len(annots) == 2
        assert annots[0].ln == 1
        assert annots[0].key == 'todo'
        assert annots[0].msg == 'message message'
        assert annots[1].ln == 2
        assert annots[1].key == 'question'
        assert annots[1].msg == 'message2 message2 message2'
        annots = todotex.scan_tex_doc(lines, True, p)
        assert len(annots) == 2
        assert annots[0].ln == 1
        assert annots[0].key == 'todo'
        assert annots[0].msg == 'message message'
        assert annots[1].ln == 2
        assert annots[1].key == 'question'
        assert annots[1].msg == 'message2 message2 message2'

    def test_two_lines_two_keys_ambiguity(self):
        lines = [
            'test test test % todo message message\n',
            '      %   question   message2 message2 message2\n',
        ]
        p = todotex.Patterns(
            config.KeywordsConfig({
                'todo': 'TODO',
                'question': 'TODO',
            }, {}))
        annots = todotex.scan_tex_doc(lines, False, p)
        assert len(annots) == 2
        assert annots[0].ln == 1
        assert annots[0].key == 'todo'
        assert annots[0].msg == 'message message'
        assert annots[1].ln == 2
        assert annots[1].key == 'question'
        assert annots[1].msg == 'message2 message2 message2'
        annots = todotex.scan_tex_doc(lines, True, p)
        assert len(annots) == 1
        assert annots[0].ln == 1
        assert annots[0].key == 'todo'
        assert annots[0].msg == ('message message question   '
                                 'message2 message2 message2')

    def test_two_lines_cont_key_on_its_own_line(self):
        lines = [
            'test test test % todo\n',
            '     %   message2 message2\n',
        ]
        p = todotex.Patterns(config.KeywordsConfig({'todo': 'TODO'}, {}))
        annots = todotex.scan_tex_doc(lines, True, p)
        assert len(annots) == 1
        assert annots[0].ln == 1
        assert annots[0].key == 'todo'
        assert annots[0].msg == 'message2 message2'

    def test_two_lines_cont_empty_second_line(self):
        lines = [
            'test test test % todo\n',
            '  %        \n',
        ]
        p = todotex.Patterns(config.KeywordsConfig({'todo': 'TODO'}, {}))
        annots = todotex.scan_tex_doc(lines, True, p)
        assert len(annots) == 1
        assert annots[0].ln == 1
        assert annots[0].key == 'todo'
        assert not annots[0].msg

        lines = [
            'test test test % todo message1\n',
            '  %         \n',
        ]
        p = todotex.Patterns(config.KeywordsConfig({'todo': 'TODO'}, {}))
        annots = todotex.scan_tex_doc(lines, True, p)
        assert len(annots) == 1
        assert annots[0].ln == 1
        assert annots[0].key == 'todo'
        assert annots[0].msg == 'message1'

    def test_two_lines_with_chinese_punc_ending_alphanum_beginning(self):
        lines = [
            'test test test % todo 测试！\n',
            '  %   222 333 444\n',
        ]
        p = todotex.Patterns(config.KeywordsConfig({'todo': 'TODO'}, {}))
        annots = todotex.scan_tex_doc(lines, True, p)
        assert len(annots) == 1
        assert annots[0].ln == 1
        assert annots[0].key == 'todo'
        assert annots[0].msg == '测试！222 333 444'

    def test_two_lines_with_chinese_ending_alphanum_beginning(self):
        lines = [
            'test test test % todo 测试\n',
            '  %   222 333 444\n',
        ]
        p = todotex.Patterns(config.KeywordsConfig({'todo': 'TODO'}, {}))
        annots = todotex.scan_tex_doc(lines, True, p)
        assert len(annots) == 1
        assert annots[0].ln == 1
        assert annots[0].key == 'todo'
        assert annots[0].msg == '测试 222 333 444'

    def test_two_lines_with_chinese_ending_chines_beginning(self):
        lines = [
            'test test test % todo 测试\n',
            '  %    再次测试\n',
        ]
        p = todotex.Patterns(config.KeywordsConfig({'todo': 'TODO'}, {}))
        annots = todotex.scan_tex_doc(lines, True, p)
        assert len(annots) == 1
        assert annots[0].ln == 1
        assert annots[0].key == 'todo'
        assert annots[0].msg == '测试再次测试'
