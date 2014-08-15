# -*- coding: utf-8 -*-

import argparse
import json
import time
import logging
import signal
import re
from json import JSONEncoder
from datetime import datetime

import aiohttp
import aiohttp.server

import asyncio

from config import config, init_config


__author__ = 'Victor Poluksht'

log = logging.getLogger(__name__)


# # monkey patch json to support datetime objects
def _default(self, obj):
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    return getattr(obj.__class__, "serialize", _default.default)(obj)


_default.default = JSONEncoder().default
JSONEncoder.default = _default


def setup_logging():
    file_handler = logging.FileHandler(config.logfile)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)
    log.setLevel(logging.INFO)


class Server(aiohttp.server.ServerHttpProtocol):
    def __init__(self, lst):
        super().__init__()
        self.last_check_dict = lst

    @asyncio.coroutine
    def handle_request(self, message, payload):
        response = aiohttp.Response(
            self.writer, 200, http_version=message.version)
        response.add_header('Content-type', 'application/json')
        response.send_headers()

        response.write(
            json.dumps(sorted([(k, v) for k, v in self.last_check_dict.items()],
                              key=lambda x: x[1].get('time'))).encode('ascii'))
        yield from response.write_eof()


class Worker:
    def __init__(self):
        self.loop = None
        self.conn = None
        self.last = None

    @asyncio.coroutine
    def do_get_page(self, url, pattern):

        while True:

            start = time.clock()

            try:
                resp = yield from aiohttp.request('GET', url, connector=self.conn)
            except Exception as e:
                stop = time.clock()
                if isinstance(e, aiohttp.errors.OsConnectionError):
                    log.info('finished processing {0}, invalid hostname, took {1:.2f} seconds'.format(
                        url, stop - start))
                    self.last[url] = {'result': 'unknown host', 'time': datetime.now()}
            else:
                stop = time.clock()
                if resp.status == 200 and 'text/html' in resp.headers.get('content-type'):

                    body = (yield from resp.read()).decode('utf-8', 'replace')

                    resp.close()

                    n = re.findall(pattern, body)
                    stop = time.clock()

                    log.info(
                        'finished processing {0}, {1} pattern \"{2}\", took {3:.2f} seconds'.format(
                            url,
                            'found' if n else 'not found',
                            pattern,
                            stop - start))

                    self.last[url] = {'result': 'found' if n else 'not found', 'time': datetime.now()}

                else:
                    log.info('finished processing {0}, http error {1}, took {2:.2f} seconds'.format(
                        url, resp.status, stop - start))
                    self.last[url] = {'result': resp.status, 'time': datetime.now()}

            yield from asyncio.sleep(config.period)

    def stop_async_loop(self):
        self.loop.stop()
        self.conn.close()

    def run(self, to_ping, last_check):
        self.last = last_check
        self.loop = asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)
        self.conn = aiohttp.TCPConnector(loop=self.loop)
        for url, pattern in to_ping:
            asyncio.async(self.do_get_page(url, pattern))
        server = self.loop.create_server(lambda: Server(self.last), config.host, config.port)
        self.loop.add_signal_handler(signal.SIGINT, self.stop_async_loop)
        self.loop.add_signal_handler(signal.SIGTERM, self.stop_async_loop)
        self.loop.run_until_complete(server)
        self.loop.run_forever()


if __name__ == '__main__':

    # # i'm waiting for this (http://bugs.python.org/issue11588) bug to be fixed.
    # # now you should manually choose your way by passing config or options as
    # # first argument to runme.py

    parser = argparse.ArgumentParser(description='F-Secure http checker utility')
    subparsers = parser.add_subparsers()

    config_file_parser = subparsers.add_parser('config')
    config_file_parser.add_argument('--config', action='store', help='config file', required=True)

    options_parser = subparsers.add_parser('options')
    options_parser.add_argument('--datafile', action='store', help='data file containing list of urls', required=True)
    options_parser.add_argument('--period', action='store', type=int, help='check period in seconds', default=30)
    options_parser.add_argument('--logfile', action='store', help='log file', default='output.log')
    options_parser.add_argument('--host', action='store', help='host to listen', default='127.0.0.1')
    options_parser.add_argument('--port', action='store', type=int, help='port to listen', default=8080)

    args = vars(parser.parse_args())
    if not args:
        parser.print_help()

    # # assuming config file has all required options

    init_config(args.get('config', args))
    setup_logging()

    data = []
    last = {}

    with open(config.datafile) as f:
        [data.append(x.rstrip().split('|')) for x in f.readlines()]

    Worker().run(data, last)

    print('\nthe end')