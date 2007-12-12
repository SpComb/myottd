# -*- test-case-name: twisted.test.test_memcache -*-
# Copyright (c) 2007 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Memcache client protocol. Memcached is a caching server, storing data in the
form of pairs key/value, and memcache is the protocol to talk with it.

To connect to a server, create a factory for L{MemCacheProtocol}::

    from twisted.internet import reactor, protocol
    from twisted.protocols.memcache import MemCacheProtocol, DEFAULT_PORT
    d = protocol.ClientCreator(reactor, MemCacheProtocol
        ).connectTCP("localhost", DEFAULT_PORT)
    def doSomething(proto):
        # Here you call the memcache operations
        return proto.set("mykey", "a lot of data")
    d.addCallback(doSomething)
    reactor.run()

All the operations of the memcache protocol are present, but
L{MemCacheProtocol.set} and L{MemCacheProtocol.get} are the more important.

See U{http://code.sixapart.com/svn/memcached/trunk/server/doc/protocol.txt} for
more information about the protocol.
"""

try:
    from collections import deque
except ImportError:
    class deque(list):
        def popleft(self):
            return self.pop(0)


from twisted.protocols.basic import LineReceiver
from twisted.protocols.policies import TimeoutMixin
from twisted.internet.defer import Deferred, fail, TimeoutError
from twisted.python import log



DEFAULT_PORT = 11211



class NoSuchCommand(Exception):
    """
    Exception raised when a non existent command is called.
    """



class ClientError(Exception):
    """
    Error caused by an invalid client call.
    """



class ServerError(Exception):
    """
    Problem happening on the server.
    """



class Command(object):
    """
    Wrap a client action into an object, that holds the values used in the
    protocol.

    @ivar _deferred: the L{Deferred} object that will be fired when the result
        arrives.
    @type _deferred: L{Deferred}

    @ivar command: name of the command sent to the server.
    @type command: C{str}
    """

    def __init__(self, command, **kwargs):
        """
        Create a command.

        @param command: the name of the command.
        @type command: C{str}

        @param kwargs: this values will be stored as attributes of the object
            for future use
        """
        self.command = command
        self._deferred = Deferred()
        for k, v in kwargs.items():
            setattr(self, k, v)


    def success(self, value):
        """
        Shortcut method to fire the underlying deferred.
        """
        self._deferred.callback(value)


    def fail(self, error):
        """
        Make the underlying deferred fails.
        """
        self._deferred.errback(error)



class MemCacheProtocol(LineReceiver, TimeoutMixin):
    """
    MemCache protocol: connect to a memcached server to store/retrieve values.

    @ivar persistentTimeOut: the timeout period used to wait for a response.
    @type persistentTimeOut: C{int}

    @ivar _current: current list of requests waiting for an answer from the
        server.
    @type _current: C{deque} of L{Command}

    @ivar _lenExpected: amount of data expected in raw mode, when reading for
        a value.
    @type _lenExpected: C{int}

    @ivar _getBuffer: current buffer of data, used to store temporary data
        when reading in raw mode.
    @type _getBuffer: C{list}

    @ivar _bufferLength: the total amount of bytes in C{_getBuffer}.
    @type _bufferLength: C{int}
    """
    MAX_KEY_LENGTH = 250

    def __init__(self, timeOut=60):
        """
        Create the protocol.

        @param timeOut: the timeout to wait before detecting that the
            connection is dead and close it. It's expressed in seconds.
        @type timeOut: C{int}
        """
        self._current = deque()
        self._lenExpected = None
        self._getBuffer = None
        self._bufferLength = None
        self.persistentTimeOut = self.timeOut = timeOut


    def timeoutConnection(self):
        """
        Close the connection in case of timeout.
        """
        for cmd in self._current:
            cmd.fail(TimeoutError("Connection timeout"))
        self.transport.loseConnection()


    def sendLine(self, line):
        """
        Override sendLine to add a timeout to response.
        """
        if not self._current:
           self.setTimeout(self.persistentTimeOut)
        LineReceiver.sendLine(self, line)


    def rawDataReceived(self, data):
        """
        Collect data for a get.
        """
        self.resetTimeout()
        self._getBuffer.append(data)
        self._bufferLength += len(data)
        if self._bufferLength >= self._lenExpected + 2:
            data = "".join(self._getBuffer)
            buf = data[:self._lenExpected]
            rem = data[self._lenExpected + 2:]
            val = buf
            self._lenExpected = None
            self._getBuffer = None
            self._bufferLength = None
            cmd = self._current[0]
            cmd.value = val
            self.setLineMode(rem)


    def cmd_STORED(self):
        """
        Manage a success response to a set operation.
        """
        self._current.popleft().success(True)


    def cmd_NOT_STORED(self):
        """
        Manage a specific 'not stored' response to a set operation: this is not
        an error, but some condition wasn't met.
        """
        self._current.popleft().success(False)


    def cmd_END(self):
        """
        This the end token to a get or a stat operation.
        """
        cmd = self._current.popleft()
        if cmd.command == "get":
            cmd.success((cmd.flags, cmd.value))
        elif cmd.command == "stats":
            cmd.success(cmd.values)


    def cmd_NOT_FOUND(self):
        """
        Manage error response for incr/decr/delete.
        """
        self._current.popleft().success(False)


    def cmd_VALUE(self, line):
        """
        Prepare the reading a value after a get.
        """
        key, flags, length = line.split()
        self._lenExpected = int(length)
        self._getBuffer = []
        self._bufferLength = 0
        cmd = self._current[0]
        if cmd.key != key:
            raise RuntimeError("Unexpected commands answer.")
        cmd.flags = int(flags)
        cmd.length = self._lenExpected
        self.setRawMode()


    def cmd_STAT(self, line):
        """
        Reception of one stat line.
        """
        cmd = self._current[0]
        key, val = line.split(" ", 1)
        cmd.values[key] = val


    def cmd_VERSION(self, versionData):
        """
        Read version token.
        """
        self._current.popleft().success(versionData)


    def cmd_ERROR(self):
        """
        An non-existent command has been sent.
        """
        log.err("Non-existent command sent.")
        cmd = self._current.popleft()
        cmd.fail(NoSuchCommand())


    def cmd_CLIENT_ERROR(self, errText):
        """
        An invalid input as been sent.
        """
        log.err("Invalid input: %s" % (errText,))
        cmd = self._current.popleft()
        cmd.fail(ClientError(errText))


    def cmd_SERVER_ERROR(self, errText):
        """
        An error has happened server-side.
        """
        log.err("Server error: %s" % (errText,))
        cmd = self._current.popleft()
        cmd.fail(ServerError(errText))


    def cmd_DELETED(self):
        """
        A delete command has completed successfully.
        """
        self._current.popleft().success(True)


    def cmd_OK(self):
        """
        The last command has been completed.
        """
        self._current.popleft().success(True)


    def lineReceived(self, line):
        """
        Receive line commands from the server.
        """
        self.resetTimeout()
        token = line.split(" ", 1)[0]
        # First manage standard commands without space
        cmd = getattr(self, "cmd_%s" % (token,), None)
        if cmd is not None:
            args = line.split(" ", 1)[1:]
            if args:
                cmd(args[0])
            else:
                cmd()
        else:
            # Then manage commands with space in it
            line = line.replace(" ", "_")
            cmd = getattr(self, "cmd_%s" % (line,), None)
            if cmd is not None:
                cmd()
            else:
                # Increment/Decrement response
                cmd = self._current.popleft()
                val = int(line)
                cmd.success(val)
        if not self._current:
            # No pending request, remove timeout
            self.setTimeout(None)


    def increment(self, key, val=1):
        """
        Increment the value of C{key} by given value (default to 1).
        C{key} must be consistent with an int. Return the new value.

        @param key: the key to modify.
        @type key: C{str}

        @param val: the value to increment.
        @type val: C{int}

        @return: a deferred with will be called back with the new value
            associated with the key (after the increment).
        @rtype: L{Deferred}
        """
        return self._incrdecr("incr", key, val)


    def decrement(self, key, val=1):
        """
        Decrement the value of C{key} by given value (default to 1).
        C{key} must be consistent with an int. Return the new value, coerced to
        0 if negative.

        @param key: the key to modify.
        @type key: C{str}

        @param val: the value to decrement.
        @type val: C{int}

        @return: a deferred with will be called back with the new value
            associated with the key (after the decrement).
        @rtype: L{Deferred}
        """
        return self._incrdecr("decr", key, val)


    def _incrdecr(self, cmd, key, val):
        """
        Internal wrapper for incr/decr.
        """
        if not isinstance(key, str):
            return fail(ClientError(
                "Invalid type for key: %s, expecting a string" % (type(key),)))
        if len(key) > self.MAX_KEY_LENGTH:
            return fail(ClientError("Key too long"))
        fullcmd = "%s %s %d" % (cmd, key, int(val))
        self.sendLine(fullcmd)
        cmdObj = Command(cmd, key=key)
        self._current.append(cmdObj)
        return cmdObj._deferred


    def replace(self, key, val, flags=0, expireTime=0):
        """
        Replace the given C{key}. It must already exist in the server.

        @param key: the key to replace.
        @type key: C{str}

        @param val: the new value associated with the key.
        @type val: C{str}

        @param flags: the flags to store with the key.
        @type flags: C{int}

        @param expireTime: if different from 0, the relative time in seconds
            when the key will be deleted from the store.
        @type expireTime: C{int}

        @return: a deferred that will fire with C{True} if the operations has
            succeeded, and C{False} with the key didn't previously exist.
        @rtype: L{Deferred}
        """
        return self._set("replace", key, val, flags, expireTime)


    def add(self, key, val, flags=0, expireTime=0):
        """
        Add the given C{key}. It must not exist in the server.

        @param key: the key to add.
        @type key: C{str}

        @param val: the value associated with the key.
        @type val: C{str}

        @param flags: the flags to store with the key.
        @type flags: C{int}

        @param expireTime: if different from 0, the relative time in seconds
            when the key will be deleted from the store.
        @type expireTime: C{int}

        @return: a deferred that will fire with C{True} if the operations has
            succeeded, and C{False} with the key already exists.
        @rtype: L{Deferred}
        """
        return self._set("add", key, val, flags, expireTime)


    def set(self, key, val, flags=0, expireTime=0):
        """
        Set the given C{key}.

        @param key: the key to replace.
        @type key: C{str}

        @param val: the value associated with the key.
        @type val: C{str}

        @param flags: the flags to store with the key.
        @type flags: C{int}

        @param expireTime: if different from 0, the relative time in seconds
            when the key will be deleted from the store.
        @type expireTime: C{int}

        @return: a deferred that will fire with C{True} if the operations has
            succeeded.
        @rtype: L{Deferred}
        """
        return self._set("set", key, val, flags, expireTime)


    def _set(self, cmd, key, val, flags, expireTime):
        """
        Internal wrapper for setting values.
        """
        if not isinstance(key, str):
            return fail(ClientError(
                "Invalid type for key: %s, expecting a string" % (type(key),)))
        if len(key) > self.MAX_KEY_LENGTH:
            return fail(ClientError("Key too long"))
        if not isinstance(val, str):
            return fail(ClientError(
                "Invalid type for value: %s, expecting a string" %
                (type(val),)))
        length = len(val)
        fullcmd = "%s %s %d %d %d" % (cmd, key, flags, expireTime, length)
        self.sendLine(fullcmd)
        self.sendLine(val)
        cmdObj = Command(cmd, key=key, flags=flags, length=length)
        self._current.append(cmdObj)
        return cmdObj._deferred


    def get(self, key):
        """
        Get the given C{key}. It doesn't support multiple keys.

        @param key: the key to retrieve.
        @type key: C{str}

        @return: a deferred that will fire with the tuple (flags, value).
        @rtype: L{Deferred}
        """
        if not isinstance(key, str):
            return fail(ClientError(
                "Invalid type for key: %s, expecting a string" % (type(key),)))
        if len(key) > self.MAX_KEY_LENGTH:
            return fail(ClientError("Key too long"))
        fullcmd = "get %s" % key
        self.sendLine(fullcmd)
        cmdObj = Command("get", key=key, value=None, flags=0)
        self._current.append(cmdObj)
        return cmdObj._deferred


    def stats(self):
        """
        Get some stats from the server. It will be available as a dict.

        @return: a deferred that will fire with a C{dict} of the available
            statistics.
        @rtype: L{Deferred}
        """
        self.sendLine("stats")
        cmdObj = Command("stats", values={})
        self._current.append(cmdObj)
        return cmdObj._deferred


    def version(self):
        """
        Get the version of the server.

        @return: a deferred that will fire with the string value of the
            version.
        @rtype: L{Deferred}
        """
        self.sendLine("version")
        cmdObj = Command("version")
        self._current.append(cmdObj)
        return cmdObj._deferred


    def delete(self, key):
        """
        Delete an existing C{key}.

        @param key: the key to delete.
        @type key: C{str}

        @return: a deferred that will be called back with C{True} if the key
            was successfully deleted, or C{False} if not.
        @rtype: L{Deferred}
        """
        if not isinstance(key, str):
            return fail(ClientError(
                "Invalid type for key: %s, expecting a string" % (type(key),)))
        self.sendLine("delete %s" % key)
        cmdObj = Command("delete", key=key)
        self._current.append(cmdObj)
        return cmdObj._deferred


    def flushAll(self):
        """
        Flush all cached values.

        @return: a deferred that will be called back with C{True} when the
            operation has succeeded.
        @rtype: L{Deferred}
        """
        self.sendLine("flush_all")
        cmdObj = Command("flush_all")
        self._current.append(cmdObj)
        return cmdObj._deferred



__all__ = ["MemCacheProtocol", "DEFAULT_PORT", "NoSuchCommand", "ClientError",
           "ServerError"]

