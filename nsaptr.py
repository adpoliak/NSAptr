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
from http.cookiejar import CookieJar
from pprint import pprint
from urllib import request
import re


def pythonify_java_format_string(match_obj):
    """
    Adapted from https://docs.python.org/3.1/library/string.html#format-string-syntax
    :param match_obj: match object generated as part of call to re.sub()
    :return: Java format string converted to python '{}'.format() syntax
    """
    fd = {'arg_integer': '', 'conversion': '!s', 'fs': {'fill': '', 'align': '', 'sign': '', 'type_prefix': '',
                                                        'zero_pad': '', 'width': '', 'comma_sep': '', 'precision': '',
                                                        'type': '',
                                                        }}

    captured = match_obj.groupdict()

    # Java Format String Indexes are Base 1
    # Python's are Base 0
    # So we have to deal with it...
    index = captured.get('index', None)
    if index is not None:
        fd['arg_integer'] = str(int(index[:-1]) - 1)

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
    encoded_data = b64decode(byte_stream)
    decoded_data = encoded_data.decode('utf-8')


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

settings = dict()
for match in rx.finditer(decoded_data):
    settings.update({key: val for key, val in match.groupdict().items() if val is not None})

if settings['NS_PATTERN'].startswith('NS_BASE + '):
    settings['NS_PATTERN'] = settings['NS_BASE'] + settings['NS_PATTERN'][10:].replace('"', '')

if b64encode(settings['GETSCHEMAURI'].encode('utf-8')) == (b'cHVibGljIHN0YXRpYyBTdHJpbmcgZ2V0U2NoZW1hVXJpKGludCB2ZXJzaW'
                                                           b'9uKSB7CiAgICAgICAgcmV0dXJuIFN0cmluZy5mb3JtYXQoTlNfQkFTRSAr'
                                                           b'ICIlZCIsIHZlcnNpb24pOyAgICAgICAgICAgLy8kTk9OLU5MUy0xJAogIC'
                                                           b'AgfQ=='):
    del (settings['GETSCHEMAURI'])
    settings['XMLNS'] = settings['NS_BASE'] + settings['NS_LATEST_VERSION']
    del (settings['NS_BASE'])

"""
definition of Java Format String from https://docs.oracle.com/javase/7/docs/api/java/util/Formatter.html
"""
jf = re.compile(
    r'%'
    r'(?P<index>[0-9]+\$)?'
    r'(?P<flags>[-#+ 0,(])?'
    r'(?P<width>[0-9]+)?'
    r'(?P<precision>[0-9]+)?'
    r'(?P<conversion>[bBhHsScCdoxXeEfgGaA%n]|[tT][HIklMSLNpzZsQBbhAaCYyjmdeRTrDFc)])',
    re.MULTILINE + re.VERBOSE + re.UNICODE + re.DOTALL)

settings['URL_FILENAME_PATTERN'], num_replacements = jf.subn(pythonify_java_format_string,
                                                             settings['URL_FILENAME_PATTERN'])

pprint(settings)

raise NotImplementedError('not done yet, sorry!')
