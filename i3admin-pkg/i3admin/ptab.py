#!/usr/bin/env python
"""Pretty Tables"""
from __future__ import division
from __future__ import print_function
import argparse
import re
import string
import sys
from collections import OrderedDict
from pprint import pprint

ansi = {
    'nop':'', #noop
    'def':'\033[39m', #default
    'rst':'\033[0m', # reset
    'inv':'\033[7m', # inverse
    # foregrounds
    'blk':'\033[30m','blu':'\033[34m','cyn':'\033[36m','grn':'\033[32m',
    'pur':'\033[35m','red':'\033[31m','wht':'\033[37m','ylw':'\033[33m',
    # backgrounds
    '@blk':'\033[40m','@blu':'\033[44m','@cyn':'\033[46m','@grn':'\033[42m',
    '@pur':'\033[45m','@red':'\033[41m','@wht':'\033[47m','@ylw':'\033[43m',
    # bold
    'bld':'\033[1m',
    '*blk':'\033[1;30m', '*blu':'\033[1;34m', '*cyn':'\033[1;36m', '*grn':'\033[1;32m',
    '*pur':'\033[1;35m', '*red':'\033[1;31m', '*wht':'\033[1;37m', '*ylw':'\033[1;33m',
    # underlined
    'und':'\033[4m',
    '_blk':'\033[4;30m','_blu':'\033[4;34m','_cyn':'\033[4;36m','_grn':'\033[4;32m',
    '_pur':'\033[4;35m','_red':'\033[4;31m','_wht':'\033[4;37m','_ylw':'\033[4;33m',
    # italic
    'itl':'\033[3m',
    '/blk':'\033[3;30m','/blu':'\033[3;34m','/cyn':'\033[3;36m','/grn':'\033[3;32m',
    '/pur':'\033[3;35m','/red':'\033[3;31m','/wht':'\033[3;37m','/ylw':'\033[3;33m',
    # blinking
    'bli':'\033[5m',
    '!blk':'\033[5;30m','!blu':'\033[5;34m','!cyn':'\033[5;36m','!grn':'\033[5;32m',
    '!pur':'\033[5;35m','!red':'\033[5;31m','!wht':'\033[5;37m','!ylw':'\033[5;33m',
}

def ptab_disable_color():
    for k in ansi:
        ansi[k] = ''

ansi_escape = re.compile(r'\x1b[^m]*m')

# remove ANSI escapes
def raw_string(s):
    return ansi_escape.sub('', s)

class Cell(object):
    def __init__(self, title, width=0, align='l', style='def', adapter=str, empty='', descr=None):
        self.title = title
        self.width = width
        self.align = align
        self.style = style
        self.adapter = adapter
        self.empty = empty
        self.value = empty
        self.descr = descr

    def __str__(self):
        return '<Cell(%s)=%r>' % (
                    ','.join(map(repr, [self.title, self.width, self.align, 
                        self.style, self.adapter, self.empty])),
                    self.value)

    def reset(self):
        self.value = self.empty

    def set(self, v):
        self.value = v

    def render(self, content=None, adapt=True):
        content = self.value if content is None else content
        if adapt:
            content = self.adapter(content)
        charcnt = len(raw_string(content))
        surplus = (self.width - charcnt if self.width else 0)
        if self.align == 'c':
            bow = ' ' * (surplus//2)
            aft = ' ' * (surplus - len(bow))
        elif self.align == 'l':
            bow = ''
            aft = ' ' * surplus
        elif self.align == 'r':
            aft = ''
            bow = ' ' * surplus
        else:
            raise Exception('Invalid alignment code: %s' % self.align)
        return ansi[self.style] + bow + content + aft


class CellBlock(object):
    def __init__(self, cells, sep=" ", rubric_spans={}, descr=None):
        self.cells = OrderedDict(cells)
        assert len(cells) == len(self.cells), "Duplicate cell names"
        self.sep = sep
        self.descr = descr
        self.rubric_spans = []
        cell_enum = list(enumerate(self.cells.values()))
        for rubric, members in rubric_spans.items():
            try:
                indexes = set(self.cells.keys().index(title) for title in members)
            except ValueError:
                missing = set.difference(set(members), set(self.cells.keys()))
                raise Exception("Rubric members not found: %s" % list(missing))
            left = min(indexes)
            right = max(indexes)
            offset = sum((c.width or len(c.title)) for i, c in cell_enum if i < left)
            offset += max(0, len(self.sep) * (left - 1))
            width = sum(c.width for i, c in cell_enum if left <= i <= right)
            width += len(self.sep) * (right - left)
            self.rubric_spans.append((offset, width, rubric))
        self.rubric_spans.sort()

    def __setitem__(self, cell, val):
        self.set(cell, val)

    def set(self, cell, val):
        self.cells[cell].set(val)

    def reset(self, cell=None):
        if cell is None:
            [c.reset() for c in self.cells.values()]
        else:
            self.cells[cell].reset()

    def render(self, style='nop'):
        return self.sep.join((c.render() + ansi['rst']) for c in self.cells.values())

    def title(self, style='und'):
        rubric_line = ""
        for offset, width, rubric in self.rubric_spans:
            rubric_line += ' ' * (offset - len(rubric_line))
            rubric_line += (self.sep if len(rubric_line) else '')
            rubric_line += string.center(rubric, width, '-')
        if rubric_line:
            print(ansi['*blk'] + rubric_line)
        titles = []
        for c in self.cells.values():
            if c.title:
                t = c.render(c.title, adapt=False) 
                titles.append(ansi[style] + ansi[c.style] + t + ansi['rst'])
            else:
                titles.append(c.render())
        return self.sep.join(titles)

    def legend(self):
        longest_title = max(len(c.title) for c in self.cells.values())
        fmt = '  %%%ss -- %%s' % longest_title
        if longest_title and self.descr:
            print('%s:' % self.descr)
        for c in self.cells.values():
            if c.title and c.descr:
                print(fmt % (c.title, c.descr))

def main():
    parser = argparse.ArgumentParser(
            description="",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('args', nargs='*')
    args = parser.parse_args()
    
    sep = Cell("", width=3, align='c', empty="|")

    block = CellBlock(cells=(
                ('foo', Cell("Foo", width=4, align="c", style='red', empty="?",
                                descr='descr foo')),
                ('s1',  sep),
                ('bar', Cell("Bar", width=5, align="r", style='inv', empty="x",
                                descr='descr bar')),
                ('s2',  sep),
                ('qux', Cell("Qux", width=3, align="l", style='def', empty="n/a")),
                ('xxx', Cell("XXX", width=3, align="l", style='def', empty="n/a")),
                ('asf', Cell("ASFASF", width=6, align="l", style='def', empty="n/a",
                                descr='descr asf')),
            ),
            sep=' ',
            rubric_spans={'rub1': ['bar', 'qux'], 'rub2':['xxx', 'asf']},
            descr='block',
    )
    block.set('foo', "foo")
    block.set('bar', 1)

    print(block.title())
    print(block.render())
    block.reset()
    print(block.render(style='@red'))
    block.legend()
    


if __name__ == '__main__':
    sys.exit(main())

