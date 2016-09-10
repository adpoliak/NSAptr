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
import tkinter as tk
import tkinter.ttk
import typing
from distutils.version import LooseVersion


class VersionChoiceDialog(tk.Toplevel):
    KEEP = True
    UPGRADE = False

    def accept_callback(self, event=None):
        _ = event
        self.return_code = 'accept'
        self.destroy()
        self.keep_while_available = self.keep_while_available.get()
        self.persist = self.persist.get()
        self.do_not_ask_again = self.do_not_ask_again.get()

    def cancel_callback(self, event=None):
        _ = event
        self.return_code = 'cancel'
        self.destroy()

    def update_persist_state(self):
        if self.keep_while_available.get() == self.KEEP or self.do_not_ask_again.get():
            self._persist_changes.config(state=tk.DISABLED)
        else:
            self._persist_changes.config(state=tk.NORMAL)
        self.update_idletasks()

    def keep_callback(self, event=None):
        _ = event
        self.update_persist_state()

    def noprompt_callback(self, event=None):
        _ = event
        if self.do_not_ask_again.get():
            self._version_chooser.config(state=tk.DISABLED)
            self._version_chooser.set('Always Install Greatest Version Available')
        else:
            self._version_chooser.config(state=tk.NORMAL)
            self._version_chooser.set(self.chosen_version)
        self.update_persist_state()

    def persist_callback(self, event=None):
        _ = event
        if self.persist.get():
            self._keep_while_available.config(state=tk.NORMAL)
            self._dont_ask_again.config(state=tk.NORMAL)
        else:
            self.keep_while_available.set(self.UPGRADE)
            self.do_not_ask_again.set(False)
            self._keep_while_available.config(state=tk.DISABLED)
            self._dont_ask_again.config(state=tk.DISABLED)
        self.update_idletasks()

    def combo_callback(self, event=None):
        _ = event
        self.chosen_version = self._version_chooser.get()
        if self.chosen_version.endswith(':KEEP'):
            self._accept_button.config(state=tk.DISABLED)
            self.persist.set(False)
            self.keep_while_available.set(self.UPGRADE)
            self.do_not_ask_again.set(False)
            self._keep_while_available.config(state=tk.DISABLED)
            self._persist_changes.config(state=tk.DISABLED)
            self._dont_ask_again.config(state=tk.DISABLED)
        else:
            self._accept_button.config(state=tk.NORMAL)
            self._persist_changes.config(state=tk.NORMAL)
        self.update_idletasks()

    def __init__(self, master, versions: typing.List[LooseVersion], persist: typing.Optional[bool] = False,
                 keep: typing.Optional[bool] = False, last_used: typing.Optional[str] = None, *args, **kwargs):
        tk.Toplevel.__init__(self, master, *args, **kwargs)
        self.grid()
        for col in range(2):
            self.columnconfigure(col, weight=1)
        for row in range(3):
            self.rowconfigure(row, weight=1)
        self.rowconfigure(3, weight=0)
        self.transient(master)
        self.master = master
        self.protocol('WM_DELETE_WINDOW', self.cancel_callback)
        self.bind("<Escape>", self.cancel_callback)
        self.bind("<Return>", self.accept_callback)
        self.title('Choose Version')
        self.return_code = None
        self.chosen_version = None
        self.persist = tk.BooleanVar()
        self.persist.set(persist)
        self.do_not_ask_again = tk.BooleanVar()
        self.do_not_ask_again.set(False)
        self.keep_while_available = tk.BooleanVar()  # self.KEEP or self.UPGRADE or None
        self.keep_while_available.set(keep)
        self._version_chooser = tk.ttk.Combobox(self, justify=tk.LEFT, state='readonly', values=versions,
                                                takefocus=True)
        self._version_chooser.bind('<<ComboboxSelected>>', self.combo_callback)
        self._version_chooser.grid(column=0, row=0, columnspan=2, padx=1, pady=1, ipadx=1, ipady=1,
                                   sticky=tk.N + tk.E + tk.W + tk.S)
        self._initial_focus = self._version_chooser
        self._persist_changes = tk.ttk.Checkbutton(self, state=tk.DISABLED, takefocus=True, text='Persist Choices',
                                                   underline=1, variable=self.persist, onvalue=True, offvalue=False,
                                                   command=self.persist_callback)
        self._persist_changes.grid(column=0, row=1, padx=1, pady=1, ipadx=1, ipady=1, sticky=tk.N + tk.E + tk.W + tk.S)
        self._keep_while_available = tk.ttk.Checkbutton(self, state=tk.DISABLED, takefocus=True,
                                                        text='Keep While Available', underline=1,
                                                        variable=self.keep_while_available, onvalue=self.KEEP,
                                                        offvalue=self.UPGRADE, command=self.keep_callback)
        self._keep_while_available.grid(column=1, row=1, padx=1, pady=1, ipadx=1, ipady=1,
                                        sticky=tk.N + tk.E + tk.W + tk.S)
        self._dont_ask_again = tk.ttk.Checkbutton(self, state=tk.DISABLED, takefocus=True, text='Don\'t Prompt Again',
                                                  underline=0, variable=self.do_not_ask_again, onvalue=True,
                                                  offvalue=False, command=self.noprompt_callback)
        self._dont_ask_again.grid(column=0, row=2, columnspan=2, padx=1, pady=1, ipadx=1, ipady=1,
                                  sticky=tk.N + tk.E + tk.W + tk.S)
        self._cancel_button = tk.ttk.Button(self, command=self.cancel_callback, takefocus=True,
                                            default=tk.ACTIVE, text='Cancel',
                                            underline=1)
        self._cancel_button.grid(column=0, row=3, padx=1, pady=1, ipadx=1, ipady=1,
                                 sticky=tk.N + tk.E + tk.W + tk.S)
        self._accept_button = tk.ttk.Button(self, command=self.accept_callback, takefocus=True, default=tk.ACTIVE,
                                            text='Continue', underline=1, state=tk.DISABLED)
        self._accept_button.grid(column=1, row=3, padx=1, pady=1, ipadx=1, ipady=1,
                                 sticky=tk.N + tk.E + tk.W + tk.S)
        if persist:
            self.persist_callback()
        if keep:
            self.keep_callback()
        if last_used is not None:
            self._version_chooser.set(last_used)
            self.combo_callback()
        else:
            self._version_chooser.set('Choose Version...')
        self.grab_set()
        if not self._initial_focus:
            self._initial_focus = self
        self._initial_focus.focus_set()
        self.wait_window(self)
