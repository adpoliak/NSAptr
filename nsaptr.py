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
import logging
import re
from base64 import b64decode, b64encode
from configparser import ConfigParser
from distutils.version import LooseVersion
from hashlib import sha1
from io import BytesIO
from os.path import expanduser, isdir
from platform import system
from types import ModuleType
from pyxb.binding import generate
from util.javafmtstr import pythonify_java_format_string, java_format_string_regex
from util.requests import make_request, reset_request
from util.zipfile_extract_perms import ZipFile, PERMS_PRESERVE_SAFE

# noinspection PyBroadException
try:
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
except:
    has_window_manager = False
    from textwrap import fill
else:
    has_window_manager = True
    from tkinter.filedialog import askdirectory
    from ui.tkinter.versionchooser import VersionChoiceDialog
    from ui.tkinter.licensedialog import LicenseDialog

config_defaults = {
    'config': {
        'accepted_license_sha1': None,
        'persist_choices': False,
        'keep_while_available': False,
        'do_not_ask_again': False,
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

opener, req = make_request(
    url='https://android.googlesource.com/platform/tools/base/+/master/sdklib/src/main/java/com/android/sdklib/'
        'repository/SdkRepoConstants.java?format=TEXT',
    method='GET',
)

with opener.open(req) as conn:
    byte_stream = conn.read()
    raw_data = b64decode(byte_stream)
    sdk_repo_source_data = raw_data.decode('utf-8')


def make_rxstr() -> str:
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

settings['URL_FILENAME_PATTERN'], num_replacements = java_format_string_regex.subn(pythonify_java_format_string,
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

if config['last_run']['version'] is not None and \
                config['last_run']['extraction_base_dir'] is not None and \
        isdir(config['last_run']['extraction_base_dir']):
    archives[config['last_run']['version'] + ':KEEP'] = {
        'size': None,
        'checksum': {
            'type': None,
            'value': None,
        },
        'url': config['last_run']['extraction_base_dir'],
        'license': config['last_run']['license_id'],
    }

if len(archives) >= 1:
    available_versions = sorted([LooseVersion(x) for x in archives.keys()])
    can_reinstall = config['last_run']['version'] in archives.keys()
    if not config['config'].getboolean('do_not_ask_again'):
        if not has_window_manager:
            print('Found Installation Candidates:')
            print("\n".join(sorted(available_versions)))
            raise NotImplementedError('Text-Mode Version Selection Not Implemented')
        else:
            if can_reinstall:
                last_version_text = config['last_run']['version']
                if config['config'].getboolean('keep_while_available'):
                    last_version_text += ':KEEP'
            else:
                last_version_text = None
            # noinspection PyUnboundLocalVariable
            version_chooser = VersionChoiceDialog(root,
                                                  available_versions,
                                                  persist=config['config'].getboolean('persist_choices'),
                                                  keep=config['config'].getboolean('keep_while_available'),
                                                  last_used=last_version_text)
            if version_chooser.return_code == 'accept':
                settings['SELECTED_VERSION'] = version_chooser.chosen_version
                settings['KEEP_WHILE_AVAILABLE'] = version_chooser.keep_while_available
                if version_chooser.persist:
                    config['config']['persist_choices'] = str(version_chooser.persist)
                    config['config']['keep_while_available'] = str(settings['KEEP_WHILE_AVAILABLE'])
                    config['config']['do_not_ask_again'] = str(version_chooser.do_not_ask_again)
            else:
                raise ValueError('User cancelled selection dialog')
    else:
        settings['KEEP_WHILE_AVAILABLE'] = config['config'].getboolean('keep_while_available')
        if settings['KEEP_WHILE_AVAILABLE'] and can_reinstall:
            settings['SELECTED_VERSION'] = config['last_run']['version'] + ':KEEP'
        else:
            settings['SELECTED_VERSION'] = available_versions[0].vstring
else:
    raise FileNotFoundError('No Available Versions')

if settings['SELECTED_VERSION'].endswith(':KEEP'):
    exit(0)

config['last_run']['version'] = settings['SELECTED_VERSION']

archive_data = archives[settings['SELECTED_VERSION']]

# TODO: refactor to skip IFF config['config'].getboolean('do_not_ask_again') and license has been accepted already
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
    # TODO: obey config['config'].getboolean('do_not_ask_again') for extraction directory as well
    config['last_run']['extraction_base_dir'] = askdirectory(title='Choose Output Base Directory', mustexist=True,
                                                             initialdir=config['last_run']['extraction_base_dir'])
else:
    raise NotImplementedError('Text-Mode Directory Choosing Not Implemented yet!')

assert config['last_run']['extraction_base_dir'] != ''
archive_obj = ZipFile(archive_fileobj)
archive_obj.extractall(path=config['last_run']['extraction_base_dir'], preserve_permissions=PERMS_PRESERVE_SAFE)

if config['config']['persist_choices']:
    with open(expanduser('~/.nsaptr.conf'), 'w+') as fp:
        config.write(fp)

# FINAL CLEANUPS

raise NotImplementedError('not done yet!')
