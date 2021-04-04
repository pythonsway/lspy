import argparse
import datetime
import locale
import math
import os
import shutil
import stat
import sys
from pathlib import Path

from .utils.constants import COLORS

# set locale for all categories to the user’s default setting
locale.setlocale(locale.LC_ALL, '')


def parse_args():
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser(prog='lspy',
                                     description='List information about the FILEs')
    parser.add_argument('--long', '-l', action='store_true',
                        help='use a long listing format')
    parser.add_argument('--all', '-a', action='store_true',
                        help='do not ignore entries starting with .')
    parser.add_argument('--sort', '-S', action='store_true',
                        help='sort by file size, largest first')
    parser.add_argument('--recursive', '-R', action='store_true',
                        help='list subdirectories recursively')
    parser.add_argument('files', type=str, nargs='*', default='.',
                        help='file paths')
    return parser.parse_args()


def ls_long(args):
    """Long list format output."""
    total_blocks = 0
    for idf, files in enumerate(list_dir(args)):
        entries = []
        for fn in files:
            filestats = os.lstat(fn)
            mode = stat.filemode(filestats.st_mode)
            nlink = str(filestats.st_nlink)
            # WindowsOS - workaround
            try:
                from grp import getgrgid
                from pwd import getpwuid
                owner = getpwuid(filestats.st_uid).pw_name
                group = getgrgid(filestats.st_uid).gr_name
            except ImportError:
                owner = str(filestats.st_gid)
                group = str(filestats.st_uid)
            size = str(filestats.st_size)
            # assumption: BLOCKSIZE=1024 bytes
            total_blocks += math.ceil(filestats.st_size / 1024)
            dt = datetime.datetime.fromtimestamp(filestats.st_mtime)
            if dt < datetime.datetime.now() - datetime.timedelta(days=365):
                time = dt.strftime('%b %d  %Y')
            else:
                time = dt.strftime('%b %d %H:%M')
            fn_name, color_name = prep_name(fn, filestats)
            long_entry = [mode, nlink, owner, group, size, time, fn_name, color_name]
            entries.append(long_entry)
        entries.sort(key=lambda x: locale.strxfrm(x[-2]))
        if args.recursive and entries[0][1].startswith('..'):
            entries[0], entries[1] = entries[1], entries[0]
        if args.sort:
            entries.sort(key=lambda x: x[4], reverse=True)
        column_widths = []
        for i in range(len(entries[0]) - 2):
            column = [row[i] for row in entries]
            column_widths.append(len(max(column, key=len)))
        text_header(args, files, idf)
        print(f'total: {total_blocks}')
        for entry in entries:
            formatted_entry = ' '.join(
                [s.rjust(column_widths[i])
                 for i, s in enumerate(entry[:-2])] + [entry[-1]]
            )
            print(formatted_entry)
        print('')


def ls_short(args):
    """Short list format output."""
    for idf, files in enumerate(list_dir(args)):
        entries = []
        for fn in files:
            filestats = os.lstat(fn)
            size = str(filestats.st_size)
            fn_name, color_name = prep_name(fn, filestats)
            short_entry = [size, fn_name, color_name]
            entries.append(short_entry)
        entries.sort(key=lambda x: locale.strxfrm(x[-2]))
        if args.recursive and entries[0][1].startswith('..'):
            entries[0], entries[1] = entries[1], entries[0]
        if args.sort:
            entries.sort(key=lambda x: x[0], reverse=True)
        column_widths = max(len(row[-2]) for row in entries)
        terminal_size = shutil.get_terminal_size()
        num_cols = terminal_size.columns // column_widths
        num_rows = math.ceil(len(entries) / num_cols)
        grouped_rows = [[] for _ in range(num_rows)]
        text_header(args, files, idf)
        for idxr, r in enumerate(entries):
            grouped_rows[idxr % num_rows].append(r)
        for row in grouped_rows:
            for entry in row:
                separator = column_widths - len(entry[-2])
                rest = ' '*separator
                print(f'{entry[-1]+rest}'.ljust(column_widths), end='')
            print('')
        print('')


def prep_name(fn, filestats):
    """Prepare names for display."""
    color = COLORS['DEFAULT']
    fn_name = '.' if fn == Path(os.curdir) else fn.name
    rest = ''
    if stat.S_ISDIR(filestats.st_mode):
        rest = '/'
        color = COLORS['DIR']
    elif stat.S_ISCHR(filestats.st_mode):
        color = COLORS['CHR']
    elif stat.S_ISBLK(filestats.st_mode):
        color = COLORS['BLK']
    elif stat.S_ISFIFO(filestats.st_mode):
        color = COLORS['FIFO']
    elif stat.S_ISSOCK(filestats.st_mode):
        color = COLORS['SOCK']
    elif stat.S_ISDOOR(filestats.st_mode):
        color = COLORS['DOOR']
    elif not os.path.exists(fn):
        color = COLORS['MISSING']
    elif stat.S_ISREG(filestats.st_mode):
        if fn.suffix in COLORS:
            color = COLORS[fn.suffix]
    elif stat.S_ISLNK(filestats.st_mode):
        symlink_target = os.readlink(fn)
        fn_name = f'{fn_name} -> {symlink_target}'
        color = COLORS['LINK']
    ansi_esc = '\033[{color}m {name}\033[00m{rest}'
    color_name = ansi_esc.format(color=color, name=fn_name, rest=rest)
    full_name = f'{fn_name}{rest}'
    return (full_name, color_name)


def text_header(args, files, idf):
    """Prepare text header."""
    if args.recursive:
        print(f'./{files[-1].parent}:')
    else:
        if len(args.files) > 1:
            print(f'{args.files[idf]}:')


def list_dir(args):
    """Find names of the entries in the directory given by path."""
    dirs = []
    for idp, path in enumerate(args.files):
        path_path = Path(path)
        if path_path.exists():
            if path_path.is_file():
                dirs.append([path_path])
            else:
                if args.recursive:
                    for root, dirs_r, files_r in os.walk(path_path):
                        path_root = Path(root)
                        dirs_str = [(path_root / n) for n in [*dirs_r, *files_r]]
                        if args.all:
                            dirs_str = [Path('.'), path_root / '..', *dirs_str]
                        dirs.append(dirs_str)
                else:
                    dirs.append([(path_path / n) for n in os.listdir(path)])
                    if args.all:
                        cur_dir = path_path.parent
                        par_dir = path_path / '..'
                        dirs[idp] = [cur_dir, par_dir, *dirs[idp]]
                    else:
                        dirs[idp] = [dir for dir in dirs[idp] if not dir.name.startswith('.')]
        else:
            print('Specified path does not exist.')
            sys.exit()
    return dirs


def lspy():
    """Entry point for 'ls':
    List information about the FILEs (the current directory by default).
    """
    args = parse_args()
    try:
        if args.long:
            ls_long(args)
        else:
            ls_short(args)
    except OSError as e:
        print(e.strerror)


if __name__ == '__main__':
    lspy()
