# -*- coding: utf-8 -*-

import yaml


class _ConfigDict(object):
    def __init__(self):
        self.set_items({})

    def clear(self):
        self.set_items({})

    def items(self):
        return self._items

    def set_items(self, items):
        object.__setattr__(self, '_items', items)

    def append_items(self, items):
        for i in items:
            setattr(self, i, items[i])

    def __getattr__(self, name):
        if name not in self._items:
            raise AttributeError('No "{0}" config option.'.format(name))
        else:
            return self._items[name]

    def __getitem__(self, key):
        if key not in self._items:
            raise KeyError('No "{0}" config option.'.format(key))
        else:
            return self._items[key]

    def get(self, name, default=None):
        return self._items.get(name, default)

    def __iter__(self):
        return self._items.__iter__()

    def next(self):
        return self._items.next()

    def __setattr__(self, name, value):
        self._items[name] = value

    def __setitem__(self, key, value):
        self._items[key] = value


config = _ConfigDict()


def init_config(inp):
    if isinstance(inp, str):
        with open(inp) as f:
            items = yaml.load(f)
            config.set_items(items)
    elif isinstance(inp, dict):
        config.set_items(inp)


def append_config(path):
    with open(path) as f:
        items = yaml.load(f)
        config.append_items(items)