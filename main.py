import types

import asyncio
import redis

from asyncio.log import logger
from asyncio.selector_events import _SelectorSocketTransport


def _make_pubsub_socket_transport(self, sock, protocol, waiter=None, *,
                                  extra=None, server=None):
    return _PubsubSelectorSocketTransport(self, sock, protocol, waiter,
                                          extra, server)


class _PubsubSelectorSocketTransport(_SelectorSocketTransport):

    def __init__(self, loop, sock, protocol, waiter=None,
                 extra=None, server=None):
        super().__init__(loop, sock, protocol, waiter, extra, server)

    def _read_ready(self):
        message = self._pubsub.get_message()
        if message:
            if isinstance(message['data'], bytes):
                self._protocol.data_received(message['data'])
        else:
            if self._loop.get_debug():
                logger.debug("%r received EOF", self)
            keep_open = self._protocol.eof_received()
            if keep_open:
                # We're keeping the connection open so the
                # protocol can write more, but we still can't
                # receive more, so remove the reader callback.
                self._loop.remove_reader(self._sock_fd)
            else:
                self.close()


@asyncio.coroutine
def foo(pubsub, loop):
    reader, writer = yield from asyncio.open_connection(sock=pubsub.connection._sock, loop=loop)
    reader._transport._pubsub = pubsub
    while not reader.at_eof():
        message = yield from reader.read(256)
        print('message: {}, type:{}'.format(message.decode(), type(message)))
    writer.close()


def main():
    pubsub = redis.StrictRedis('127.0.0.1').pubsub()
    pubsub.subscribe('test')

    loop = asyncio.get_event_loop()
    loop._make_socket_transport = types.MethodType(_make_pubsub_socket_transport, loop)

    task_foo = loop.create_task(foo(pubsub))
    loop.run_until_complete(task_foo)
    # loop.run_forever()

if __name__ == '__main__':
    main()
