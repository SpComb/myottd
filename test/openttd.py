from twisted.internet import reactor, protocol, defer
from twisted.python import log

import rpc2
import rpc_test
import buffer

class Openttd (rpc2.RPCProtocol, protocol.ProcessProtocol) :
    RECV_COMMANDS = [x.strip() for x in """
        CMD_IN_NULL,
        CMD_IN_CONSOLE,
        CMD_IN_WARNING,
        CMD_IN_ERROR,
        CMD_IN_DEBUG,
        CMD_IN_NETWORK_EVENT,
        CMD_IN_PLAYERS_REPLY,
        CMD_IN_SCREENSHOT_REPLY,
        CMD_IN_ERROR_REPLY
    """.strip().split(',\n')]

    SEND_COMMANDS = [x.strip() for x in """
        CMD_OUT_NULL,
        CMD_OUT_CONSOLE_EXEC,
        CMD_OUT_PLAYERS,
        CMD_OUT_SCREENSHOT
    """.strip().split(',\n')]

    NETWORK_EVENTS = [x.strip() for x in """
        NETWORK_ACTION_JOIN,
        NETWORK_ACTION_LEAVE,
        NETWORK_ACTION_SERVER_MESSAGE,
        NETWORK_ACTION_CHAT,
        NETWORK_ACTION_CHAT_COMPANY,
        NETWORK_ACTION_CHAT_CLIENT,
        NETWORK_ACTION_GIVE_MONEY,
        NETWORK_ACTION_NAME_CHANGE
    """.strip().split(',\n')]    

    def __init__ (self) :
        super(Openttd, self).__init__()

        self._screenshot_deferred = None
        self.reqs = []
        
        args=['openttd', '-A', '-D', '192.168.11.11:8118', '-b', '8bpp-simple']
        reactor.spawnProcess(self, '/home/terom/my_ottd/openttd/trunk/bin/openttd', args=args, path='/home/terom/my_ottd/openttd/trunk/bin/', usePTY=False)

    def connectionMade (self) :
        log.msg("OpenTTD running...")
        
    def outReceived (self, data) :
        self.dataReceived(data)

    def errReceived (self, data) :
        log.msg("stderr: %s" % data)

    def processEnded (self, reason) :
        log.err(reason)

    def processCommand (self, buf) :
        method = buf.readEnum(self.RECV_COMMANDS)

        args = rpc2.readMany(buf)
        
        func = getattr(self, "rpc_%s" % method, None)

        if func :
            ret = None

            try :
                ret = func(*args)
            except Exception, e :
                self.error(e)
                raise

            if isinstance(ret, defer.Deferred) :
                ret.addErrback(self.error)
        else :
            print "Read %s:" % method

            for arg in args :
                print "\t%20s : %s" % (type(arg), arg)

            print
    
    def getScreenshot (self, x, y, width, height, zoom) :
        log.msg("%dx%d screenshot at (%d, %d), zoom level %d" % (width, height, x, y, zoom))
        return self.invoke("CMD_OUT_SCREENSHOT", x, y, width, height, zoom)
        
    def rpc_CMD_IN_SCREENSHOT_REPLY (self, chunks) :
        self._popCall().callback(''.join(chunks))

    def rpc_CMD_IN_ERROR_REPLY (self, msg) :
        self._popCall().errback(msg)

from twisted.web2 import http_headers, http, stream, responsecode, resource

class OpenttdImage (resource.Resource) :
    def __init__ (self, openttd) :
        self.openttd = openttd

    def render (self, r) :
        x = int(r.args['x'][0])
        y = int(r.args['y'][0])
        w = int(r.args['w'][0])
        h = int(r.args['h'][0])
        z = int(r.args['z'][0])

        d = self.openttd.getScreenshot(x, y, w, h, z)

        d.addCallback(self._respond)

        return d

    def _respond (self, image_data) :
        return http.Response(
            responsecode.OK,
            {
                'Content-Type': http_headers.MimeType('image', 'png'),

                # Not cacheable
                'Cache-Control': {'no-store': None},
                'Expires': 100,
            },
            stream.MemoryStream(image_data)
        )

