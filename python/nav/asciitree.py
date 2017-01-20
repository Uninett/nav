# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2014 Marc Brinkmann
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from __future__ import print_function

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


def draw_tree(node,
              child_iter=lambda n: n.children,
              text_str=lambda n: str(n)):
    return _draw_tree(node, '', child_iter, text_str)


def _draw_tree(node, prefix, child_iter, text_str):
    buf = StringIO()

    children = list(child_iter(node))

    # check if root node
    if prefix:
        buf.write(prefix[:-3])
        buf.write('  +--')
    buf.write(text_str(node))
    buf.write('\n')

    for index, child in enumerate(children):
        if index+1 == len(children):
            sub_prefix = prefix + '   '
        else:
            sub_prefix = prefix + '  |'

        buf.write(
            _draw_tree(child, sub_prefix, child_iter, text_str)
        )

    return buf.getvalue()


if __name__ == '__main__':
    class Node(object):
        def __init__(self, name, children):
            self.name = name
            self.children = children

        def __str__(self):
            return self.name

    root = Node('root', [
        Node('sub1', []),
        Node('sub2', [
            Node('sub2sub1', [])
        ]),
        Node('sub3', [
            Node('sub3sub1', [
                Node('sub3sub1sub1', [])
            ]),
            Node('sub3sub2', [])
        ])
    ])

    print(draw_tree(root))
