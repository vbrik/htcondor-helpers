#!/usr/bin/env python
"""ANSI terminal text color, formatting, etc."""
from __future__ import print_function
import os
import string
import sys
from pprint import pprint
from collections import namedtuple

"""
To send an xterm 256 color foreground color one must print "\e[38;5;#m" where # is a number between 0 and 255. For background colors one must print "\e[48;5;#m" where # behaves in the same manner as foreground colors. 

Curses-based implementation; supports more terminal capabilities
http://code.activestate.com/recipes/475116/
http://docs.python.org/howto/curses.html
alternative: http://nadiana.com/python-curses-terminal-controller
"""

termwidth = int(os.popen('tput cols', 'r').read())
termheight = int(os.popen('tput lines', 'r').read())

def columns(*args, **kwargs):
    sep = kwargs.get('sep') or ''
    border = bool(kwargs.get('border'))
    parts = []
    for width, text in zip(args[::2], args[1::2]):
        text = str(text)
        pad = ' ' * (abs(width) - len(nocolor(text)))
        if width > 0:
            parts.append(pad + text)
        else:
            parts.append(text + pad)
    if border:
        return sep + sep.join(parts) + sep
    else:
        return sep.join(parts) 

# convenience prefixes:
#       @  background
#       *  bold/bright
#       _  underline
#       /  italic
#       !  blinking
ansi = {
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

ATTRS = namedtuple('Text_attribute', 
    'reset bright dark italic underline blink blink_fast inverse concealed'
    )._make(range(9))
BG = namedtuple('Background_color',
    'gray red green yellow blue magenta cyan white'
    )._make(range(40, 48))
FG = namedtuple('Foreground_color',
    'gray red green yellow blue magenta cyan white'
    )._make(range(30, 38))
RESET = '\033[0m' #keep all codes the same length to simplify removal from string

def nocolor(text):
    """remove substrings that look like \033.*m"""
    if not text:
        return text
    parts = [s for s in text.split('\033')]
    first = parts.pop(0)
    parts = [s[(s.find('m')+1):] for s in parts]
    return first + ''.join(parts)
    
def _make_color_shortcut(fg, attrs):
    def _color_shortcut(text):
        return incolor(text, fg=fg, attrs=attrs)
    return _color_shortcut

red = _make_color_shortcut('red', 'dark')
crimson = _make_color_shortcut('red', 'bright')
green = _make_color_shortcut('green', 'dark')
lime = _make_color_shortcut('green', 'bright')
yellow = _make_color_shortcut('yellow', 'bright')
brown = _make_color_shortcut('yellow', 'dark')
blue = _make_color_shortcut('blue', 'dark')
sky = _make_color_shortcut('blue', 'bright') 
magenta = _make_color_shortcut('magenta', 'bright')
purple = _make_color_shortcut('magenta', 'dark')
cyan = _make_color_shortcut('cyan', 'bright')
teal = _make_color_shortcut('cyan', 'dark')
white = _make_color_shortcut('white', 'bright')
gray = _make_color_shortcut('white', 'dark')
dark = _make_color_shortcut('gray', 'bright')

def incolor(text, fg=None, bg=None, attrs=None, reset=True):
    text = str(text)
    if isinstance(attrs, str):
        attrs = [attrs]
    if os.getenv('ANSI_COLORS_DISABLED'):
        return text
    fmt_str = '\033[%dm%s'
    if fg:
        text = fmt_str % (FG._asdict()[fg], text)
    if bg:
        text = fmt_str % (BG._asdict()[bg], text)
    if attrs:
        for attr in attrs:
            text = fmt_str % (ATTRS._asdict()[attr], text)
    if text.endswith('\n'):
        return text[:-1] + RESET + '\n'
    else:
        return text + (RESET if reset else '')

def vga(text, color):
    """256-color text"""
    return '\033[38;5;%dm%s\033[0m' % (color, str(text))

if __name__ == '__main__':
    separator = '-' * 79
    print('Terminal type: ', os.getenv('TERM'))
    print(separator)

    print('Testing text attributes:')
    for attr in ATTRS._fields:
        print('    %s:\t' % attr,
            incolor('This is attribute %s' % attr, attrs=[attr]))

    print('Testing background colors:')
    for color in BG._fields:
        print('    %s:\t' % color,
            incolor('This is background color %s' % color, bg=color))
    print(separator)

    print('Testing foreground colors:')
    for color in FG._fields:
        for attr in ['bright', 'dark']:
            print('    %s (%s): \t' % (color, attr),
                incolor('This is foreground color %s(%s)' % (color, attr),fg=color, attrs=attr))
    print(separator)

    print('Testing 8-bit colors:')
    for i in range(16):
        print('\033[38;5;%dm%02x ' % (i,i), end='')
    print()
    strings = ['\033[38;5;%dm%02x ' % (i,i) for i in range(16, 256)]
    for i in range(len(strings)):
        print(strings[i], end='')
        if (i+1) % 24 == 0:
            print()


