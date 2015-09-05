import asyncio
import selectors
import redis


def _make_socket_transport(self, sock, protocol, waiter=None, *,
                           extra=None, server=None):
    return _RedisSelectorSocketTransport(self, sock, protocol, waiter,
                                         extra, server)


class _RedisSelectorSocketTransport(_SelectorSocketTransport):

    def __init__(self, loop, sock, protocol, waiter=None,
                 extra=None, server=None):
        super().__init__(loop, sock, protocol, extra, server)
        self._eof = False
        self._paused = False

        self._loop.call_soon(self._protocol.connection_made, self)
        # only start reading when connection_made() has been called
        self._loop.call_soon(self._loop.add_reader,
                             self._sock_fd, self._read_ready)
        if waiter is not None:
            # only wake up the waiter when connection_made() has been called
            self._loop.call_soon(waiter._set_result_unless_cancelled, None)

    def _read_ready(self):
        # 重写
        try:
            data = self._sock.recv(self.max_size)
        except (BlockingIOError, InterruptedError):
            pass
        except Exception as exc:
            self._fatal_error(exc, 'Fatal read error on socket transport')
        else:
            if data:
                self._protocol.data_received(data)
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

sub = redis.StrictRedis().subscribe('test')


loop = asyncio.get_event_loop()
loop._make_socket_transport = _make_socket_transport


async def foo():
    reader, writer = await asyncio.open_connection(sock=sub.connection._sock, loop=loop)
    while not reader._eof:
        message = reader.read(256)
        print('message: {}'.format(message.decode()))
