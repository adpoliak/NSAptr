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
from base64 import b64decode, b64encode
from distutils.version import LooseVersion
from http.cookiejar import CookieJar
from platform import system
from pyxb.binding import generate
from textwrap import fill
from types import ModuleType
from urllib import request, parse
import re


def pythonify_java_format_string(match_obj):
    """
    Adapted from https://docs.python.org/3.1/library/string.html#format-string-syntax
    :param match_obj: match object generated as part of call to re.sub()
    :return: Java format string converted to python '{}'.format() syntax
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


rdh = request.HTTPRedirectHandler()
rdh.max_repeats = 999
rdh.max_redirections = 999

cj = CookieJar()
cjh = request.HTTPCookieProcessor(cj)
del cj
del CookieJar

opener = request.build_opener(
    rdh,
    cjh
)
del rdh
del cjh

req = request.Request(
    url='https://android.googlesource.com/platform/tools/base/+/master/sdklib/src/main/java/com/android/sdklib/'
        'repository/SdkRepoConstants.java?format=TEXT',
    method='GET',
)
del request

with opener.open(req) as conn:
    byte_stream = conn.read()
    raw_data = b64decode(byte_stream)
    sdk_repo_source_data = raw_data.decode('utf-8')
    del raw_data

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
rxstr += r'^[ \t]*(?P<GETSCHEMAURI>public[ \t]+static[ \t]+string[ \t]+getSchemaUri\([^)]*\)[ \t]*\{.*?\})[ \t\r\n]*$'
rx = re.compile(rxstr, re.MULTILINE + re.IGNORECASE + re.VERBOSE + re.UNICODE + re.DOTALL)
del rxstr
del sf
del psf
del psfs
del rsfs
del endl
del nn1

settings = dict()
for match in rx.finditer(sdk_repo_source_data):
    settings.update({key: val for key, val in match.groupdict().items() if val is not None})
del match
del rx
del sdk_repo_source_data

if settings['NS_PATTERN'].startswith('NS_BASE + '):
    settings['NS_PATTERN'] = settings['NS_BASE'] + settings['NS_PATTERN'][10:].replace('"', '')

if b64encode(settings['GETSCHEMAURI'].encode('utf-8')) == (b'cHVibGljIHN0YXRpYyBTdHJpbmcgZ2V0U2NoZW1hVXJpKGludCB2ZXJzaW'
                                                           b'9uKSB7CiAgICAgICAgcmV0dXJuIFN0cmluZy5mb3JtYXQoTlNfQkFTRSAr'
                                                           b'ICIlZCIsIHZlcnNpb24pOyAgICAgICAgICAgLy8kTk9OLU5MUy0xJAogIC'
                                                           b'AgfQ=='):
    if b64encode(settings['NS_URI'].encode('utf-8')) == b'Z2V0U2NoZW1hVXJpKE5TX0xBVEVTVF9WRVJTSU9OKQ==':
        del settings['GETSCHEMAURI']
        del settings['NS_URI']
        settings['XMLNS'] = settings['NS_BASE'] + settings['NS_LATEST_VERSION']
        del settings['NS_BASE']
del b64encode

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
del jf
del num_replacements
del pythonify_java_format_string

settings['REPO_URL'] = '{}{}'.format(
    settings['URL_GOOGLE_SDK_SITE'],
    settings['URL_FILENAME_PATTERN'].format(int(settings['NS_LATEST_VERSION']))
)
del settings['URL_FILENAME_PATTERN']

settings['XSD_URL'] = '{}/{}-{}.xsd?format=TEXT'.format(
    'https://android.googlesource.com/platform/tools/base/+/master/sdklib/src/main/java/com/android/sdklib/repository',
    settings['NODE_SDK_REPOSITORY'],
    settings['NS_LATEST_VERSION']
)
del settings['NS_LATEST_VERSION']

req.full_url = settings['REPO_URL']
result = parse.urlparse(settings['REPO_URL'], allow_fragments=True)
req.host = result.netloc
req.fragment = result.fragment
req.origin_req_host = req.host
req.unredirected_hdrs = dict()
with opener.open(req) as conn:
    byte_stream = conn.read()
    repo_data = byte_stream.decode('utf-8')

req.full_url = settings['XSD_URL']
result = parse.urlparse(settings['XSD_URL'], allow_fragments=True)
req.host = result.netloc
req.fragment = result.fragment
req.origin_req_host = req.host
req.unredirected_hdrs = dict()
with opener.open(req) as conn:
    byte_stream = conn.read()
    raw_data = b64decode(byte_stream)
    xsd_data = raw_data.decode('utf-8')
    del raw_data
assert re.search(settings['NS_PATTERN'], xsd_data)
del re
del b64decode
del settings['NS_PATTERN']

generate._log.disabled = 1
repository_xsd_code = generate.GeneratePython(schema_text=xsd_data)
del xsd_data
repository_module_code = compile(source=repository_xsd_code, filename=settings['XSD_URL'], mode='exec')
del repository_xsd_code
repository_module = ModuleType('repository_module')
exec(repository_module_code, repository_module.__dict__)
del repository_module_code
del settings['XSD_URL']
del generate
del ModuleType

repository = repository_module.CreateFromDocument(xml_text=repo_data, location_base=settings['REPO_URL'])
del repository_module
del repo_data
del settings['REPO_URL']
assert len([y for x, y in repository._namespaceContext().inScopeNamespaces().items() if y._Namespace__uri == settings['XMLNS']]) > 0
assert repository._element().name().localName() == settings['NODE_SDK_REPOSITORY']
del settings['NODE_SDK_REPOSITORY']
del settings['XMLNS']

platforms = {
    'Linux': 'linux',
    'Windows': 'windows',
    'Darwin': 'macosx',
}

licenses = dict()
archives = dict()
# TODO: get previous installation info from configuration to show in later steps

for candidate in getattr(repository, settings['NODE_PLATFORM_TOOL'].replace('-', '_')):
    candidate_version = LooseVersion('{}.{}.{}'.format(candidate.revision.major,
                                                       candidate.revision.minor,
                                                       candidate.revision.micro)).vstring
    licenses[candidate_version] = candidate.uses_license.ref
    for archive in candidate.archives.archive:
        if archive.host_os == platforms[system()]:
            archives[candidate_version] = {
                'size': archive.size,
                'checksum': {
                    'type': archive.checksum.type,
                    'value': archive.checksum.value(),
                },
                'url': archive.url,
            }
            break
    if archives.get(candidate_version, None) is None:
        del licenses[candidate_version]
del settings['NODE_PLATFORM_TOOL']
del platforms
del candidate
del candidate_version
del archive

print('Found Installation Candidates:')
print("\n".join(sorted(archives.keys(), key=LooseVersion)))

if len(archives) > 1:
    # TODO: prompt user for which version to deploy
    raise NotImplementedError('Version Selection Not Implemented')
elif len(archives) == 0:
    raise FileNotFoundError('No Available Versions')
else:
    settings['SELECTED_VERSION'] = list(archives.keys())[0]
del LooseVersion

print('Android Platform Tools v{} for {} is distributed under the "{}" license.'.format(settings['SELECTED_VERSION'],
                                                                                        system(),
                                                                                        licenses[settings['SELECTED_VERSION']]))
del system
print('Please read the following license:')
for prod_license in [x for x in repository.license if x.id == licenses[settings['SELECTED_VERSION']]]:
    print(fill(prod_license.value(), replace_whitespace=False,  drop_whitespace=False, width=80))
del fill
del prod_license
del licenses
#license_accepted = input('Please type "I ACCEPT THIS LICENSE" to continue []:')
#if license_accepted != 'I ACCEPT THIS LICENSE':
#    raise PermissionError('License Not Accepted')

archive_data = archives[settings['SELECTED_VERSION']]
del archives

# TODO: Retrieve and verify archive
del byte_stream
del conn
del req
del opener
del parse
del repository
del result

# TODO: deploy archive
del archive_data

# TODO: save settings

# FINAL CLEANUPS
raise NotImplementedError('not done yet!')
