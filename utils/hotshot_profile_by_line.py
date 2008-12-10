#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Display per-line profile information from `hotshot`.

`hotshot` can record per-line profiling statistics, but the standard
`hotshot.stats` module only shows you per-function statistics, not
per-line statistics.

This program is likely to produce voluminous output, on the order of
the size of the program being profiled (minus comments, blank lines,
and lines that weren’t covered in the profiler run).

The output is formatted with several objectives in mind:

- it’s in a readable tabular format
- it has the most time-consuming lines at the top, so that you can
  pipe this program’s output to head(1) and usefully reduce the
  time it takes to run
- it shows the lines of source directly, so you don’t have to
  constantly refer back and forth between the profiler output and your
  source code
- it’s hypertext if you load it into Emacs, so that if you want to see
  your expensive source code lines in context, you can do it just by
  clicking the mouse on the line
- if you pipe it to sort(1) you get back a version of your program,
  annotated with execution counts and times in the left margin,
  omitting parts that didn’t run.  This works best if sort(1) is
  configured to sort things by ASCII code (e.g. `| LANG=C sort`)
  instead of e.g. English sort order.

These are in conflict to some extent.

BUGS
----

Because `hotshot` doesn’t record full paths to files, let alone their
contents, this program relies on `sys.path` (via `linecache`) to find
the contents of source files.  This means that if you run it on a
different machine or in a different version of Python than you ran the
profile in, or if you have edited the program since you ran the
profiler, the source code shown will be wonky.

`hotshot` has the option to record per-line profiling statistics, but
doesn’t do so by default.  You have to request it using the
`lineevents` flag when you instantiate a `hotshot.Profile`:

    >>> import hotshot
    >>> prof = hotshot.Profile('parse.fec_csv.prof', lineevents=True)
    >>> x = prof.runcall(whatever)
    >>> prof.close()

Reading `hotshot` profile log files is kind of slow.  On my machine it
takes about 4.5× as long to generate this profile data as to run the
original code to be profiled.

The output (and the source, and the documentation) is in UTF-8-encoded
Unicode.  Not everything defaults to UTF-8 yet; in particular `pydoc
-w` seems to still default to ISO-8859-1.

The Emacs hypertext works better with stuff in your current directory
than with stuff pulled in from Python libraries.

The output doesn’t sort correctly with sort(1) if you have modules
over 9999 lines.
"""

import sys, hotshot.log, cgitb, linecache, os

def display_profiling_information(filename):
    """Display `hotshot` per-line profiling information.

    We treat ENTER, EXIT, and LINE events as mostly equivalent; each
    just provides a time delta which gets charged to the specified
    line number.  I don’t know if that is correct with regard to
    `hotshot` output.

    Arguments:
    - `filename`: the filename to read the log from.
    """
    
    log = hotshot.log.LogReader(filename)
    time = {}
    n = {}

    for what, where, tdelta in log:
        time.setdefault(where, 0)
        time[where] += tdelta

        n.setdefault(where, 0)
        if what != hotshot.log.EXIT: n[where] += 1

    total = sum(time.values())

    here = os.getcwd()
    # leading space to get `LANG=C sort` to leave these at the top
    print '  -*- mode: grep; default-directory: "%s"; coding: utf-8 -*-' % here
    print " (output of proflines.py %s, formatted for emacs; %.3gs total)" % (
        filename, total * 1e-6)
    for where in sorted(time.keys(), key=time.get, reverse=True):
        filename, lineno, funcname = where
        line = linecache.getline(filename, lineno)
        header = '%s:%04d: (%s)' % (filename, lineno, funcname)
        seconds = time[where] * 1e-6
        try:
            percall = seconds / n[where]
        except ZeroDivisionError:
            percall = 0
        print "%s%s %8.3gs (%4d × %7.2g) %s"  % (header,
                                                 ' ' * max(0, 40 - len(header)),
                                                 seconds,
                                                 n[where],
                                                 percall,
                                                 line.rstrip())

def main(argv):
    """Display `hotshot` profiling information per line.
    
    Arguments:
    - `argv`: [inputfilename]
    """
    display_profiling_information(argv[1])

if __name__ == '__main__':
    cgitb.enable(format='text')
    main(sys.argv)
