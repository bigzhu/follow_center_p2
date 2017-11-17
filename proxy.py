#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64

import tornado
import tornado.web
import logging
import socket
try:
    from urlparse import urlparse
except ImportError:
    import urllib.parse as urlparse

import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web
import tornado.httpclient

logger = logging.getLogger('tornado_proxy')


def decodeUrl(url):
    '''
    针对中国大陆的网络, url 要加密两次才不会被 gfw 发现, 这里也要解密两次
    >>> decodeUrl('YUhSMGNEb3ZMelk0TG0xbFpHbGhMblIxYldKc2NpNWpiMjB2TVRNNFpUZzBPV0ZsWWpkbE4yUmhPV1ppT1dGaVpXUTFOamxsT0dVMU9ETXZkSFZ0WW14eVgyNXBOV0o1Y1VObVNFWXhkSE0zZFRCeWJ6UmZjakZmTVRJNE1DNXFjR2M9')
    b'http://68.media.tumblr.com/138e849aeb7e7da9fb9abed569e8e583/tumblr_ni5byqCfHF1ts7u0ro4_r1_1280.jpg'
    '''
    return base64.b64decode(base64.b64decode(url))


class ProxyHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'CONNECT']

    @tornado.web.asynchronous
    def get(self, url):
        self.url = url
        logger.debug('Handle %s request to %s', self.request.method, self.url)

        def handle_response(response):
            if (response.error and not
                    isinstance(response.error, tornado.httpclient.HTTPError)):
                self.set_status(500)
                self.write('Internal server error:\n' + str(response.error))
            else:
                self.set_status(response.code)
                for header in ('Date', 'Cache-Control', 'Server', 'Content-Type', 'Location'):
                    v = response.headers.get(header)
                    if v:
                        self.set_header(header, v)
                v = response.headers.get_list('Set-Cookie')
                if v:
                    for i in v:
                        self.add_header('Set-Cookie', i)
                if response.body:
                    self.write(response.body)
            self.finish()

        body = self.request.body
        if not body:
            body = None
        # try:
        self.request.headers["Host"] = urlparse(self.url).netloc
        fetch_request(
            self.url, handle_response,
            method=self.request.method, body=body,
            headers=self.request.headers, follow_redirects=False,
            allow_nonstandard_methods=True)
        # except tornado.httpclient.HTTPError as e:
        #    if hasattr(e, 'response') and e.response:
        #        handle_response(e.response)
        #    else:
        #        self.set_status(500)
        #        self.write('Internal server error:\n' + str(e))
        #        self.finish()

    @tornado.web.asynchronous
    def post(self):
        return self.get()

    @tornado.web.asynchronous
    def connect(self):
        logger.debug('Start CONNECT to %s', self.url)
        host, port = self.url.split(':')
        client = self.request.connection.stream

        def read_from_client(data):
            upstream.write(data)

        def read_from_upstream(data):
            client.write(data)

        def client_close(data=None):
            if upstream.closed():
                return
            if data:
                upstream.write(data)
            upstream.close()

        def upstream_close(data=None):
            if client.closed():
                return
            if data:
                client.write(data)
            client.close()

        def start_tunnel():
            logger.debug('CONNECT tunnel established to %s', self.url)
            client.read_until_close(client_close, read_from_client)
            upstream.read_until_close(upstream_close, read_from_upstream)
            client.write(b'HTTP/1.0 200 Connection established\r\n\r\n')

        def on_proxy_response(data=None):
            if data:
                first_line = data.splitlines()[0]
                http_v, status, text = first_line.split(None, 2)
                if int(status) == 200:
                    logger.debug('Connected to upstream proxy %s', proxy)
                    start_tunnel()
                    return

            self.set_status(500)
            self.finish()

        def start_proxy_tunnel():
            upstream.write('CONNECT %s HTTP/1.1\r\n' % self.url)
            upstream.write('Host: %s\r\n' % self.url)
            upstream.write('Proxy-Connection: Keep-Alive\r\n\r\n')
            upstream.read_until('\r\n\r\n', on_proxy_response)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        upstream = tornado.iostream.IOStream(s)

        proxy = get_proxy(self.url)
        if proxy:
            proxy_host, proxy_port = parse_proxy(proxy)
            upstream.connect((proxy_host, proxy_port), start_proxy_tunnel)
        else:
            upstream.connect((host, int(port)), start_tunnel)


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
