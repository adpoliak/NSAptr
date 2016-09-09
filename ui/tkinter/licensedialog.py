"""
NSAptr - a Non-Sketchy Android Platform Tools Retriever
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


class LicenseDialog(tk.Toplevel):
    def accept_callback(self, event=None):
        _ = event
        self.return_code = 'accept'
        self.destroy()

    def cancel_callback(self, event=None):
        _ = event
        self.return_code = 'cancel'
        self.destroy()

    def __init__(self, master, license_heading, license_body, *args, **kwargs):
        tk.Toplevel.__init__(self, master, *args, **kwargs)
        self.minsize(640, 480)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)
        self.columnconfigure(4, weight=0)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.transient(master)
        self.master = master
        self.protocol('WM_DELETE_WINDOW', self.cancel_callback)
        self.bind("<Escape>", self.cancel_callback)
        self.title('License Agreement')
        self.return_code = None
        self.grid()
        self._license_text = tk.Text(self, padx=1, pady=1, state=tk.NORMAL, takefocus=True, wrap=tk.WORD)
        self._license_text.grid(column=0, row=0, columnspan=4, padx=1, pady=1, ipadx=1, ipady=1,
                                sticky=tk.N + tk.E + tk.W + tk.S)
        self._license_text.insert(tk.INSERT, license_heading + "\n\n")
        self._license_text.insert(tk.INSERT, license_body)
        self._license_text.config(state=tk.DISABLED)
        self._initial_focus = self._license_text
        self._license_vertical_scroll = tk.ttk.Scrollbar(self, command=self._license_text.yview, orient=tk.VERTICAL)
        self._license_vertical_scroll.grid(column=4, row=0, rowspan=2, padx=1, pady=1, ipadx=1, ipady=1,
                                           sticky=tk.N + tk.E + tk.W + tk.S)
        self._license_text.config(yscrollcommand=self._license_vertical_scroll.set)
        self._license_horizontal_scroll = tk.ttk.Scrollbar(self, command=self._license_text.xview, orient=tk.HORIZONTAL)
        self._license_horizontal_scroll.grid(column=0, row=1, columnspan=4, padx=1, pady=1, ipadx=1, ipady=1,
                                             sticky=tk.N + tk.E + tk.W + tk.S)
        self._license_text.config(xscrollcommand=self._license_horizontal_scroll.set)
        self._accept_button = tk.ttk.Button(self, command=self.accept_callback, takefocus=True,
                                            text='I Accept this License Agreement', underline=2)
        self._accept_button.grid(column=0, row=2, columnspan=2, padx=1, pady=1, ipadx=1, ipady=1,
                                 sticky=tk.N + tk.E + tk.W + tk.S)
        self._cancel_button = tk.ttk.Button(self, command=self.cancel_callback, takefocus=True,
                                            default=tk.ACTIVE, text='I DON\'T Accept this License Agreement',
                                            underline=2)
        self._cancel_button.grid(column=2, row=2, columnspan=2, padx=1, pady=1, ipadx=1, ipady=1,
                                 sticky=tk.N + tk.E + tk.W + tk.S)
        self._size_grip = tk.ttk.Sizegrip(self)
        self._size_grip.grid(column=4, row=2)
        self.grab_set()
        if not self._initial_focus:
            self._initial_focus = self
        self._initial_focus.focus_set()
        self.wait_window(self)
