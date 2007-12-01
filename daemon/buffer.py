try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import struct

# prefixed to all struct format strings
STRUCT_PREFIX = '!'

def hex (bytes) :
    return ' '.join(['%#04x' % ord(b) for b in bytes])
    
class NotEnoughDataError (Exception) : 
    pass

class IStreamBase (object) :
    # prefixed to all struct format strings
    STRUCT_PREFIX = '!'

class IReadStream (IStreamBase) :
    """
        IReadStream simply provides various interfaces for reading bytes from a
        stream in various ways
    """

    def read (self, size=None) :
        """
            Read and return up to the given amount of bytes, or all bytes
            available if no size given.
        """

        abstract

    def readStruct (self, fmt) :
        """
            Reads the correct amount of data and then unpacks it according to
            the given format. Note that this always returns a tuple, for single
            items, use readItem
        """
        
        fmt = self.STRUCT_PREFIX + fmt

        fmt_size = struct.calcsize(fmt)
        data = self.read(fmt_size)
        
        return struct.unpack(fmt, data)

    def readItem (self, fmt) :
        """
            Reads the correct amount of data, unpacks it according to the 
            given format, and then returns the first item.
        """

        return self.readStruct(fmt)[0]

    def readVarLen (self, len_type) :
        """
            Return the data part of a <length><data> structure.
            len_type indicates what type length has (struct format code).
        """
        
        size = self.readItem(len_type)
        
        if size :
            return self.read(size)
        else :
            return ""

    def readEnum (self, enum) :
        """
            Returns the item from the given list of enum values that corresponds
            to a single-byte value read from the stream
        """

        return enum[self.readItem('B')]

class ISeekableStream (IStreamBase) :
    """
        Extends IStreamBase to provide the ability to seek backwards into the
        stream (which still does not know it's length, and thence cannot seek
        forwards).
    """

    _position = None

    def tell (self) :
        """
            Return the current offset into the seekable stream
        """
        
        abstract

    def seek (self, pos) :
        """
            Seek to the given position in the stream. 
        """

        abstract

    def mark (self) :
        """
            Set a mark that can be later rolled back to with .reset()
        """
        
        self._position = self.tell()

    def unmark (self) :
        """
            Remove the mark without affecting the current position
        """
        
        self._position = None
    
    def reset (self) :
        """
            Rolls the buffer back to the position set earlier with mark()
        """
        
        if self._position is not None :
            self.seek(self._position)
            self._position = None

        else :
            raise Exception("reset() without mark()")

class ISeekableReadStream (ISeekableStream, IReadStream) :
    def peek (self, len=None) :
        """
            Return a string representing what buf.read(len) would return, but do
            not affect future read operations
        """

        pos = self.tell()

        data = self.read(len)

        self.seek(pos)
        
        return data
    

class INonBlockingReadStream (IReadStream) :
    """
        Otherwise identical to IReadStream, but read will either return size
        bytes, or raise a NotEnoughDataError
    """
    
    pass

class IWriteStream (IStreamBase) :
    """
        IWriteStream provides various ways to write data to a byte stream
    """

    def write (self, data) :
        """
            Write the given bytes to the stream
        """

        abstract

    def writeStruct (self, fmt, *args) :
        """
            Pack the given arguments with the given struct format, and write it
            to the stream.
        """

        self.write(struct.pack(self.STRUCT_PREFIX + fmt, *args))
        
    def writeVarLen (self, len_type, data) :
        """
            Write a <length><data> field into the buffer. Len_type is the
            struct format code for the length field.
        """

        self.writeStruct(len_type, len(data))
        self.write(data)

    def writeEnum (self, enum, name) :
        """
            Write the single-byte value correspnding to the given name's
            position in the given enum
        """

        self.writeStruct('B', enum.index(name))

class IBufferBase (ISeekableStream) :
    """
        A buffer simply provides a way to read and write data to/from a byte
        sequence stored in memory.
    """

    def tell (self) :
        return self._buf.tell()
    
    def seek (self, offset) :
        return self._buf.seek(offset)

    def getvalue (self) :
        """
            Returns the value of the buffer, i.e. a string with the contents of
            the buffer from position zero to the end.
        """

        return self._buf.getvalue()

class ReadBuffer (INonBlockingReadStream, ISeekableReadStream, IBufferBase) :
    """
       A read-only buffer. Can be initialized with a given value and then later
       replaced in various ways, but cannot be modified.
    """

    def __init__ (self, data="") :
        """
            Initialize the buffer with the given data
        """

        self._buf = StringIO(data)
    
    def read (self, size=None) :
        """
            Return the given number of bytes, or raise a NotEnoughDataError
        """

        if size == 0 :
            raise ValueError("can't read zero bytes")
         
        if size :
            ret = self._buf.read(size)
        else :
            ret = self._buf.read()

        if size and len(ret) < size :
            raise NotEnoughDataError()

        return ret    
    
    def append (self, data) :
        """
            Modify the buffer such that it contains the old data from this
            buffer, and the given data at the end. The read position in the buffer
            is kept the same.
        """

        pos = self.tell()

        self._buf = StringIO(self._buf.getvalue() + data)

        self.seek(pos)

    def chop (self) :
        """
            Discard the data in the buffer before the current read position.
            Also removes any marks.
        """

        self._position = None
        
        self._buf = StringIO(self.read())

    def processWith (self, func) :
        """
            Call the given function with this buffer as an argument after
            calling mark(). If the function 
                a) returns None, the buffer is .chop()'d, and we repeat the
                   process.
                b) raises a NotEnoughDataError, whereupon the buffer is rolled
                   back to where it was before calling the function with 
                   chop().
                c) raises a StopIteration, whereupon we chop the buffer and 
                   return.
                d) returns something (i.e. ret is not None), whereupon we
                   return that (and leave the current buffer position untouched).
        """
        ret = None
        
        try :
            while ret is None :
                self.mark()  # mark the position of the packet we are processing
                ret = func(self)

                if ret is None :
                    # discard the processed packet and proceed to the next one
                    self.chop()
                
        except NotEnoughDataError, e :
            self.reset() # reset position back to the start of the packet
            return e
            
        except StopIteration, e:
            self.chop()
            return e # processed ok, but we don't want to process any further packets
            
        else :
            return ret

class WriteBuffer (IWriteStream, IBufferBase) :
    """
        A write-only buffer. Data can be written to this buffer in various
        ways, but cannot be read from it except as a whole.
    """

    def __init__ (self) :
        """
            Initialize the buffer
        """

        self._buf = StringIO()

    def write (self, data) :
        """
            Write the given data to the current position in the stream,
            overwriting any previous data in that position, and extending
            the buffer if needed
        """

        return self._buf.write(data)
    
class BufferProtocol (object) :
    """
        A mixin to let you use Buffer with twisted.internet.protocol.Protocol
    """
    
    # a list of receivable command names 
    RECV_COMMANDS = None

    # a list of sendable command names
    SEND_COMMANDS = None

    def __init__ (self) :
        """
            Initialize the cross-dataReceived buffer
        """

        self.in_buffer = ReadBuffer()

    def send (self, buf) :
        """
            Write the contents of the given WriteBuffer to the transport
        """

        self.transport.write(buf.getvalue())

    def dataReceived (self, data) :
        """
            Buffer the incoming data and then try and process it
        """

        self.in_buffer.append(data)
        
        ret = self.in_buffer.processWith(self.processPacket)
        
    def processPacket (self, buf) :
        """
            Call processCommand with the buffer, handling the return value (either None or a deferred)
        """

        ret = self.processCommand(buf)

        if ret :
            ret.addCallback(self.send)

    def processCommand (self, buf) :
        """
            Process a command from the given buffer. May return a callback
        """

        return self.readMethod(buf, self.RECV_COMMANDS, buf)

    # conveniance read/write
    def startCommand (self, cmd) :
        buf = WriteBuffer()
        
        buf.writeEnum(self.SEND_COMMANDS, cmd)

        return buf
    
    def readMethod (self, buf, methods, *args, **kwargs) :
        """
            Reads a single-byte <methods>-enum value from the given buffer and
            use it to find the corresponding method (as <prefix>_<method-name>,
            prefix can be overriden with a keyword argument and defaults to
            'on'. If any extra arguments are given, they will be passed to the
            method.
        """

        prefix = kwargs.pop("prefix", "on")

        return getattr(self, "%s_%s" % (prefix, buf.readEnum(methods)))(*args, **kwargs)

