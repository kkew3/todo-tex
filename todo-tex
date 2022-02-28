#!/usr/bin/env python3

import argparse
import re
import sys
import os
from collections import OrderedDict
try:
    import chardet
except ImportError:
    chardet = None
if sys.platform == 'win32':
    import glob

__version__ = '2.1'
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

KEYPATTERN = (r'([^\\]|^)%[ \t]*('
              + '|'.join(list(KEYWORDS_done) + list(KEYWORDS_todo))
              + r')[ \t]*:?[ \t]*(.*)$')

def test_keypattern():
    matched = re.search(KEYPATTERN, 'blablabla % continue ...')
    assert matched.group(2) == 'continue ...'
    assert matched.group(3) == ''
    matched = re.search(KEYPATTERN, 'blablabla % question solved: explanation')
    assert matched.group(2) == 'question solved'
    assert matched.group(3) == 'explanation'


#################

def make_parser():
    parser = argparse.ArgumentParser(description='list filename and line '
            'numbers with "TODO", "todo", "continue here", "continue later", '
            '"continue ...", "question", "problem" at the head of comments of '
            'tex files')
    parser.add_argument('-L', dest='print_linenumber', action='store_false',
            help='suppress printing line numbers')
    parser.add_argument('-D', dest='print_done', action='store_false',
            help='suppress printing entries of `done\' keyword')
    parser.add_argument('-l', dest='print_label', action='store_true',
            help='print the label of the entry keywords')
    parser.add_argument('-m', dest='print_message', action='store_true',
            help='print the messages')
    parser.add_argument('-d', dest='basedir', metavar='PATH', default='.',
            help='the directory under witch tex files are to be scaned, '
            'default to current working directory')
    parser.add_argument('-r', dest='recursive', action='store_true',
            help='recursively search for tex files')
    parser.add_argument('texfiles', metavar='TEXFILE', nargs='*',
            help='specify certain TeX files to inspect. If there are TeX '
            'files specified in this way, the recursive option `-r` and the '
            'base directory option `-d` will be deactivated. On Windows, '
            'python-style globbing is supported within the filename; '
            'otherwise see the filename expansion rule of the underlying '
            'shell')
    parser.add_argument('-V', '--version', action='version',
            version='%(prog)s ' + __version__)
    return parser

def scan_tex_file(infile, keypattern):
    """
    :param infile: the file object with mode 'r'
    :param keypattern: the keypattern to use
    :return: the tuples (line number, keyword, message)
    """
    annotations = []
    for lid, line in enumerate(infile):
        line = line.rstrip()
        matched = re.search(keypattern, line)
        if matched:
            annotations.append((lid + 1, matched.group(2), matched.group(3)))
    return annotations

def scan_bunch_of_texfiles(basedir, texfilenames, keypattern):
    texfile_linenumbers = OrderedDict()
    for x in texfilenames:
        texfilepath = os.path.join(basedir, x)
        ec = None
        if chardet:
            with open(texfilepath, 'rb') as infile:
                ec = chardet.detect(infile.read())['encoding']
        with open(texfilepath, encoding=ec) as infile:
            annotations = scan_tex_file(infile, keypattern)
        if len(annotations) > 0:
            texfile_linenumbers[texfilepath] = annotations
    return texfile_linenumbers

def scan_directory(dirpath, keypattern, recursive):
    """
    :param dirpath: the path of directory to scan
    :param keypattern: the keypattern to use
    :param recursive: True to scan dirpath recursively
    :return: an OrderedDict object with key the tex file path and value the
             annotations
    """
    if not os.path.isdir(dirpath):
        raise ValueError('dirpath "' + str(dirpath) + '" not found')
    texfile_annotations = OrderedDict()
    for root, _, files in os.walk(dirpath):
        texfiles = [x for x in files if x.endswith('.tex')]
        texfile_annotations.update(scan_bunch_of_texfiles(
            root, texfiles, keypattern))
        if not recursive:
            break
    return texfile_annotations

def show_result(texfile_annotations, print_linenumber, print_done, print_label, print_message):
    for texfilepath in texfile_annotations:
        todo_count = len([(l, k, m)
                          for l, k, m in texfile_annotations[texfilepath]
                          if k in KEYWORDS_todo])
        if todo_count == 0 and not print_done:
            continue
        print(texfilepath)
        if print_linenumber:
            for linenumber, keyword, message in texfile_annotations[texfilepath]:
                if not (keyword in KEYWORDS_done and not print_done):
                    if print_label:
                        try:
                            label = KEYWORDS_todo[keyword]
                        except KeyError:
                            label = KEYWORDS_done[keyword]
                        if print_message and message:
                            print('    [{}] line {}: {}'
                                  .format(label, linenumber, message))
                        else:
                            print('    [{}] line {}'.format(label, linenumber))
                    else:
                        if print_message and message:
                            print('    line {}: {}'.format(linenumber, message))
                        else:
                            print('    line {}'.format(linenumber))

def main():
    args = make_parser().parse_args(sys.argv[1:])
    if len(args.texfiles) == 0:
        show_result(scan_directory(args.basedir, KEYPATTERN, args.recursive),
                    args.print_linenumber, args.print_done, args.print_label,
                    args.print_message)
    else:
        if sys.platform == 'win32':
            texfilenames = []
            for globtexfile in args.texfiles:
                texfilenames.extend(glob.glob(globtexfile))
        else:
            # the glob pattern should already be expanded by shell
            texfilenames = args.texfiles
        show_result(scan_bunch_of_texfiles(os.curdir, texfilenames,
                                           KEYPATTERN),
                    args.print_linenumber, args.print_done, args.print_label,
                    args.print_message)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    except BrokenPipeError:
        sys.stderr.close()
