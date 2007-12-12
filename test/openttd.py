from twisted.internet import reactor, protocol, defer
from twisted.python import log

import rpc2
import rpc_test
import buffer

import simplejson
#import imagetiles

def enum (data) : return [x.strip() for x in data.strip("\n\t ,").split(',\n')]

class Openttd (rpc2.RPCProtocol, protocol.ProcessProtocol) :
    RECV_COMMANDS = enum("""
        CMD_IN_NULL,
        CMD_IN_CONSOLE,
        CMD_IN_WARNING,
        CMD_IN_ERROR,
        CMD_IN_DEBUG,
        CMD_IN_NETWORK_EVENT,
        CMD_IN_PLAYERS_REPLY,
        CMD_IN_SCREENSHOT_REPLY,
        CMD_IN_ERROR_REPLY,
        CMD_IN_VEHICLES_REPLY,
        CMD_IN_SAVELOAD_REPLY,
    """)

    SEND_COMMANDS = enum("""
        CMD_OUT_NULL,
        CMD_OUT_CONSOLE_EXEC,
        CMD_OUT_PLAYERS,
        CMD_OUT_SCREENSHOT,
        CMD_OUT_VEHICLE_SCREENSHOT,
        CMD_OUT_VEHICLES,
        CMD_OUT_VEHICLE_SPRITE,
        CMD_OUT_SAVELOAD,
    """)

    NETWORK_EVENTS = enum("""
        NETWORK_ACTION_JOIN,
        NETWORK_ACTION_LEAVE,
        NETWORK_ACTION_SERVER_MESSAGE,
        NETWORK_ACTION_CHAT,
        NETWORK_ACTION_CHAT_COMPANY,
        NETWORK_ACTION_CHAT_CLIENT,
        NETWORK_ACTION_GIVE_MONEY,
        NETWORK_ACTION_NAME_CHANGE
    """)
    
    VEHICLE_TYPES = enum("""
        VEH_TRAIN,
        VEH_ROAD,
        VEH_SHIP,
        VEH_AIRCRAFT,
        VEH_SPECIAL,
        VEH_DISASTER,
    """)

    VEHICLE_TYPE_NAMES = enum("""
        Train,
        Road,
        Ship,
        Aircraft,
    """)

    SAVELOAD_MODE = enum("""

    """)
        


    def __init__ (self) :
        super(Openttd, self).__init__()

        self._screenshot_deferred = None
        self.reqs = []
        
        args=['openttd', '-A', '-D', '192.168.11.11:7199', '-b', '8bpp-simple']
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
#                self.error(e)
                raise

#            if isinstance(ret, defer.Deferred) :
#                ret.addErrback(self.error)
        else :
            print "Read %s:" % method

            for arg in args :
                print "\t%20s : %s" % (type(arg), arg)

            print
    
    def getScreenshot (self, x, y, width, height, zoom) :
        log.msg("%dx%d screenshot at (%d, %d), zoom level %d" % (width, height, x, y, zoom))
        return self.invoke("CMD_OUT_SCREENSHOT", x, y, width, height, zoom)

    def getVehicleScreenshot (self, veh_id, width, height, zoom) :
        log.msg("%dx%d screenshot of vehicle %d, zoom level %d" % (width, height, veh_id, zoom))
        return self.invoke("CMD_OUT_VEHICLE_SCREENSHOT", veh_id, width, height, zoom)

    def getVehicleList (self) :
        log.msg("fetch vehicle list")
        return self.invoke("CMD_OUT_VEHICLES")

    def getVehicleSprite (self, veh_id) :
        log.msg("fetch vehicle %d sprite" % veh_id)
        return self.invoke("CMD_OUT_VEHICLE_SPRITE", veh_id)
        
    def rpc_CMD_IN_SCREENSHOT_REPLY (self, chunks) :
        self._popCall().callback(''.join(chunks))

    def rpc_CMD_IN_ERROR_REPLY (self, msg) :
        self._popCall().errback(msg)

    def rpc_CMD_IN_VEHICLES_REPLY (self, vehicles) :
        self._popCall().callback([dict(
            id      = id, 
            type    = self.VEHICLE_TYPE_NAMES[type],
            x       = x,
            y       = y,
            profit_this_year    = profit_this_year,
            profit_last_year    = profit_last_year,
        ) for (id, type, x, y, profit_this_year, profit_last_year) in vehicles])

from twisted.web2 import http_headers, http, stream, responsecode, resource

class Tile (resource.Resource) :
    def __init__ (self, openttd) :
        self.openttd = openttd

    def render (self, r) :
        z = int(r.args['z'][0])
        
        if 'r' in r.args and 'c' in r.args :
            w, h = imagetiles.TILE_SIZE

            r = int(r.args['r'][0])
            c = int(r.args['c'][0])
            
            x = c * w
            y = r * h

            d = self.openttd.getScreenshot(x, y, w, h, z)

        else :
            w = int(r.args['w'][0])
            h = int(r.args['h'][0])

            if 'v' in r.args :
                v = int(r.args['v'][0])

                d = self.openttd.getVehicleScreenshot(v, w, h, z)

            else :
                x = int(r.args['x'][0])
                y = int(r.args['y'][0])

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

class Vehicles (resource.Resource) :
    def __init__ (self, openttd) :
        self.openttd = openttd

    def render (self, r) :
        d = self.openttd.getVehicleList()

        d.addCallback(self._respond)

        return d

    def _respond (self, vehicles) :
        json = simplejson.dumps(vehicles)

        r = http.Response(
            responsecode.OK,
            {
                'Content-Type': http_headers.MimeType('text', 'javascript'),

                # Not cacheable
                'Cache-Control': {'no-store': None},
                'Expires': 100,
            },
            stream.MemoryStream(json)
        )
        
        r.headers.addRawHeader('X-JSON', json)
        
        return r

class VehicleSprite (resource.Resource) :
    def __init__ (self, openttd) :
        self.openttd = openttd

    def render (self, r) :
        v = int(r.args['v'][0])

        d = self.openttd.getVehicleSprite(v)

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

def startup (root) :
    ottd = Openttd()
    root.putChild("tile", Tile(ottd))
    root.putChild("vehicles", Vehicles(ottd))
    root.putChild("sprite", VehicleSprite(ottd))

