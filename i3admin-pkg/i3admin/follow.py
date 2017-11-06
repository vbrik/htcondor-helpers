#!/usr/bin/env python
# $Id: follow.py 511 2014-09-18 18:14:16Z vbrik $
from __future__ import division
from __future__ import print_function
import argparse
import os
import sys
import time

stderr = lambda *args: print(*args, file=sys.stderr)

def _get_file(filename, sleep=1.0, retry=False):
    while True:
        try:
            stat = os.stat(filename)
            fobj = open(filename)
        except (IOError, OSError) as e:
            stderr('follow: problem with file "%s": %s' % (filename, e.args))
            if retry:
                time.sleep(sleep)
                continue
            else:
                raise
        return fobj,stat


def follow(filename, sleep=1.0, from_tail=True, keep_trying=True):
    curfile,curfstat = _get_file(filename, keep_trying, sleep)
    linebuf = ""
    if from_tail:
        # keep reading until reach end of file; if file ends with a newline
        # linebuf should be empty, otherwise we are probably seeing a partial
        # write, and want linebuf to contain the last line.
        while True:
            linebuf = curfile.readline()
            if linebuf == "":
                break
            elif linebuf[-1] != '\n':
                stderr('follow: no newline at end of file; linebuf="%s"' % linebuf)
                break
    while True:
        line = curfile.readline()
        linebuf += line
        if linebuf.endswith('\n'):
            yield linebuf.strip()
            linebuf = ""
            continue
        # readline(): '\n' is left at the end of the string, and is only omitted 
        # on the last line of the file if the file doesn't end in a newline.
        # So, at this point we are at eof, but the last line may still be buffered.
        if keep_trying:
            # Open the filename again to check later if anything has changed.
            # First, try _get_file() without retrying on failure (e.g. because 
            # file has been deleted) because if a failure does occur, we need 
            # to flush buffers before retrying _get_file() indefinitely
            try:
                newfile, newfstat = _get_file(filename, sleep, retry=False)
            except (IOError, OSError) as e:
                if linebuf:
                    stderr('follow: forced to flush; linebuf="%s"' % linebuf)
                    yield linebuf
                    linebuf = ""
                newfile, newfstat = _get_file(filename, sleep, retry=True)
            if newfstat.st_ino != curfstat.st_ino:
                stderr('follow: file inode changed; re-opening %s' % filename)
                curfile.close()
                curfile,curfstat = newfile, newfstat
                # since we are switching to a new file, flush any old buffered
                # data, even if the old file did not end with a newline
                if linebuf:
                    stderr('follow: forced to flush; linebuf="%s"' % linebuf)
                    yield linebuf
                    linebuf = ""
            elif newfstat.st_size < curfile.tell():
                stderr('follow: file shrunk; re-opening')
                curfile,curfstat = newfile, newfstat
                # since, from buffering point of view, shrinking/trancating is
                # the same as reaching eof, flush any buffered data
                if linebuf:
                    stderr('follow: forced to flush; linebuf="%s"' % linebuf)
                    yield linebuf
                    linebuf = ""
            # newfile same as curfile; just clean up and wait
            else:
                newfile.close()
                time.sleep(sleep)
        else:
            # eof reached and we don't want to try again; flush buffers if any
            if linebuf:
                stderr('follow: forced to flush; linebuf="%s"' % linebuf)
                yield linebuf
            return

def main():
    parser = argparse.ArgumentParser(
            description="An implementation of tail -f as a Python module. "
                        "Follows file name, not file descriptor. "
                        "Able to handle file moves (rotations), deletions, "
                        "truncations. Buffers on newlines and strips them. ",
            epilog = "The design philosophy here is do roughly the right thing "
                        "while keeping the code simple. "
                        "Some content may be discarded during abnormal events "
                        "such as file rotations. ",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('file', metavar='PATH', nargs=1,
        help='File to follow')
    parser.add_argument('--sleep-time', metavar='SEC', type=float, default=1.0, 
        help="Sleep duration when waiting")
    parser.add_argument('--keep-trying', action='store_true', default=False,
        help="Keep retrying on EOF")
    parser.add_argument('--from-tail', action='store_true', default=False,
        help="Seek to the last newline or end of FILE before starting.")
    args = parser.parse_args()

    for l in follow(args.file[0], args.sleep_time, args.from_tail, args.keep_trying):
        print(l)

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)

