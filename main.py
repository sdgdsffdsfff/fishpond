import asyncio
import selectors
import redis


def add_reader(self, fd, callback, *args):
        """Add a reader callback."""
        self._check_closed()
        handle = events.Handle(callback, args, self)
        try:
            key = self._selector.get_key(fd)
        except KeyError:
            self._selector.register(fd, selectors.EVENT_READ,
                                    (handle, None))
        else:
            mask, (reader, writer) = key.events, key.data
            self._selector.modify(fd, mask | selectors.EVENT_READ,
                                  (handle, writer))
            if reader is not None:
                reader.cancel()

loop = asyncio.get_event_loop()

r = redis.StrictRedis()

sub = r.subscribe('test')
