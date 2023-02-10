#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
from email.utils import formatdate
# you may use urllib to encode data appropriately
import urllib.parse


def help():
    print("httpclient.py [GET/POST] [URL]\n")


class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

    def __str__(self) -> str:
        return "Response code: " + str(self.code) + "\n" + "Response body:\n" + self.body


class HTTPClient(object):
    # def get_host_port(self,url):

    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return None

    def get_code(self, data):
        code = data.splitlines()[0].split()[1]
        return int(code)

    def get_headers(self, data):
        return data.split("\r\n\r\n")[0]

    def get_body(self, data):
        return data.split("\r\n\r\n")[1]

    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))

    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer.decode('utf-8')

    def sendRequest(self, method, path, hostname, body="", otherFields={}, qParams=""):
        date = formatdate(usegmt=True)  # HTTP formatted data
        if qParams:
            qParams = '?'+qParams
        userAgent = 'Python'
        accept = '*/*'
        if not path:
            path = '/'
        header = (
            f"{method} {path+qParams} HTTP/1.1\r\n"
            f"Host: {hostname}\r\n"
            f"User-Agent: {userAgent}\r\n"
            f"Accept: {accept}\r\n"
            f"Connection: close\r\n"
        )
        if otherFields:
            for field, value in otherFields.items():
                header += f"{field}: {value}\r\n"
        if body:
            rq = header + "\r\n" + body + "\r\n"
        else:
            rq = header + "\r\n"

        self.sendall(rq)

    def GET(self, url, args=None):
        code = 500
        body = ""
        if args:  # append args if given
            url = self.add_query_param(url)
        u = urllib.parse.urlparse(url)
        port = u.port if u.port else 80
        self.connect(u.hostname, port)
        self.sendRequest('GET', u.path, u.hostname, qParams=u.query)
        data = self.recvall(self.socket)
        self.close()
        code = self.get_code(data)
        body = self.get_body(data)

        return HTTPResponse(code, body)

    def add_query_param(self, url, args={}):
        '''Given a URL and a dictionary, adds or replaces 
        the query parameter(s) from the dictionary and returns the modified URL.'''
        # adopted from answer at https://stackoverflow.com/a/12897375 by Wilfred Hughes
        scheme, netloc, path, query, fragment = urllib.parse.urlsplit(url)
        qs = query
        query_params = urllib.parse.parse_qs(qs)
        for field, value in args.items():
            query_params[field] = value
        query = urllib.parse.urlencode(query_params)
        return urllib.parse.urlunsplit((scheme, netloc, path, query, fragment))

    def POST(self, url, args=None):
        code = 500
        body = ""
        rBody = ""
        # only this content-type needs to be supported
        fields = {'Content-Type': 'application/x-www-form-urlencoded'}
        contentLength = 0
        if args:
            rBody = self.dict_to_form_urlencode(args)

        u = urllib.parse.urlparse(url)
        contentLength = self.get_content_length(
            rBody)  # calculate content length
        # add content length to header
        fields['Content-Length'] = str(contentLength)

        port = u.port if u.port else 80
        self.connect(u.hostname, port)

        self.sendRequest('POST', u.path, u.hostname,
                         body=rBody, otherFields=fields)

        data = self.recvall(self.socket)
        self.close()

        code = self.get_code(data)
        body = self.get_body(data)

        return HTTPResponse(code, body)

    def dict_to_form_urlencode(self, args):
        rBody = ""
        for field, value in args.items():
            rBody += f'{field}={urllib.parse.quote(value)}&'
        rBody = rBody[:-1]  # remove final &
        return rBody

    def get_content_length(self, str):
        return len(str.encode('utf-8'))

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST(url, args)
        else:
            return self.GET(url, args)


if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command(sys.argv[2], sys.argv[1]))
    else:
        print(client.command(sys.argv[1]))
