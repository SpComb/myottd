from twisted.internet import protocol

class RPCProtocol (protocol.Protocol) :
    RECV_COMMANDS = SEND_COMMANDS = [
        'call',
        'return',
        'error',
    ]

    METHODS = [

    ]

    def __init__ (self) :
        self.calls = []


    def do_call (self, method, *args) :
        o = self.startCommand('call')
        
        o.writeEnum(self.METHODS, method)
        self._write_list(o, args)

        self.send(o)

        d = defer.Deferred()

        self.calls.append(d)

        return d

    def on_call (self, i) :
        method = i.readEnum(self.METHODS)
        
        args = self._read_list(i)

        func = getattr(self, "rpc_%s" % method)
        
        try :
            func(*args)
        except Exception, e :
            self.do_error(e)
            raise

        if isinstance(ret, defer.Deferred) :
            ret.addCallback(self.do_return).addErrback(self.do_error)
        else :
            self.do_return(ret)
            
    def do_return (self, value) :
        o = self.startCommand('return')

        self._write_item(o, value)

        self.send(o)

    def do_error (self, error) :
        o = self.startCommand('error')

        self._write_item(o, str(error))

        self.send(o)

    def on_return (self, i) :
        value = self._read_item(i)

        self.calls.pop(0).callback(value)
    
    def on_error (self, i) :
        value = self._read_item(i)

        self.calls.pop(0).errback(value)

def _write_list (buf, items) :
    buf.writeStruct('B', len(items))

    for item in items :
        _write_item(buf, item)

def _write_item (buf, arg) :
    if isinstance(arg, int) :
        if arg >= 0 :
            if arg < 2**8 :
                type = 'B'
            elif arg < 2**16 :
                type = 'H'
            elif arg < 2**32 :
                type = 'I'
            else :
                raise ValueError("Integer %d is too large" % arg)
        else :
            raise ValueError("Signed integers like %s are not yet supported" % arg)

        buf.write(type)   
        buf.writeStruct(type, arg)

    elif isinstance(arg, basestring) :
        if isinstance(arg, unicode) :
            arg = arg.encode('utf8')

        if len(arg) < 2**8 :
            type = 'B'
        elif len(arg) < 2**16 :
            type = 'H'
        elif len(arg) < 2**32 :
            type = 'I'
        else :
            raise ValueError("String of length %d is too long" % len(arg))

        buf.write('S')
        buf.write(type)
        buf.writeVarLen(type, arg)
    
    elif isinstance(arg, (tuple, list, dict)) :
        if isinstance(arg, dict) :
            arg = arg.iteritems()

        buf.write("X")
        _write_list(buf, arg)
    
    elif isinstance(arg, bool) :
        buf.write("x")
        buf.writeStruct('B', bool)

    elif arg is None :
        buf.write(" ")

    else :
        raise ValueError("Don't know how to handle argument of type %s" % type(arg))

def _read_list (i) :
    num_args, = i.readStruct('B')

    args = []

    for x in xrange(num_args) :
        item = _read_item(i)

        args.append(item)
    
    return args

def _read_item (i) : 
    type = i.readAll(1)

#    print "Read type %r" % type

    if type == 'x' :
        value = bool(i.readStruct('B'))

    elif type == 'X' :
        value = _read_list(i)

    elif type == 'S' :
        strType = i.readAll(1)

#        print "Str type %r" % strType

        value = i.readVarLen(strType)

    elif type == ' ' :
        value = None

    elif type == '(' :
        # variable-length list
        value = []
        
        while True :
            try :
                value.append(_read_item(i))
            except StopIteration :
                break
    
    elif type == ')' :
        raise StopIteration()

    else :
        value, = i.readStruct(type)
    
    return value

