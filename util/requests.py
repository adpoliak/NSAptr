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
import typing
from http.cookiejar import CookieJar
from urllib import parse, request


def make_request(url: str,
                 method: typing.Optional[str] = 'GET') -> typing.Tuple[request.OpenerDirector, request.Request]:
    """
    Creates a request and an opener to run it
    :param url: Initial URL for request
    :param method: HTTP Method for request
    :return: tuple containing the OpenerDirector instance and the Request object
    """
    rdh = request.HTTPRedirectHandler()
    rdh.max_repeats = 999
    rdh.max_redirections = 999

    cj = CookieJar()
    cjh = request.HTTPCookieProcessor(cj)

    opener = request.build_opener(
        rdh,
        cjh
    )

    return opener, request.Request(url, method=method)


def reset_request(request_obj: request.Request,
                  new_uri: str,
                  new_method: str = None,
                  new_data: typing.Optional[typing.ByteString] = b'`^NO CHANGE^`') -> None:
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
