import sys
import itertools
from pathlib import Path

if sys.platform == 'win32':
    try:
        import chardet
    except ImportError:
        import locale
        chardet = locale.getpreferredencoding(False)
else:
    chardet = 'utf-8'

if sys.platform == 'win32':
    import glob

if sys.platform == 'win32':
    try:
        from colorama import just_fix_windows_console
        just_fix_windows_console()
        allow_color = True
    except ImportError:
        allow_color = False
else:
    allow_color = True

from todotex import config
from todotex import todotex
from todotex import interface


def main():
    args = interface.make_parser().parse_args()
    keywords = config.read_cfg(args.config)
    pat = todotex.Patterns(keywords)
    if args.files_or_dirs:
        if sys.platform == 'win32':
            files_or_dirs = map(
                Path,
                itertools.chain.from_iterable(
                    map(glob.glob, args.files_or_dirs)))
        else:
            files_or_dirs = map(Path, args.files_or_dirs)
        annots = todotex.scan_fs_for_tex(
            files_or_dirs,
            pat,
            args.recursive,
            args.allow_continuation,
            chardet,
        )
    else:
        annots = todotex.scan_tex_doc(
            sys.stdin,
            args.allow_continuation,
            pat,
        )
    interface.show_result(
        annots,
        keywords,
        args.print_linenumber,
        args.print_done,
        args.print_label,
        args.print_message,
        args.absolute_path,
        args.heading,
        args.color if allow_color else 'never',
    )


if __name__ == '__main__':
    try:
        main()
    except BrokenPipeError:
        pass
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as err:
        print(err, file=sys.stderr)
        sys.exit(1)
