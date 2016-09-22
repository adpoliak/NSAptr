"""
Originally from https://gist.github.com/rygwdn/394885

Yet another curses-based directory tree browser, in Python.

I thought I could use something like this for filename entry, kind of
like the old 4DOS 'select' command --- cd $(cursoutline.py).  So you
navigate and hit Enter, and it exits and spits out the file you're on.

Originally from: http://lists.canonical.org/pipermail/kragen-hacks/2005-December/000424.html
Originally by: Kragen Sitaker

"""
# There are several general approaches to the drawing-an-outline
# problem.  This program supports the following operations:
# - move cursor to previous item (in preorder traversal)
# - move cursor to next item (likewise)
# - hide descendants
# - reveal children
# And because it runs over the filesystem, it must be at least somewhat lazy
# about expanding children.
# And it doesn't really bother to worry about someone else changing the outline
# behind its back.
# So the strategy is to store our current linear position in the
# in-order traversal, and defer operations on the current node until the next
# time we're traversing.

import cgitb
import curses
import os
import sys

cgitb.enable(format="text")
ESC = 27


class Dir(object):
    def __init__(self, name):
        self.name = name
        # noinspection PyBroadException
        try:
            self.child_names = sorted(os.listdir(name))
        except:
            self.child_names = None  # probably permission denied
        self.kids = None
        self.expanded = False

    @staticmethod
    def _pad(data, width):
        # XXX this won't work with UTF-8
        return data + ' ' * (width - len(data))

    def children(self):
        if self.child_names is None:
            return []
        if self.kids is None:
            self.kids = [Dir(os.path.join(self.name, kid))
                         for kid in self.child_names if os.path.isdir(os.path.join(self.name, kid))]
        return self.kids

    def icon(self):
        if self.expanded:
            return '[-]'
        elif self.child_names is None:
            return '[?]'
        elif self.children():
            return '[+]'
        else:
            return '[ ]'

    def expand(self):
        self.expanded = True

    def collapse(self):
        self.expanded = False

    def traverse(self):
        yield self, 0
        if not self.expanded:
            return
        for child in self.children():
            for kid, depth in child.traverse():
                yield kid, depth + 1

    def render(self, depth, width):
        return self._pad('%s%s %s' % (' ' * 4 * depth, self.icon(),
                                      os.path.basename(self.name)), width)


def __askdirectory_main(screen, initialdir, title, mustexist=True):
    # TODO: Implement Directory Creation for mustexist=False
    # TODO: Implement Location Entry box with autocomplete for direct entry
    if not mustexist:
        raise NotImplementedError('Directory Creation Functionality Not Available.')

    screen.clear()
    screen.refresh()
    curses.nl()
    curses.noecho()
    screen.timeout(0)
    screen.nodelay(0)
    directory_object = Dir(initialdir)
    directory_object.expand()
    current_index = 2
    pending_action = None
    pending_save = False
    pending_root_change = False

    while 1:
        screen.clear()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
        screen.attrset(curses.color_pair(0))
        screen.addstr(0, 0, title)
        screen.addstr(1, 0, ('Press BACKSPACE to go up on the Directory Tree. '
                             'Press DELETE to set new Directory Tree Root'))
        line = 2
        offset = max(0, current_index - curses.LINES + 3)
        for data, depth in directory_object.traverse():
            if line == current_index:
                screen.attrset(curses.color_pair(1) | curses.A_BOLD)
                if pending_action:
                    getattr(data, pending_action)()
                    pending_action = None
                elif pending_root_change:
                    initialdir = os.path.abspath(data.name)
                    directory_object = Dir(initialdir)
                    directory_object.expand()
                    current_index = 2
                    break
                elif pending_save:
                    return data.name
            else:
                screen.attrset(curses.color_pair(0))
            if 0 <= line - offset < curses.LINES - 1:
                screen.addstr(line - offset, 0,
                              data.render(depth, curses.COLS))
            line += 1
        if pending_root_change:
            pending_root_change = False
            continue
        screen.refresh()
        ch = screen.getch()
        if ch == curses.KEY_UP:
            current_index -= 1
        elif ch == curses.KEY_DOWN:
            current_index += 1
        elif ch == curses.KEY_PPAGE:
            current_index -= curses.LINES
            if current_index < 2:
                current_index = 2
        elif ch == curses.KEY_NPAGE:
            current_index += curses.LINES
            if current_index >= line:
                current_index = line - 1
        elif ch == curses.KEY_RIGHT:
            pending_action = 'expand'
        elif ch == curses.KEY_LEFT:
            pending_action = 'collapse'
        elif ch == curses.KEY_BACKSPACE or ch == 127:
            initialdir = os.path.abspath(os.path.join(initialdir, '..'))
            directory_object = Dir(initialdir)
            directory_object.expand()
            current_index = 2
        elif ch == curses.KEY_DC:
            pending_root_change = True
        elif ch == ESC or ch == ord('q') or ch == ord('Q'):
            return None
        elif ch == ord('\n'):
            pending_save = True
        current_index %= line
        if current_index < 2:
            current_index = 2


def __open_tty():
    saved_stdin = os.dup(0)
    saved_stdout = os.dup(1)
    saved_sys_stdin = sys.stdin
    saved_sys_stdout = sys.stdout
    os.close(0)
    os.close(1)
    sys.stdin = os.open('/dev/tty', os.O_RDONLY)
    sys.stdout = os.open('/dev/tty', os.O_RDWR)
    return saved_stdin, saved_stdout, saved_sys_stdin, saved_sys_stdout


def __restore_stdio(saved_stdin, saved_stdout, saved_sys_stdin, saved_sys_stdout):
    os.dup(saved_stdin)
    os.dup(saved_stdout)
    sys.stdin = saved_sys_stdin
    sys.stdout = saved_sys_stdout


def askdirectory(**kwargs):
    arguments = {
        'title': 'Choose Directory',
        'initialdir': os.getcwd(),
        'mustexist': True,
    }
    arguments.update(kwargs)
    saved_fds = __open_tty()
    # noinspection PyBroadException
    try:
        result = curses.wrapper(__askdirectory_main, **arguments)
    finally:
        __restore_stdio(*saved_fds)
    return result

if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]) else os.path.sep
    ret = askdirectory(initialdir=start)
    print(ret)
