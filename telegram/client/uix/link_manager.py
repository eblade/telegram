#!/usr/bin/env python3

""" Link Manager for teh tkInter Text Box """

from tkinter import CURRENT

class LinkManager(object):
    def __init__(self, text):
        self.text = text
        self.text.tag_config('link', foreground="white", background="blue")

        self.text.tag_bind('link', '<Enter>', self._enter)
        self.text.tag_bind('link', '<Leave>', self._leave)
        self.text.tag_bind('link', '<Button-1>', self._click)

        self.reset()

    def reset(self):
        self.links = {}

    def add(self, action, *args):
        tag = 'link-%i' % len(self.links)
        self.links[tag] = action, args
        return 'link', tag

    def _enter(self, event):
        self.text.config(cursor='hand2')

    def _leave(self, event):
        self.text.config(cursor='')

    def _click(self, event):
        for tag in self.text.tag_names(CURRENT):
            if tag[:5] == 'link-':
                f, args = self.links[tag]
                f(*args)
                return
