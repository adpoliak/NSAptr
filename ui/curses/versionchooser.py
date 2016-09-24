"""
Copyright 2016 adpoliak

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
from distutils.version import LooseVersion
import curses
import os
import sys
import typing


class VersionItem(object):
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name


class VersionChoiceDialog(object):
    @property
    def chosen_version(self):
        return self._chosen_version

    @property
    def do_not_ask_again(self):
        return self._do_not_ask_again

    @do_not_ask_again.setter
    def do_not_ask_again(self, value: bool):
        self._do_not_ask_again = value

    @property
    def keep_while_available(self):
        return self._keep_while_available

    @keep_while_available.setter
    def keep_while_available(self, value: bool):
        self._keep_while_available = value

    @property
    def persist(self):
        return self._persist

    @persist.setter
    def persist(self, value: bool):
        self._persist = value

    @property
    def return_code(self):
        return self._return_code

    @return_code.setter
    def return_code(self, value: str):
        self._return_code = value

    def persist_action(self):
        if self.persist is not None:
            self.persist ^= True
            if self.persist:
                self.keep_while_available = False
                self.do_not_ask_again = False
            else:
                self.keep_while_available = None
                self.do_not_ask_again = None

    def update_persist_state(self):
        if self.keep_while_available or self.do_not_ask_again:
            self.persist = None
        else:
            self.persist = False

    def keep_action(self):
        if self.keep_while_available is not None:
            self.keep_while_available ^= True
            self.update_persist_state()

    def noprompt_action(self):
        if self.do_not_ask_again is not None:
            self.do_not_ask_again ^= True

    def select_action(self):
        self.chosen_version = list(self._child_names)[self._index]
        if self.chosen_version.endswith(':KEEP'):
            self._can_continue = False
            self.persist = None
            self.keep_while_available = None
            self.do_not_ask_again = None
        else:
            self._can_continue = True
            self.persist = False
            self.persist = False
            self.do_not_ask_again = False

    def cancel_action(self):
        self.return_code = 'cancel'

    def accept_action(self):
        if self._can_continue:
            self.return_code = 'accept'

    def __init__(self, master: typing.Optional[object], versions: typing.Set[LooseVersion],
                 persist: typing.Optional[bool] = False, keep: typing.Optional[bool] = False,
                 last_used: typing.Optional[str] = None, *args, **kwargs):

        # assign tkinter-compatible interface items to placeholder to placate PyCharm
        _ = master
        _ = args
        _ = kwargs
        self._can_continue = None
        self._child_names = set(versions)
        self._child_objects = None
        self._chosen_version = None
        self._do_not_ask_again = False
        self._keep_while_available = keep
        self._last_used = last_used
        self._return_code = None
        self._persist = persist
        self._index = 0

        if persist:
            self.persist_action()
        if keep:
            self.keep_action()
        if last_used is not None:
            last_used_version_object = LooseVersion(last_used)
            self._index = list(self._child_names).index(last_used_version_object) \
                if last_used_version_object in self._child_names else 0
            self.select_action()
