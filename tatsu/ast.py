# -*- coding: utf-8 -*-
"""
Define the AST class, a direct descendant of dict that's used during parsing
to store the values of named elements of grammar rules.
"""
from __future__ import generator_stop
from collections.abc import Mapping

from tatsu.util import asjson, is_list


class AST(dict):
    _frozen = False

    def __init__(self, *args, **kwargs):
        super().__init__()

        self.update(*args, **kwargs)
        self._frozen = True

    def set_parseinfo(self, value):
        self._set('parseinfo', value)

    def asjson(self):
        return asjson(self)

    def update(self, *args, **kwargs):
        def upairs(d):
            for k, v in d:
                self[k] = v

        for d in args:
            if isinstance(d, Mapping):
                upairs(d.items())
            else:
                upairs(d)
        upairs(kwargs.items())

    def _set(self, key, value, force_list=False):
        key = self._safekey(key)

        previous = self.get(key)
        if previous is None:
            if force_list:
                super().__setitem__(key, [value])
            else:
                super().__setitem__(key, value)
        elif is_list(previous):
            previous.append(value)
        else:
            super().__setitem__(key, [previous, value])
        return self

    def _setlist(self, key, value):
        return self._set(key, value, force_list=True)

    def __copy__(self):
        return AST(
            (k, v[:] if is_list(v) else v)
            for k, v in self.items()
        )

    def copy(self):
        return self.__copy__()

    def __getitem__(self, key):
        if key in self:
            return super().__getitem__(key)
        key = self._safekey(key)
        if key in self:
            return super().__getitem__(key)

    def __setitem__(self, key, value):
        self._set(key, value)

    def __delitem__(self, key):
        key = self._safekey(key)
        super().__delitem__(key)

    def __setattr__(self, name, value):
        if self._frozen and name not in vars(self):
            raise AttributeError(
                '%s attributes are fixed. Cannot set attribute %s.'
                %
                (self.__class__.__name__, name)
            )
        super().__setattr__(name, value)

    def __getattr__(self, name):
        return self[name]

    def __hasattribute__(self, name):
        if not isinstance(name, str):
            return False
        try:
            super().__getattribute__(name)
            return True
        except AttributeError:
            return False

    def __reduce__(self):
        return (AST, (), None, None, iter(self.items()))

    def _safekey(self, key):
        while self.__hasattribute__(key):
            key += '_'
        return key

    def _define(self, keys, list_keys=None):
        # WARNING: This is the *only* implementation that does what's intended
        for key in list_keys or []:
            key = self._safekey(key)
            if key not in self:
                self[key] = []

        for key in keys:
            key = self._safekey(key)
            if key not in self:
                super().__setitem__(key, None)

    def __json__(self):
        return {
            asjson(k): asjson(v)
            for k, v in self.items() if not k.startswith('_')
        }

    def __repr__(self):
        return "%s(%s)" % (
            self.__class__.__name__,
            super().__repr__()
        )
