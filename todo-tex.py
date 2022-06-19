#!/usr/bin/env python3

import argparse
import re
import sys
import os
import collections
try:
    import chardet
except ImportError:
    chardet = None
if sys.platform == 'win32':
    import glob
try:
    import colorama
except ImportError:
    colorama = None
else:
    colorama.init()

__version__ = '3.0'
__author__ = 'Kaiwen Wu'

# any line satisfying this pattern, unless otherwise specified, is recorded
KEYWORDS_todo = {  # keyword : label
    'todo'              : 'TODO',
    'TODO'              : 'TODO',
    'question'          : 'QUESTION',
    'problem'           : 'PROBLEM',
    'continue here'     : 'TODO',
    'continue later'    : 'TODO',
    r'continue ?\.{3,}' : 'TODO',
}

KEYWORDS_done = {  # keyword : label
    'question solved'  : 'SOLVED',
    'problem solved'   : 'SOLVED',
    'done'             : 'SOLVED',
}

#################

KEYPATTERN = (r'([^\\]|^)%(?P<pfx_space>[ \t]*)(?P<key>'
              + '|'.join(list(KEYWORDS_done) + list(KEYWORDS_todo))
              + r')[ \t]*:?[ \t]*(?P<msg>\S.*)?$')
CONTPATTERN = r'^[ \t]*%(?P<pfx_space>[ \t]*)(?P<msg>\S.*)?$'
# Reference: https://blog.csdn.net/cysear/article/details/80435756
# Reference: https://github.com/hotoo/pangu.vim/blob/master/plugin/pangu.vim
HANS = (r'[\u4e00-\u9fa5\u3040-\u30ff\u3002\uff1f\uff01\uff0c\u3001\uff1b'
        r'\uff1a\u201c\u201d\u2018\u2019\uff08\uff09\u300a\u300b\u3008\u3009'
        r'\u3010\u3011\u300e\u300f\u300c\u300d\ufe43\ufe44\u3014\u3015\u2026'
        r'\u2014\uff5e\ufe4f\uffe5]')

COLOR_PURPLE = '\33[0;35m'
COLOR_GREEN = '\33[0;32m'
COLOR_BRED = '\33[1;31m'
COLOR_RST = '\33[0m'


def test_keypattern():
    matched = re.search(KEYPATTERN, 'blablabla % continue ...')
    assert matched.group('key') == 'continue ...'
    assert not matched.group('msg')
    matched = re.search(KEYPATTERN, 'blablabla % question solved: explanation')
    assert matched.group('key') == 'question solved'
    assert matched.group('msg') == 'explanation'


TexAnnotation = collections.namedtuple('TexAnnotation',
                                       ['ln', 'pfxlen', 'key', 'msg'])


def make_parser():
    parser = argparse.ArgumentParser(
        description=(
            'list filename and line '
            'numbers with "TODO", "todo", "continue here", "continue later", '
            '"continue ...", "question", "problem" at the head of comments of '
            'tex files'))
    parser.add_argument(
        '-L',
        dest='print_linenumber',
        action='store_false',
        help='suppress printing line numbers')
    parser.add_argument(
        '-D',
        dest='print_done',
        action='store_false',
        help='suppress printing entries of `done\' keyword')
    parser.add_argument(
        '-A',
        dest='print_label',
        action='store_false',
        help='suppress printing the label of the entry keywords')
    parser.add_argument(
        '-M',
        dest='print_message',
        action='store_false',
        help='suppress printing messages')
    parser.add_argument(
        '-d',
        dest='basedir',
        metavar='PATH',
        default='.',
        help=('the directory under which tex files are to be scanned. '
              'Default to current working directory'))
    parser.add_argument(
        '-r',
        dest='recursive',
        action='store_true',
        help='recursively search for tex files')
    parser.add_argument(
        '-c',
        dest='allow_continuation',
        action='store_true',
        help=('allow continuation of todo/done message on next lines by '
              'prefixing message with extra spaces'))
    parser.add_argument(
        '--heading',
        choices=['never', 'auto', 'always'],
        default='auto',
        help=('choose `always\' to always group the output and put filename '
              'in heading; choose `never\' to always put filename as a '
              'prefix; otherwise, make filename a prefix if not atty else as '
              'heading. Default to `%(default)s\''))
    parser.add_argument(
        '--color',
        choices=['never', 'auto', 'always'],
        default='auto',
        help='when to show color. Default to `%(default)s\'')
    parser.add_argument(
        'texfiles',
        metavar='TEXFILE',
        nargs='*',
        help=('specify certain TeX files to inspect. If there are TeX '
              'files specified in this way, the recursive option `-r\' and the'
              ' base directory option `-d\' will be deactivated. On Windows, '
              'python-style globbing is supported within the filename; '
              'otherwise see the filename expansion rule of the underlying '
              'shell'))
    parser.add_argument(
        '-V', '--version', action='version', version='%(prog)s ' + __version__)
    return parser


def scan_tex_file(lines_iter, allow_continuation):
    """
    :param lines_iter: an iterator of lines
    :param allow_continuation: whether to allow message continuation
    :return: the annotations
    :rtype: List[TexAnnotation]
    """
    annotations = []
    if not allow_continuation:
        for ln, line in enumerate(lines_iter, 1):
            line = line.rstrip('\n')
            matched = re.search(KEYPATTERN, line)
            if matched:
                annotations.append(
                    TexAnnotation(ln, len(matched.group('pfx_space')),
                                  matched.group('key'), matched.group('msg')))
    else:
        continuing = False
        for ln, line in enumerate(lines_iter, 1):
            line = line.rstrip('\n')
            if continuing:
                try:
                    prev_annot = annotations.pop()
                except IndexError:
                    continuing = False
                else:
                    matched = re.match(CONTPATTERN, line)
                    if (matched and len(matched.group('pfx_space')) >
                            prev_annot.pfxlen):
                        if not prev_annot.msg or not matched.group('msg'):
                            msgsep = ''
                        # handle Chinese
                        elif (prev_annot.msg
                                and re.match(HANS, prev_annot.msg[-1])
                                and matched.group('msg')
                                and re.match(HANS,
                                             matched.group('msg')[0])):
                            msgsep = ''
                        else:
                            msgsep = ' '
                        annotations.append(
                            TexAnnotation(
                                prev_annot.ln, prev_annot.pfxlen,
                                prev_annot.key,
                                msgsep.join(
                                    [prev_annot.msg or '',
                                     matched.group('msg') or ''])))
                    else:
                        annotations.append(prev_annot)
                        continuing = False
            if not continuing:
                matched = re.search(KEYPATTERN, line)
                if matched:
                    annotations.append(
                        TexAnnotation(ln, len(matched.group('pfx_space')),
                                      matched.group('key'),
                                      matched.group('msg')))
                    continuing = True
    return annotations


def test_scan_tex_file():
    lines = [
        'test test test % todo message message\n',
        '      %      message2 message2 message2\n'
    ]
    annots = scan_tex_file(iter(lines), False)
    assert len(annots) == 1
    assert annots[0].ln == 1
    assert annots[0].pfxlen == 1
    assert annots[0].key == 'todo'
    assert annots[0].msg == 'message message'
    annots = scan_tex_file(iter(lines), True)
    assert len(annots) == 1
    assert annots[0].ln == 1
    assert annots[0].pfxlen == 1
    assert annots[0].key == 'todo'
    assert annots[0].msg == 'message message message2 message2 message2'

    lines = [
        'test test test % todo message message\n',
        '      % question     message2 message2 message2\n'
    ]
    annots = scan_tex_file(iter(lines), False)
    assert len(annots) == 2
    assert annots[0].ln == 1
    assert annots[0].key == 'todo'
    assert annots[0].msg == 'message message'
    assert annots[1].ln == 2
    assert annots[1].key == 'question'
    assert annots[1].msg == 'message2 message2 message2'
    annots = scan_tex_file(iter(lines), True)
    assert len(annots) == 2
    assert annots[0].ln == 1
    assert annots[0].key == 'todo'
    assert annots[0].msg == 'message message'
    assert annots[1].ln == 2
    assert annots[1].key == 'question'
    assert annots[1].msg == 'message2 message2 message2'

    lines = [
        'test test test % todo message message\n',
        '      %   question   message2 message2 message2\n'
    ]
    annots = scan_tex_file(iter(lines), False)
    assert len(annots) == 2
    assert annots[0].ln == 1
    assert annots[0].key == 'todo'
    assert annots[0].msg == 'message message'
    assert annots[1].ln == 2
    assert annots[1].key == 'question'
    assert annots[1].msg == 'message2 message2 message2'
    annots = scan_tex_file(iter(lines), True)
    assert len(annots) == 1
    assert annots[0].ln == 1
    assert annots[0].key == 'todo'
    assert annots[0].msg == ('message message question   '
                             'message2 message2 message2')

    lines = [
        'test test test % todo\n',
        '     %   message2 message2\n',
    ]
    annots = scan_tex_file(iter(lines), True)
    assert len(annots) == 1
    assert annots[0].ln == 1
    assert annots[0].key == 'todo'
    assert annots[0].msg == 'message2 message2'

    lines = [
        'test test test % todo\n',
        '  %        \n',
    ]
    assert len(annots) == 1
    assert annots[0].ln == 1
    assert annots[0].key == 'todo'
    assert not annots[0].msg

    lines = [
        'test test test % todo message1\n',
        '  %         \n',
    ]
    assert len(annots) == 1
    assert annots[0].ln == 1
    assert annots[0].key == 'todo'
    assert annots[0].msg == 'message1'

    lines = [
        'test test test % todo 测试！\n',
        '  %   222 333 444\n',
    ]
    annots = scan_tex_file(iter(lines), True)
    assert len(annots) == 1
    assert annots[0].ln == 1
    assert annots[0].key == 'todo'
    assert annots[0].msg == '测试！222 333 444'

    lines = [
        'test test test % todo 测试\n',
        '  %   222 333 444\n',
    ]
    assert len(annots) == 1
    assert annots[0].ln == 1
    assert annots[0].key == 'todo'
    assert annots[0].msg == '测试 222 333 444'

    lines = [
        'test test test % todo 测试\n',
        '  %    再次测试\n',
    ]
    assert len(annots) == 1
    assert annots[0].ln == 1
    assert annots[0].key == 'todo'
    assert annots[0].msg == '测试再次测试'


def scan_bunch_of_texfiles(basedir, texfilenames, allow_continuation):
    per_file_annotations = collections.OrderedDict()
    for x in texfilenames:
        texfilepath = os.path.join(basedir, x)
        ec = None
        if chardet:
            with open(texfilepath, 'rb') as infile:
                ec = chardet.detect(infile.read())['encoding']
        with open(texfilepath, encoding=ec) as infile:
            annotations = scan_tex_file(infile, allow_continuation)
        if len(annotations) > 0:
            per_file_annotations[texfilepath] = annotations
    return per_file_annotations


def scan_directory(basedir, allow_continuation, recursive):
    """
    :param basedir: the path of directory to scan
    :param allow_continuation: whether to allow message continuation
    :param recursive: True to scan dirpath recursively
    :return: an OrderedDict object with key the tex file path and value the
             annotations
    """
    if not os.path.isdir(basedir):
        raise ValueError('basedir "{}" not found'.format(basedir))
    per_file_annotations = collections.OrderedDict()
    for root, _, files in os.walk(basedir):
        texfiles = [x for x in files if x.endswith('.tex')]
        per_file_annotations.update(
            scan_bunch_of_texfiles(root, texfiles, allow_continuation))
        if not recursive:
            break
    return per_file_annotations


def populate_result_line(sbuf, annot, print_linenumber, print_label,
                         print_message, color):
    if print_linenumber:
        if sbuf:
            sbuf.append(':')
        if color:
            sbuf.extend([COLOR_GREEN, str(annot.ln), COLOR_RST])
        else:
            sbuf.append(str(annot.ln))
    if print_label:
        if sbuf:
            sbuf.append(':')
        try:
            label = KEYWORDS_todo[annot.key]
        except KeyError:
            label = KEYWORDS_done[annot.key]
        if color:
            sbuf.extend([COLOR_BRED, label, COLOR_RST])
        else:
            sbuf.append(label)
    if print_message and annot.msg:
        if sbuf:
            sbuf.append(':')
        sbuf.append(annot.msg)


def show_result_heading(per_file_annotations, print_linenumber, print_done,
                        print_label, print_message, color):
    first_entry = True
    for texfilepath, annotations in per_file_annotations.items():
        annotations_to_show = [
            a for a in annotations if a.key in KEYWORDS_todo or (
                a.key in KEYWORDS_done and print_done)
        ]
        if not annotations_to_show:
            continue
        if not first_entry:
            print()
        if color:
            print(COLOR_PURPLE + texfilepath + COLOR_RST)
        else:
            print(texfilepath)
        if print_linenumber or print_label or print_message:
            for a in annotations_to_show:
                sbuf = []
                populate_result_line(sbuf, a, print_linenumber, print_label,
                                     print_message, color)
                print(''.join(sbuf))
            first_entry = False


def show_result_no_heading(per_file_annotations, print_linenumber, print_done,
                           print_label, print_message, color):
    for texfilepath, annotations in per_file_annotations.items():
        annotations_to_show = [
            a for a in annotations if a.key in KEYWORDS_todo or (
                a.key in KEYWORDS_done and print_done)
        ]
        for a in annotations_to_show:
            sbuf = []
            if color:
                sbuf.extend([COLOR_PURPLE, texfilepath, COLOR_RST])
            else:
                sbuf.append(texfilepath)
            populate_result_line(sbuf, a, print_linenumber, print_label,
                                 print_message, color)
            print(''.join(sbuf))


def show_result(per_file_annotations, print_linenumber, print_done,
                print_label, print_message, heading, color):
    if heading:
        show_result_heading(per_file_annotations, print_linenumber, print_done,
                            print_label, print_message, color)
    else:
        show_result_no_heading(per_file_annotations, print_linenumber,
                               print_done, print_label, print_message, color)


def resolve_color(color):
    if color == 'always':
        return True
    if color == 'never':
        return False
    return sys.stdout.isatty()


def resolve_heading(heading):
    if heading == 'always':
        return True
    if heading == 'never':
        return False
    return sys.stdout.isatty()


def main():
    args = make_parser().parse_args(sys.argv[1:])
    color = resolve_color(args.color)
    heading = resolve_heading(args.heading)
    if not args.texfiles:
        pfa = scan_directory(args.basedir, args.allow_continuation,
                             args.recursive)
    else:
        if sys.platform == 'win32':
            texfilenames = []
            for globtexfile in args.texfiles:
                texfilenames.extend(glob.glob(globtexfile))
        else:
            # the glob pattern should already be expanded by shell
            texfilenames = args.texfiles
        pfa = scan_bunch_of_texfiles(os.curdir, texfilenames,
                                     args.allow_continuation)
    show_result(pfa, args.print_linenumber, args.print_done, args.print_label,
                args.print_message, heading, color)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    except BrokenPipeError:
        sys.stderr.close()
