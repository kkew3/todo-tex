import dataclasses
import itertools
import os
import re
from pathlib import Path
import collections
import typing as ty

from todotex.config import KeywordsConfig


class Patterns:
    def __init__(self, cfg: KeywordsConfig):
        # the pattern matching the start of todo key
        self.key = re.compile(r'([^\\]|^)%(?P<pfx_space>[ \t]*)(?P<key>'
                              # note the order
                              + '|'.join(itertools.chain(cfg.done, cfg.todo))
                              + r')[ \t]*:?[ \t]*(?P<msg>\S.*)?$')
        # the pattern matching the continual message
        self.cont = re.compile(r'^[ \t]*%(?P<pfx_space>[ \t]*)(?P<msg>\S.*)?$')
        # the Chinese characters
        self.hans = re.compile(r'[\u4e00-\u9fa5\u3040-\u30ff]')
        # the Chinese punctuations
        self.hans_punc = re.compile(
            r'[\u3002\uff1f\uff01\uff0c\u3001\uff1b'
            r'\uff1a\u201c\u201d\u2018\u2019\uff08\uff09\u300a\u300b\u3008'
            r'\u3009\u3010\u3011\u300e\u300f\u300c\u300d\ufe43\ufe44\u3014'
            r'\u3015\u2026\u2014\uff5e\ufe4f\uffe5]')


@dataclasses.dataclass
class TexAnnotation:
    ln: int
    pfxlen: int
    key: str
    msg: str


def scan_tex_doc(
    doc: ty.Union[ty.Iterable[str], ty.TextIO],
    allow_continuation: bool,
    p: Patterns,
) -> ty.List[TexAnnotation]:
    """
    :param doc: an iterable of lines
    :param allow_continuation: whether to allow message continuation
    :param p: the patterns
    :return: the annotations
    """
    annotations = []
    if not allow_continuation:
        for ln, line in enumerate(doc, 1):
            line = line.rstrip('\n')
            matched = p.key.search(line)
            if matched:
                annotations.append(
                    TexAnnotation(ln, len(matched.group('pfx_space')),
                                  matched.group('key'), matched.group('msg')))
    else:
        continuing = False
        for ln, line in enumerate(doc, 1):
            line = line.rstrip('\n')
            if continuing:
                if not annotations:
                    continuing = False
                else:
                    prev_annot = annotations.pop()
                    matched = p.cont.match(line)
                    if (matched and len(matched.group('pfx_space')) >
                            prev_annot.pfxlen):
                        if not prev_annot.msg or not matched.group('msg'):
                            msgsep = ''
                        # handle Chinese and Chinese punctuation
                        elif ((p.hans.match(prev_annot.msg[-1])
                               and p.hans.match(matched.group('msg')[0])) or
                              (p.hans_punc.match(prev_annot.msg[-1])
                               or p.hans_punc.match(matched.group('msg')[0]))):
                            msgsep = ''
                        else:
                            msgsep = ' '
                        prev_annot_msg = prev_annot.msg or ''
                        curr_annot_msg = matched.group('msg') or ''
                        annotations.append(
                            TexAnnotation(
                                prev_annot.ln,
                                prev_annot.pfxlen,
                                prev_annot.key,
                                f'{prev_annot_msg}{msgsep}{curr_annot_msg}',
                            ))
                    else:
                        annotations.append(prev_annot)
                        continuing = False
            if not continuing:
                matched = p.key.search(line)
                if matched:
                    annotations.append(
                        TexAnnotation(ln, len(matched.group('pfx_space')),
                                      matched.group('key'),
                                      matched.group('msg')))
                    continuing = True
    return annotations


def scan_fs_for_tex(
    paths: ty.Iterable[Path],
    p: Patterns,
    recursive: bool,
    allow_continuation: bool,
    chardet,
) -> ty.OrderedDict[Path, ty.List[TexAnnotation]]:
    """
    :param paths: paths to search for TeX files
    :param p: the patterns
    :param recursive: whether to search with recursion
    :param allow_continuation: whether to allow message continuation
    :param chardet: if of type ``str``, the encoding for the TeX files to open;
           otherwise, the ``chardet`` package
           (https://github.com/chardet/chardet)
    :return: a dict of TeX file path mapped to annotations
    """
    per_file_annotations = collections.OrderedDict()

    def _scan_and_add_to_annots(_path: Path):
        if isinstance(chardet, str):
            ec = chardet
        else:
            with open(_path, 'rb') as infile:
                # sample the first 64 KiB for chardet
                ec = chardet.detect(infile.read(1024 * 64))['encoding']
        with open(_path, encoding=ec) as infile:
            annots = scan_tex_doc(infile, allow_continuation, p)
        if annots:
            per_file_annotations[_path] = annots

    for path in paths:
        if path.is_file() and path.suffix == '.tex':
            _scan_and_add_to_annots(path)
        elif path.is_dir() and not recursive:
            for child in path.iterdir():
                if child.is_file() and child.suffix == '.tex':
                    _scan_and_add_to_annots(child)
        elif path.is_dir():
            for root, _, files in os.walk(path):
                for name in files:
                    child = Path(root) / name
                    if child.suffix == '.tex':
                        _scan_and_add_to_annots(child)
    return per_file_annotations
