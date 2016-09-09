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
import re
import typing


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

# definition of Java Format String from https://docs.oracle.com/javase/7/docs/api/java/util/Formatter.html
java_format_string_regex = re.compile(
    r'%'
    r'(?P<index>[0-9]+\$)?'
    r'(?P<flags>[-#+ 0,(]+)?'
    r'(?P<width>[0-9]+)?'
    r'(?P<precision>\.[0-9]+)?'
    r'(?P<conversion>[bBhHsScCdoxXeEfgGaA%n]|[tT][HIklMSLNpzZsQBbhAaCYyjmdeRTrDFc)])',
    re.MULTILINE + re.VERBOSE + re.UNICODE + re.DOTALL
)
