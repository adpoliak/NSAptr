#!/usr/bin/env python3
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
# from argparse import ArgumentParser
from base64 import b64decode, b64encode
from configparser import ConfigParser
from distutils.version import LooseVersion
from hashlib import sha1
from http.cookiejar import CookieJar
from io import BytesIO
from os.path import expanduser, isdir
from platform import system
from pyxb.binding import generate
from textwrap import fill
from tkinter.filedialog import askdirectory
from types import ModuleType
from urllib import request, parse
from zipfile import ZipFile
import logging
import re
import tkinter as tk
import tkinter.ttk
import typing


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
                                sticky=tk.N+tk.E+tk.W+tk.S)
        self._license_text.insert(tk.INSERT, license_heading + "\n\n")
        self._license_text.insert(tk.INSERT, license_body)
        self._license_text.config(state=tk.DISABLED)
        self._initial_focus = self._license_text
        self._license_vertical_scroll = tk.ttk.Scrollbar(self, command=self._license_text.yview, orient=tk.VERTICAL)
        self._license_vertical_scroll.grid(column=4, row=0, rowspan=2, padx=1, pady=1, ipadx=1, ipady=1,
                                           sticky=tk.N+tk.E+tk.W+tk.S)
        self._license_text.config(yscrollcommand=self._license_vertical_scroll.set)
        self._license_horizontal_scroll = tk.ttk.Scrollbar(self, command=self._license_text.xview, orient=tk.HORIZONTAL)
        self._license_horizontal_scroll.grid(column=0, row=1, columnspan=4, padx=1, pady=1, ipadx=1, ipady=1,
                                             sticky=tk.N+tk.E+tk.W+tk.S)
        self._license_text.config(xscrollcommand=self._license_horizontal_scroll.set)
        self._accept_button = tk.ttk.Button(self, command=self.accept_callback, takefocus=True,
                                            text='I Accept this License Agreement', underline=2)
        self._accept_button.grid(column=0, row=2, columnspan=2, padx=1, pady=1, ipadx=1, ipady=1,
                                 sticky=tk.N+tk.E+tk.W+tk.S)
        self._cancel_button = tk.ttk.Button(self, command=self.cancel_callback, takefocus=True,
                                            default=tk.ACTIVE, text='I DON\'T Accept this License Agreement',
                                            underline=2)
        self._cancel_button.grid(column=2, row=2, columnspan=2, padx=1, pady=1, ipadx=1, ipady=1,
                                 sticky=tk.N+tk.E+tk.W+tk.S)
        self.grab_set()
        if not self._initial_focus:
            self._initial_focus = self
        self._initial_focus.focus_set()
        self.wait_window(self)


def pythonify_java_format_string(match_obj: typing.re.Match) -> str:
    """
    :rtype: str
    :param match_obj: match object generated as part of call to re.sub()
    :return: Java format string converted to python '{}'.format() syntax
    Adapted from https://docs.python.org/3.1/library/string.html#format-string-syntax
    """
    fd = {'arg_integer': '', 'conversion': '', 'fs': {'fill': '', 'align': '', 'sign': '', 'type_prefix': '',
                                                      'zero_pad': '', 'width': '', 'comma_sep': '', 'precision': '',
                                                      'type': '',
                                                      }}

    captured = match_obj.groupdict()

    index = captured.get('index', None)
    if index is not None:
        # Java Format String Indexes are Base 1
        # Python's are Base 0
        # So we have to deal with it...
        fd['arg_integer'] = str(int(index[:-1]) - 1)

    flags = captured.get('flags', None)
    if flags is not None:
        # Lack of alignment flag in Java means to do right-alignment
        fd['fs']['align'] = '<' if '-' in flags else '>'
        if '+' in flags:
            fd['fs']['sign'] = '+'
        elif ' ' in flags:
            fd['fs']['sign'] = ' '
        else:
            # Java doesn't do distinction between default left- and right-aligned fields, so we force Java's default
            fd['fs']['sign'] = '-'
        if '#' in flags:
            fd['fs']['type_prefix'] = '#'
        if '0' in flags:
            fd['fs']['fill'] = '0'
            fd['fs']['align'] = '='
        if ',' in flags:
            fd['fs']['comma_sep'] = ','
        if '(' in flags:
            raise NotImplementedError('"(" Formatting flag not natively supported in Python.')

    width = captured.get('width', None)
    if width is not None:
        # Zero padding was taken care of in flags, make sure it is stripped out here
        fd['fs']['width'] = str(int(width))

    precision = captured.get('precision', None)
    if precision is not None:
        fd['fs']['precision'] = precision

    conversion = captured.get('conversion', None)
    if conversion is not None:
        if conversion in list('sScCdoXxeEfgG'):
            fd['fs']['type'] = conversion
        else:
            raise NotImplementedError('"{}" Conversion not natively supported in Python.'.format(conversion))

    ret = (
        '{' +
        fd['arg_integer'] +
        fd['conversion'] +
        ':' +
        fd['fs']['fill'] +
        fd['fs']['align'] +
        fd['fs']['sign'] +
        fd['fs']['type_prefix'] +
        fd['fs']['zero_pad'] +
        fd['fs']['width'] +
        fd['fs']['comma_sep'] +
        fd['fs']['precision'] +
        fd['fs']['type'] +
        '}'
    )
    return ret


def reset_request(request_obj: request.Request,
                  new_uri: str,
                  new_method: str=None,
                  new_data: typing.Optional[typing.ByteString]=b'`^NO CHANGE^`') -> None:
    """
    Resets a urllib.request.Request instance URI
    Default value of new_data chosen because it contains characters that are not allowed per RFC 3986
    :param request_obj: urllib.request.Request - The object being reset
    :param new_uri: str - String containing the new URI
    :param new_method: str - String containing the new request method
    :param new_data: byte string - data to be sent alongside the request
    :rtype: None
    """
    if new_method is not None:
        request_obj.method = new_method
    if new_data != b'`^NO CHANGE^`':
        request_obj.data = new_data
    request_obj.full_url = new_uri
    result = parse.urlparse(new_uri, allow_fragments=True)
    request_obj.host = result.netloc
    request_obj.fragment = result.fragment
    request_obj.origin_req_host = request_obj.host
    request_obj.unredirected_hdrs = dict()


# noinspection PyBroadException
try:
    root = tk.Tk()
    root.withdraw()
    has_window_manager = True
except:
    has_window_manager = False

config_defaults = {
    'config': {
        'accepted_license_sha1': None,
        'no_upgrade_prompt': None,
    },
    'last_run': {
        'extraction_base_dir': '.',
        'license_id': None,
        'version': None,
    },
}
config = ConfigParser(allow_no_value=True, strict=True, empty_lines_in_values=False)
config.read_dict(config_defaults)
config.read([
    './nsaptr.conf',
    '/etc/nsaptr.conf', '/etc/nsaptr/nsaptr.conf',
    '/usr/local/etc/nsaptr.conf', '/usr/local/etc/nsaptr/nsaptr.conf',
    '/opt/local/etc/nsaptr.conf', '/opt/local/etc/nsaptr/nsaptr.conf',
    '/usr/local/nsaptr/etc/nsaptr.conf', '/usr/local/nsaptr/nsaptr.conf',
    '/opt/local/nsaptr/etc/nsaptr.conf', '/opt/local/nsaptr/nsaptr.conf',
    expanduser('~/nsaptr.conf'), expanduser('~/nsaptr/nsaptr.conf'),
    expanduser('~/.nsaptr.conf'), expanduser('~/.nsaptr/nsaptr.conf'),
])
if not isdir(config['last_run']['extraction_base_dir']):
    config['last_run']['extraction_base_dir'] = '.'

rdh = request.HTTPRedirectHandler()
rdh.max_repeats = 999
rdh.max_redirections = 999

cj = CookieJar()
cjh = request.HTTPCookieProcessor(cj)

opener = request.build_opener(
    rdh,
    cjh
)

req = request.Request(
    url='https://android.googlesource.com/platform/tools/base/+/master/sdklib/src/main/java/com/android/sdklib/'
        'repository/SdkRepoConstants.java?format=TEXT',
    method='GET',
)

with opener.open(req) as conn:
    byte_stream = conn.read()
    raw_data = b64decode(byte_stream)
    sdk_repo_source_data = raw_data.decode('utf-8')


def make_rxstr() ->str:
    rxstr = r''
    sf = r'static[ \t]+final[ \t]+'
    psf = r'^[ \t]*public[ \t]+' + sf
    psfs = psf + r'string[ \t]+'
    rsfs = r'^[ \t]*private[ \t]+' + sf + r'string[ \t]+'
    endl = r'[ \t]*$'
    nn1 = r'[ \t]+//\$NON-NLS-1\$' + endl
    # URL_GOOGLE_SDK_SITE Variable
    rxstr += psfs + r'URL_GOOGLE_SDK_SITE[ \t\r\n]*=[ \t\r\n]*[\'"](?P<URL_GOOGLE_SDK_SITE>.*?)[\'"];' + nn1 + r'|'
    # NS_LATEST_VERSION Variable
    rxstr += psf + r'int[ \t]+NS_LATEST_VERSION[ \t\r\n]*=[ \t\r\n]*(?P<NS_LATEST_VERSION>.*?);' + endl + r'|'
    # URL_FILENAME_PATTERN Variable
    rxstr += psfs + r'URL_FILENAME_PATTERN[ \t\r\n]*=[ \t\r\n]*[\'"](?P<URL_FILENAME_PATTERN>.*?)[\'"];' + nn1 + r'|'
    # NS_BASE Variable
    rxstr += rsfs + r'NS_BASE[ \t\r\n]*=[ \t\r\n]*[\'"](?P<NS_BASE>.*?)[\'"];' + nn1 + r'|'
    # NS_PATTERN Variable
    rxstr += psfs + r'NS_PATTERN[ \t\r\n]*=[ \t\r\n]*(?P<NS_PATTERN>.*?);' + nn1 + r'|'
    # NS_URI Variable
    rxstr += psfs + r'NS_URI[ \t\r\n]*=[ \t\r\n]*(?P<NS_URI>.*?);' + endl + r'|'
    # NODE_SDK_REPOSITORY Variable
    rxstr += psfs + r'NODE_SDK_REPOSITORY[ \t\r\n]*=[ \t\r\n]*[\'"](?P<NODE_SDK_REPOSITORY>.*?)[\'"];' + nn1 + r'|'
    # NODE_PLATFORM_TOOL Variable
    rxstr += psfs + r'NODE_PLATFORM_TOOL[ \t\r\n]*=[ \t\r\n]*[\'"](?P<NODE_PLATFORM_TOOL>.*?)[\'"];' + nn1 + r'|'
    # GETSCHEMAURI Variable
    rxstr += r'^[ \t]*(?P<GETSCHEMAURI>public[ \t]+static[ \t]+string[ \t]+getSchemaUri\([^)]*\)[ \t]*\{.*?\})[ \t\r\n]'
    rxstr += r'*$'
    return rxstr

rx_string = make_rxstr()
rx = re.compile(rx_string, re.MULTILINE + re.IGNORECASE + re.VERBOSE + re.UNICODE + re.DOTALL)

settings = dict()
for match in rx.finditer(sdk_repo_source_data):
    settings.update({key: val for key, val in match.groupdict().items() if val is not None})

if settings['NS_PATTERN'].startswith('NS_BASE + '):
    settings['NS_PATTERN'] = settings['NS_BASE'] + settings['NS_PATTERN'][10:].replace('"', '')

if b64encode(settings['GETSCHEMAURI'].encode('utf-8')) == (b'cHVibGljIHN0YXRpYyBTdHJpbmcgZ2V0U2NoZW1hVXJpKGludCB2ZXJzaW'
                                                           b'9uKSB7CiAgICAgICAgcmV0dXJuIFN0cmluZy5mb3JtYXQoTlNfQkFTRSAr'
                                                           b'ICIlZCIsIHZlcnNpb24pOyAgICAgICAgICAgLy8kTk9OLU5MUy0xJAogIC'
                                                           b'AgfQ=='):
    if b64encode(settings['NS_URI'].encode('utf-8')) == b'Z2V0U2NoZW1hVXJpKE5TX0xBVEVTVF9WRVJTSU9OKQ==':
        settings['XMLNS'] = settings['NS_BASE'] + settings['NS_LATEST_VERSION']

# definition of Java Format String from https://docs.oracle.com/javase/7/docs/api/java/util/Formatter.html
jf = re.compile(
    r'%'
    r'(?P<index>[0-9]+\$)?'
    r'(?P<flags>[-#+ 0,(]+)?'
    r'(?P<width>[0-9]+)?'
    r'(?P<precision>\.[0-9]+)?'
    r'(?P<conversion>[bBhHsScCdoxXeEfgGaA%n]|[tT][HIklMSLNpzZsQBbhAaCYyjmdeRTrDFc)])',
    re.MULTILINE + re.VERBOSE + re.UNICODE + re.DOTALL
)

settings['URL_FILENAME_PATTERN'], num_replacements = jf.subn(pythonify_java_format_string,
                                                             settings['URL_FILENAME_PATTERN'])

settings['REPO_URL'] = '{}{}'.format(
    settings['URL_GOOGLE_SDK_SITE'],
    settings['URL_FILENAME_PATTERN'].format(int(settings['NS_LATEST_VERSION']))
)

settings['XSD_URL'] = '{}/{}-{}.xsd?format=TEXT'.format(
    'https://android.googlesource.com/platform/tools/base/+/master/sdklib/src/main/java/com/android/sdklib/repository',
    settings['NODE_SDK_REPOSITORY'],
    settings['NS_LATEST_VERSION']
)

reset_request(req, settings['REPO_URL'])
with opener.open(req) as conn:
    byte_stream = conn.read()
    repo_data = byte_stream.decode('utf-8')

reset_request(req, settings['XSD_URL'])
with opener.open(req) as conn:
    byte_stream = conn.read()
    raw_data = b64decode(byte_stream)
    xsd_data = raw_data.decode('utf-8')
assert re.search(settings['NS_PATTERN'], xsd_data)

logging.disable(logging.CRITICAL)
repository_xsd_code = generate.GeneratePython(schema_text=xsd_data)

repository_module_code = compile(source=repository_xsd_code, filename=settings['XSD_URL'], mode='exec')
repository_module = ModuleType('repository_module')
exec(repository_module_code, repository_module.__dict__)

repository = repository_module.CreateFromDocument(xml_text=repo_data, location_base=settings['REPO_URL'])
repository_dom = repository.toDOM()
assert repository_dom.documentElement.namespaceURI == settings['XMLNS']
assert repository_dom.documentElement.localName == settings['NODE_SDK_REPOSITORY']

platforms = {
    'Linux': 'linux',
    'Windows': 'windows',
    'Darwin': 'macosx',
}

archives = dict()
# TODO: get previous installation info from configuration to show in later steps

for candidate in getattr(repository, settings['NODE_PLATFORM_TOOL'].replace('-', '_')):
    candidate_version = LooseVersion('{}.{}.{}'.format(candidate.revision.major,
                                                       candidate.revision.minor,
                                                       candidate.revision.micro)).vstring
    candidate_license = candidate.uses_license.ref
    for archive in candidate.archives.archive:
        if archive.host_os == platforms[system()]:
            assert archive.checksum.type in ['sha1', ]
            archives[candidate_version] = {
                'size': archive.size,
                'checksum': {
                    'type': archive.checksum.type,
                    'value': archive.checksum.value(),
                },
                'url': archive.url,
                'license': candidate_license,
            }
            break

if config['last_run']['version'] is not None:
    archives[LooseVersion(config['last_run']['version']+':INSTALLED').vstring] = {
        'size': None,
        'checksum': {
            'type': None,
            'value': None,
        },
        'url': config['last_run']['extraction_base_dir'],
        'license': config['last_run']['license_id'],
    }

print('Found Installation Candidates:')
print("\n".join(sorted(archives.keys(), key=LooseVersion)))

if len(archives) > 1:
    # TODO: prompt user for which version to deploy
    raise NotImplementedError('Version Selection Not Implemented')
elif len(archives) == 0:
    raise FileNotFoundError('No Available Versions')
else:
    settings['SELECTED_VERSION'] = list(archives.keys())[0]

if settings['SELECTED_VERSION'].endswith(':INSTALLED'):
    exit(0)

config['last_run']['version'] = settings['SELECTED_VERSION']

archive_data = archives[settings['SELECTED_VERSION']]

for prod_license in [x for x in repository.license if x.id == archive_data['license']]:
    license_text = prod_license.value()
    sha1_checker = sha1()
    sha1_checker.update(license_text.encode('utf-8'))
    if sha1_checker.hexdigest() not in str(config['config']['accepted_license_sha1']):
        if has_window_manager:
            # noinspection PyUnboundLocalVariable
            d = LicenseDialog(root, license_heading=('Android Platform Tools v{} for {} is distributed '
                                                     'under the "{}" license:').format(settings['SELECTED_VERSION'],
                                                                                       system(),
                                                                                       archive_data['license']),
                              license_body=license_text)
            license_accepted = d.return_code == 'accept'
            d.destroy()()
        else:
            print(('Android Platform Tools v{} for {} is distributed '
                   'under the "{}" license:').format(settings['SELECTED_VERSION'],
                                                     system(),
                                                     archive_data['license']))
            print('Please read the following license:')
            print(fill(license_text, replace_whitespace=False, drop_whitespace=False, width=80))
            license_accepted = input('Please type "I ACCEPT THIS LICENSE" to continue []:') == 'I ACCEPT THIS LICENSE'
        if not license_accepted:
            raise PermissionError('License Not Accepted')
        else:
            config['last_run']['license_id'] = archive_data['license']
            if config['config']['accepted_license_sha1'] is None:
                config['config']['accepted_license_sha1'] = sha1_checker.hexdigest()
            else:
                config['config']['accepted_license_sha1'] += ',' + sha1_checker.hexdigest()
    break

if not archive_data['url'].lower().startswith('http'):
    archive_data['url'] = settings['URL_GOOGLE_SDK_SITE'] + archive_data['url']

reset_request(req, archive_data['url'])
with opener.open(req) as conn:
    byte_stream = conn.read()
    assert len(byte_stream) == archive_data['size']
    sha1_checker = sha1()
    sha1_checker.update(byte_stream)
    assert sha1_checker.hexdigest() == archive_data['checksum']['value']
    archive_fileobj = BytesIO(byte_stream)

assert archive_data['url'].lower().endswith('.zip')
if has_window_manager:
    config['last_run']['extraction_base_dir'] = askdirectory(title='Choose Output Base Directory', mustexist=True,
                                                             initialdir=config['last_run']['extraction_base_dir'])
assert config['last_run']['extraction_base_dir'] != ''
archive_obj = ZipFile(archive_fileobj)
archive_obj.extractall(path=config['last_run']['extraction_base_dir'])
# TODO: Replace line above with code that sets permissions on executables as they extract


with open(expanduser('~/.nsaptr.conf'), 'w+') as fp:
    config.write(fp)

# FINAL CLEANUPS

raise NotImplementedError('not done yet!')
