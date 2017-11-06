#!/usr/bin/env python
from __future__ import division
from __future__ import print_function
import sys
import os
import time
from itertools import chain, izip, tee, islice, count, groupby
from operator import itemgetter, eq
from collections import defaultdict, OrderedDict
from contextlib import contextmanager

def bipart(seq, key=None, comp=None, arg=None):
    """binary partition of a sequence"""
    if key is None:
        key = lambda x: x
    elif not callable(key):
        key = itemgetter(key)
    if comp is None:
        comp = eq
    flags = [comp(key(e), arg) for e in seq]
    yep = [e for e,f in zip(seq, flags) if f]
    nope = [e for e,f in zip(seq, flags) if not f]
    return yep, nope


def alnumencode(num):
    """Encode number in English alphabet + digits (base62)"""
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"\
                + "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if (num == 0):
        return alphabet[0]
    isnegative = num < 0
    num = abs(num)
    arr = []
    base = len(alphabet)
    while num:
        rem = num % base
        num = num // base
        arr.append(alphabet[rem])
    arr.reverse()
    return ('-' if isnegative else '') + ''.join(arr) 

def alnumdecode(string):
    """Decode number from string encoded in English alphabet + numbers (base 62)"""
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"\
                + "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    base = len(alphabet)
    isnegative = string.startswith('-')
    string = string[1:] if isnegative else string
    strlen = len(string)
    num = 0
    idx = 0
    for char in string:
        power = (strlen - (idx + 1))
        num += alphabet.index(char) * (base ** power)
        idx += 1
    return num * (-1 if isnegative else 1)

def daemonize(target, *args, **kwargs):
    if os.fork() > 0:
        return
    else:
        os.setsid()
        if os.fork() > 0:
            sys.exit(0)
        else:
            sys.exit(target(*args, **kwargs))

def _indent(line, char=' '):
    """Length of indentation by character char"""
    if line.startswith(char):
        for k,g in groupby(line):
            return len(list(g))
    else:
        return 0

def _parse_indent_tree_test():
    data = ("a\n"
            "    aa\n"
            "    ab\n"
            "b\n"
            "    ba\n"
            "        baa\n"
            "    bb\n")
    root = parse_indent_tree(data.splitlines())
    print(root)

def parse_indent_tree(lines, tabstop=4):
    root = cur = Tree('__ROOT__')
    for l in lines:
        lvl = _indent(l)//tabstop + 1
        leaf = Tree(l.strip())
        if lvl <= cur.depth:
            while lvl < cur.depth:
                cur = cur.parent
            cur = cur.parent
        elif lvl > cur.depth:
            assert (lvl - cur.depth == 1), "Indentation error at: " + l
        cur.add(leaf)
        cur = leaf
    return root


class Tree(object):
    def __init__(self, obj):
        self.obj = obj
        self.children = []
        self.parent = self

    def add(self, tree):
        tree.parent = self
        self.children.append(tree)

    @property
    def depth(self):
        return len(self.parents)

    @property
    def parents(self):
        cur = self
        ret = []
        while not cur.isroot:
            ret.append(cur.parent)
            cur = cur.parent
        return ret

    @property
    def isroot(self):
        return self.parent == self

    def __repr__(self):
        tabstop = 4
        ret = ' ' * tabstop * (self.depth - 1)
        #ret = ' ' * tabstop * (self.depth - 1)
        #if not self.isroot:
        #    ret += '\033[01;30m' + '^' + ('-' * (tabstop - 1)) + '\033[00m'
        ret += str(self.obj)
        if self.children:
            ret += '\n' + '\n'.join(repr(c) for c in self.children)
        return ret

    def serialize(self):
        return [self] + flatten(c.serialize() for c in self.children)


def simple_xml_to_dict(parent_node):
    ''' Convert _simple_ XML to a Python dictionary. 
    - Assumes unique tags (bad: <list> <v>1</v> <v>2</v> </list>)
    - Ignores text of tags with attributes (bad: <t> attr=0 text</t>)
    Based on http://code.activestate.com/recipes/410469-xml-as-dictionary
    >>> import cElementTree as ElementTree
    >>> xml = ElementTree.parse('file.xml')
    >>> xmldict = xml_to_dict(xml.getroot())
    '''
    ret = {}
    if parent_node.attrib:
        ret.update(dict(parent_node.items()))
    for node in parent_node:
        if len(node): 
            ret.update({node.tag: xml_to_dict(node)})
        elif node.attrib:
            # ignores text of tags with attributes
            ret.update({node.tag: dict(node.items())})
        else:
            ret.update({node.tag: node.text})
    return ret

def xml_to_dict(xmlroot):
    ''' http://code.activestate.com/recipes/410469/
    Convert reasonable XML to dict. 
    Ignores text of tags with attributes
    >>> root = ElementTree.parse('your_file.xml').getroot()
    >>> # root = ElementTree.XML(xml_string)
    >>> xmldict = xml_to_dict(root)
    '''
    ret = {}
    if xmlroot.items():
        ret.update(dict(xmlroot.items()))
    for element in xmlroot:
        if element:
            # assume that if the first two tags in a series are different,
            # then they are all different. Otherwise, all are the same
            if len(element) == 1 or element[0].tag != element[1].tag:
                aDict = xml_to_dict(element)
            else:
                aDict = {element[0].tag: __xml_list(element)}
            if element.items():
                aDict.update(dict(element.items()))
            ret.update({element.tag: aDict})
        # this assumes tags with attributes have no text
        elif element.items():
            ret.update({element.tag: dict(element.items())})
        # if there are no child tags and no attributes, extract the text
        else:
            ret.update({element.tag: element.text})
    return ret

def __xml_list(aList):
    ret = []
    for element in aList:
        if element:
            # treat like dict
            if len(element) == 1 or element[0].tag != element[1].tag:
                ret.append(xml_to_dict(element))
            # treat like list
            elif element[0].tag == element[1].tag:
                ret.append(__xml_list(element))
        elif element.text:
            text = element.text.strip()
            if text:
                ret.append(text)
    return ret


@contextmanager
def tasklog(prolog, textwidth=50):
    """Pretty way to notify user what action is being performed and how long it took:
    >>> with tasklog("Running foo")
    >>>    foo()
    Running foo ...  done (0s)
    """
    print(prolog.ljust(textwidth), '...', end='')
    sys.stdout.flush()
    start_time = time.time()
    yield
    print('\tdone (%is)' % round(time.time() - start_time, 0))
    sys.stdout.flush()

def sgroupby(seq, key=None):
    """Sorted groupby: sort by key, then groupby key"""
    seq = sorted(seq, key=key)
    return [(k,list(g)) for k,g in groupby(seq, key=key)]

def mean(seq):
    return sum(seq)/len(seq)

def median(seq):
    seq = sorted(seq)
    return seq[len(seq)//2]

def readable(number, binary=False, precision=1, separator=''):
    """Make numbers more readable by using SI-like prefixes K, M, G, T, ..."""
    units = ('', 'K', 'M', 'G', 'T', 'P')
    if binary:
        scale = lambda exp: float(1024 ** exp)
    else:
        scale = lambda exp: float(1000 ** exp)
    for exp, unit in enumerate(units):
        if abs(number) < scale(exp + 1):
            break
    estimate = round(number/scale(exp), precision)
    if estimate == number or precision == 0:
        estimate = int(estimate)
    return '%s%s%s' % (estimate, separator, unit)

def uniq(func, *args, **kwargs):
    """Filter consequtive returns of func() to yield only distinct values"""
    prev = func(*args, **kwargs)
    yield prev
    while True:
        cur = func(*args, **kwargs)
        if cur != prev:
            yield cur
        prev = cur

class ToleranceExceeded(Exception): 
    pass

class Scheduler(object):
    def __init__(self, tolerance=0.01):
        self._period = None
        self._timelog = []
        self._tolerance = tolerance

    @property
    def dt(self):
        return self._timelog[-1] - self._timelog[-2]

    @property
    def toterr(self):
        last_act = self._timelog[-1] - self._timelog[0]
        last_exp = (len(self._timelog)-1) * self._period
        return last_act - last_exp

    @property
    def wait(self):
        try:
            elapsed = time.time() - self._timelog[-1]
            return self._period - elapsed - self.toterr
        except IndexError:
            return 0

    @property
    def err(self):
        return abs(self.dt - self._period) / self._period 

    def run(self, rate, func, count=float('inf'), args=(), kwargs=None):
        kwargs = kwargs or {}
        self._period = 1/float(rate)
        self._timelog = []
        while True:
            try:
                time.sleep(self.wait)
            except IOError:
                break
            self._timelog.append(time.time())
            yield func(*args, **kwargs)
            if len(self._timelog) >= count:
                return

    def report(self, rate, func, count=float('inf'), args=(), kwargs=None):
        kwargs = kwargs or {}
        self._period = 1/float(rate)
        self._timelog = [time.time()]
        while True:
            hist = []
            while self.wait > 0:
                hist.append(func(*args, **kwargs))
            self._timelog.append(time.time())
            if self.err > self._tolerance:
                raise ToleranceExceeded(self.err)
            yield hist
            if len(self._timelog) -1 >= count:
                return

    @classmethod
    def self_test(cls):
        print('"Run every" mode test:')
        cnt = count()
        sched = cls()
        err = []
        for v in sched.run(10, cnt.next):
            err.append(sched.toterr)
            if v > 10:
                print('\t', len(err), sum(err)/float(len(err)), max(err))
                break

        print('"Run between" mode test')
        cnt = count()
        sched = cls()
        for v in sched.report(10, cnt.next):
            print('\t', len(v), sched.toterr)
            break

def take(n, iterable):
    "Return first n items of the iterable as a list"
    return list(islice(iterable, n))

def delta(seq):
    """Return differences between adjacent elements"""
    head, tail = tee(seq[:])
    head.next()
    return [h-t for h,t in zip(head, tail)]

def getch():
    """getch analog for Linux"""
    import tty, termios
    ret = None
    fd = sys.stdin.fileno()
    saved_attrs = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ret = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved_attrs)
    return ret

class NonBlockingConsole(object):
    """ with NonBlockingConsole() as nbc:
            while True:
                ch = nbc.get_data()
                if ch:
                    print(ch)
                if ch == '\x1b': # ESC
                    break
    """
    def __enter__(self):
        import termios
        import tty
        self.old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        return self

    def __exit__(self, type, value, traceback):
        import termios
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

    def get_data(self):
        import select
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            return sys.stdin.read(1)
        return False

class recursivedefaultdict(defaultdict):
    def __init__(self):
        self.default_factory = type(self) 

def groupsof(n, seq, **kwargs):
    if 'pad' in kwargs:
        return izip(*[chain(s, [kwargs['pad']]*(n-1))]*n)
    else:
        return izip(*[iter(seq)]*n)

def shear(seq, shear_point=1):
    left=[s[:shear_point] for s in seq]
    right=[s[shear_point:] for s in seq]
    return left, right

def peephole(seq, length=2):
    """peephole('01234') -> [('0', '1'), ('1', '2'), ('2', '3'), ('3', '4')]"""
    assert len(seq) >= length
    offsets = tee(seq, length)
    [next(it) for n,it in enumerate(offsets) for j in range(n)]
    return izip(*offsets)

def cut(seq, *cutpoints):
    for p0,p1 in peephole((0,) + cutpoints + (None,)):
        yield list(seq)

def flatten(listOfLists):
    return list(chain(*listOfLists))

def getdimension(seq, dimension):
    """get items from sequence of specified dimension"""
    return map(itemgetter(dimension), seq)

def quick_prop(func):
    """http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/205183
    class MyClass(object):
        @quick_prop
        def foo():
            doc = "property foo's doc string"
            def fget(self): return self._foo # skip fset, fdel if read-only
            def fset(self, value): self._foo = value
            def fdel(self): del self._foo
               return locals()
        #which is equivalent to:
        #foo = property(**foo())"""
    return property(doc=func.__doc__, **func())

def least_sq_line(xs, ys):
    n = len(xs)
    sumx = sum(xs)
    sumy = sum(ys)
    sumxy = sum(x*y for x,y in zip(xs,ys))
    sumxx = sum(x*x for x in xs)
    slope = (n*sumxy - sumy*sumx)/(n*sumxx - sumx**2)
    intercept = (sumy - slope*sumx)/n
    return slope, intercept

def expandpaths(*paths):
    """sorted names of regular files in paths union files of trees of 
    directories in paths"""
    filenames = []
    for p in paths:
        if os.path.isdir(p):
            filenames.extend(walkpath(p))
        else:
            filenames.append(p)
    return list(sorted(set(filenames)))

def walkpath(path):
    """names of regular files in tree rooted at path"""
    filelist = []
    for root, dirs, files in os.walk(path):
        filelist.extend(os.path.join(root, f) for f in files)
    return filelist

def dup_files(filelist, size=-1):
    """find files in filelist with identical content of first <size> bytes"""
    _content_ = itemgetter(0)
    _file_ = itemgetter(1)
    fcontents = sorted( (f.read(size), f.name) for f in imap(open, filelist))
    dupfiles = [ list(g) for k,g in groupby(fcontents, _content_)]
    dupfiles = ( map(_file_, g) for g in dupfiles if len(g) > 1)
    return dupfiles

def profile_main(stat_lines=18):
    import cProfile, pstats
    from term import incolor
    sys.stderr.write(incolor('PROFILING', 'cyan', 'red', 'blink'))
    sys.stderr.write('\n')
    sys.stderr.flush()
    profname = sys.argv[0] + '.prof'
    cProfile.run('main()', profname)
    pstats.Stats(profname).strip_dirs().sort_stats('time').print_stats(stat_lines)

def send_email(subject, body, to, sender=None, cc=[], server="mail"):
    import email.mime.text, smtplib, socket, time
    to = ([to] if isinstance(to, str) else to)
    cc = ([cc] if isinstance(cc, str) else cc)
    msg = email.mime.text.MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = (sender or "noreply@" + socket.gethostname())
    msg['To'] = ', '.join(to)
    if cc:
        msg['Cc'] = ', '.join(cc)
        to.extend(cc)
    msg['Date'] = time.ctime()
    s = smtplib.SMTP(server)
    s.sendmail(sender, to, msg.as_string())
    s.quit()

def main():
    pass

if __name__ == '__main__':
    main()
