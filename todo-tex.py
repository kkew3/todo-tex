#!/usr/bin/python3

import argparse
import re
import sys
import os
from collections import OrderedDict
import chardet

__version__ = '2.0'
__author__  = 'Kaiwen Wu'


# any line satisfying this pattern, unless otherwise specified, is recorded
# KEYPATTERN = r'([^\\]|^)%[ \t]*(todo|TODO|question|problem|continue here|continue later|continue ?\.{3,})'
KEYWORDS_todo = {  # keyword : label
    'todo'              : 'TODO',
    'TODO'              : 'TODO',
    'question'          : 'QUESTION',
    'problem'           : 'PROBLEM',
    'continue here'     : 'TODO',
    'continue later'    : 'TODO',
    r'continue ?\.{3,}' : 'TODO'
}

KEYWORDS_done = {  # keyword : label
    r'question solved'  : 'SOLVED',
    r'problem solved'   : 'SOLVED'
}

KEYPATTERN = r'([^\\]|^)%[ \t]*('\
        + '|'.join(list(KEYWORDS_done) + list(KEYWORDS_todo))\
        + r')[ \t]*:?[ \t]*(.*)$'  # KEYPATTERN v2.0

def test_keypattern():
    """
    >>> _, kw, msg = re.findall(KEYPATTERN, 'blablabla % continue ...')[0]
    >>> assert kw == 'continue ...' and msg == ''
    >>> _, kw, msg = re.findall(KEYPATTERN, 'blablabla % question solved: explanation')[0]
    >>> assert kw in KEYWORDS_done and msg == 'explanation'
    """
    pass


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
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    return parser

def scan_tex_file(infile, keypattern):
    """
    :param infile: the file object with mode 'r'
    :param keypattern: the keypattern to use
    :return: the tuples (line number, keyword, message)
    """
    content = list(infile)
    annotations = []
    for lid, line in enumerate(content):
        line = line.rstrip()
        annot = re.findall(keypattern, line)
        if len(annot) > 0:
            assert len(annot) == 1
            annot = annot[0]
            annotations.append((lid + 1, annot[1], annot[2]))
    return annotations

def scan_bunch_of_texfiles(basedir, texfilenames, keypattern):
    texfile_linenumbers = OrderedDict()
    for x in texfilenames:
        texfilepath = os.path.join(basedir, x)
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
    for root, dirs, files in os.walk(dirpath):
        texfiles = [x for x in files if x.endswith('.tex')]
        texfile_annotations.update(scan_bunch_of_texfiles(
                root, texfiles, keypattern))
        if not recursive:
            break
    return texfile_annotations

def show_result(texfile_annotations, print_linenumber, print_done, print_label, print_message):
    for texfilepath in texfile_annotations:
        todo_count = len([(l,k,m) for l,k,m in texfile_annotations[texfilepath] if k in KEYWORDS_todo])
        if todo_count == 0 and not print_done:
            continue
        print(texfilepath)
        if print_linenumber:
            for linenumber, keyword, message in texfile_annotations[texfilepath]:
                if not (keyword in KEYWORDS_done and not print_done):
                    print('    %sline %d%s' % (
                            ('[' + (KEYWORDS_todo[keyword] if keyword in KEYWORDS_todo else KEYWORDS_done[keyword]) + '] ') if print_label else '',
                            linenumber,
                            (': ' + message) if print_message and message != '' else ''))

def main():
    args = make_parser().parse_args(sys.argv[1:])
    show_result(scan_directory(args.basedir, KEYPATTERN, args.recursive),
                args.print_linenumber, args.print_done, args.print_label, args.print_message)

if __name__ == '__main__':
    main()
