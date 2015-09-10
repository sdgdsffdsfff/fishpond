import asyncio
import selectors
import types
from asyncio.selector_events import _SelectorSocketTransport
from asyncio.log import logger

import redis


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
            return
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

pubsub = redis.StrictRedis('172.100.102.101').pubsub()
pubsub.subscribe('test')


loop = asyncio.get_event_loop()
loop.set_debug(True)
loop._make_socket_transport = types.MethodType(_make_pubsub_socket_transport, loop)


async def foo(pubsub):
    reader, writer = await asyncio.open_connection(sock=pubsub.connection._sock, loop=loop)
    reader._transport._pubsub = pubsub
    for i in range(2):
        message = await reader.read(256)
        print('message: {}, type:{}'.format(message.decode(), type(message)))
    return
