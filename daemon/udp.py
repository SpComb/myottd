import datetime
import socket

import construct as c
from twisted.internet import reactor, protocol, defer

class IpAddressAdapter (c.Adapter) :
    def _encode (self, obj, ctx) :
        return socket.inet_aton(obj)

    def _decode (self, obj, ctx) :
        return socket.inet_ntoa(obj)

def IpAddress (name) :
    return IpAddressAdapter(c.Bytes(name, 4))

class OpenTTD_DateAdapter (c.Adapter) :
    def _encode (self, obj, ctx) :
        raise Exception("negative, sir")

    def _decode (self, obj, ctx) :
        # openttd has 0 = Jan 1st 0AD/BC, fromordinal takes 1 = Jan 1st 1AD, and OpenTTD considers yr 0 to be a leap year
        try :
            return datetime.date.fromordinal(obj - 365)
        except ValueError :
            return datetime.date.max

def OpenTTD_OldDate (name) :
    return OpenTTD_DateAdapter(c.ULInt16(name))

def OpenTTD_NewDate (name) :
    return OpenTTD_DateAdapter(c.ULInt32(name))

class BinHex_Adapter (c.Adapter) :
    def _encode (self, obj, ctx) :
        return ''.join([chr(int(obj[o:o+2], 16)) for o in xrange(0, len(obj), 2)])

    def _decode (self, obj, ctx) :
        return ''.join(["%02x" % ord(x) for x in obj])

def GrfID (name) :
    return BinHex_Adapter(c.Bytes(name, 4))

def MD5 (name) :
    return BinHex_Adapter(c.Bytes(name, 16))

MAX_INFO_LEN          = 1024
MASTER_SERVER_PORT    = 3978   # The default port of the master server (UDP)
MASTER_SERVER_HOST    = "master.openttd.org"
MASTER_SERVER_MSG     = "OpenTTDRegister"
DEFAULT_PORT          = 3979   # The default port of the game server (TCP & UDP)

Header = c.Struct("header",
    c.ULInt16("size"),
    c.Enum(c.ULInt8("type"),
        UDP_CLIENT_FIND_SERVER=0,
        UDP_SERVER_RESPONSE=1,
        UDP_CLIENT_DETAIL_INFO=2,
        UDP_SERVER_DETAIL_INFO=3,
        UDP_SERVER_REGISTER=4,
        UDP_MASTER_ACK_REGISTER=5,
        UDP_CLIENT_GET_LIST=6,
        UDP_MASTER_RESPONSE_LIST=7,
        UDP_SERVER_UNREGISTER=8,
        UDP_CLIENT_GET_NEWGRFS=9,
        UDP_SERVER_NEWGRFS=10,
        UDP_END=11
    )
)

ServerList = c.Struct("serverlist",
    Header,
    c.ULInt8("version"),
    c.ULInt16("server_count"),
    c.MetaRepeater(lambda ctx: ctx["server_count"], c.Struct("servers",
        IpAddress("host"),
        c.ULInt16("port")
    )),
)

GameInfo = c.Struct("gameinfo",
    Header,
    c.ULInt8("version"),
    c.If(lambda ctx: ctx["version"] >= 4,
        c.Struct("newgrf_info",
            c.ULInt8("newgrf_count"),
            c.MetaRepeater(lambda ctx: ctx["newgrf_count"], c.Struct("newgrfs",
                GrfID("grfid"),
                MD5("md5"),
            ))
        )
    ),
    c.If(lambda ctx: ctx["version"] >= 3,
        c.Struct("ext_date",
            OpenTTD_NewDate("current"),
            OpenTTD_NewDate("start"),
        )
    ),
    c.If(lambda ctx: ctx["version"] >= 2,
        c.Struct("ext_limits",
            c.ULInt8("company_max"),
            c.ULInt8("company_current"),
            c.ULInt8("spectator_max")
        )
    ),
    c.If(lambda ctx: ctx["version"] >= 1,
        c.Struct("basic", 
            c.CString("name"),
            c.CString("revision"),
            c.Enum(c.ULInt8("language"),
                any=0,
                en=1,
                de=2,
                fr=3,
            ),
            c.ULInt8("has_password"),
            c.ULInt8("clients_max"),
            c.ULInt8("clients_current"),
            c.ULInt8("spectators_current"),
            c.If(lambda ctx: ctx["_"]["version"] < 3, c.Struct("old_date",
                OpenTTD_OldDate("current"),
                OpenTTD_OldDate("start"),
            )),
            c.CString("map_name"),
            c.ULInt16("map_width"),
            c.ULInt16("map_height"),
            c.Enum(c.ULInt8("map_type"),
                temperate=0,
                arctic=1,
                desert=2,
                toyland=3,
            ),
            c.ULInt8("dedicated"),
        )
    )
)

DetailInfo = c.Struct("detailinfo",
    Header,
    c.ULInt8("version"),
    c.ULInt8("player_count"),
    c.MetaRepeater(lambda ctx: ctx["player_count"], c.Struct("players",
        c.ULInt8("current"),
        c.CString("name"),
        c.ULInt32("inaugurated"),
        c.ULInt64("company_value"),
        c.ULInt64("balance"),
        c.ULInt64("income"),
        c.ULInt16("performance"),
        c.ULInt8("password"),
        c.Struct("vehicles",
            c.ULInt16("trains"),
            c.ULInt16("trucks"),
            c.ULInt16("busses"),
            c.ULInt16("planes"),
            c.ULInt16("ships"),
        ),
        c.Struct("stations",
            c.ULInt16("trains"),
            c.ULInt16("trucks"),
            c.ULInt16("busses"),
            c.ULInt16("planes"),
            c.ULInt16("ships"),
        ),
        c.ULInt8("has_clients"),
        c.If(lambda ctx: ctx["has_clients"] > 0,
            c.RepeatUntil(lambda obj, ctx: obj.more == 0, c.Struct("clients",
                c.CString("name"),
                c.CString("unique_id"),
                OpenTTD_NewDate("joined"),
                c.ULInt8("more"),
            )),
        ),
    )),
    c.ULInt8("has_spectators"),
    c.If(lambda ctx: ctx["has_spectators"] > 0,
        c.RepeatUntil(lambda obj, ctx: obj.more == 0, c.Struct("spectators",
            c.CString("name"),
            c.CString("unique_id"),
            OpenTTD_NewDate("joined"),
            c.ULInt8("more"),
        )),
    ),
)

NewGrfQuery = c.Struct("newgrfquery",
    Header,
    c.ULInt8("newgrf_count"),
    c.MetaRepeater(lambda ctx: ctx["newgrf_count"], c.Struct("newgrfs",
        GrfID("grfid"),
        MD5("md5"),
    ))
)

NewGrfInfo = c.Struct("newgrfinfo",
    Header,
    c.ULInt8("newgrf_count"),
    c.MetaRepeater(lambda ctx: ctx["newgrf_count"], c.Struct("newgrfs",
        GrfID("grfid"),
        MD5("md5"),
        c.CString("name"),
    )),
)


class Poller (protocol.DatagramProtocol) :
    def __init__ (self) :
        self.requests = {}

        self.masterserver_addr = None

        reactor.listenUDP(0, self)

    def datagramReceived (self, data, (host, port)) :
        self.log("%d bytes from %s:%s", len(data), host, port)

        if (host, port) in self.requests :
            type, d = self.requests[(host, port)]

            self.log("is a reply to a %s query" % type)

            type_func = getattr(self, 'got_%s' % type)

            type_func(data, d, (host, port))
        else :
            self.log("no request, ignoring")

    def deferred (self, type, host, port, timeout, addHostPort=True) :
        d = defer.Deferred()
        self.requests[(host, port)] = type, d

        d.setTimeout(timeout)
        
        if addHostPort :
            d.addErrback(self._reqTimeout, host, port)

        return d

    def _reqTimeout (self, err, host, port) :
        """
            Turn timeout errors into (host, port, None)
        """

        err.trap(defer.TimeoutError) 

        return host, port, None

    def getInfo (self, host, port) :
        self.log("sending info query to %s:%s", host, port)

        req = c.Container(type='UDP_CLIENT_FIND_SERVER', size=3)
        self.transport.write(Header.build(req), (host, port))
        
        return self.deferred('info', host, port, 2)

    def got_info (self, data, d, (host, port)) :
        game_info = GameInfo.parse(data)

        d.callback((host, port, game_info))

    def getServers (self) :
        if self.masterserver_addr :
            return self._getServers_haveAddr(self.masterserver_addr)
        else :
            self.log("resolving masterserver address...")
            return reactor.resolve(MASTER_SERVER_HOST).addCallback(self._getServers_haveAddr)

    def _getServers_haveAddr (self, host) :
        self.log("getting server list from masterserver (%s)", host)

        req = c.Container(type='UDP_CLIENT_GET_LIST', size=3)
        self.transport.write(Header.build(req), (host, MASTER_SERVER_PORT))

        return self.deferred('servers', host, MASTER_SERVER_PORT, 10, False)
    
    def got_servers (self, data, d, (host, port)) :
        servers = ServerList.parse(data)
        
        d.callback(servers)

    def getDetails (self, host, port) :
        self.log("sending details query to %s:%s", host, port)

        req = c.Container(type='UDP_CLIENT_DETAIL_INFO', size=3)
        self.transport.write(Header.build(req), (host, port))
        
        return self.deferred('detail', host, port, 2)

    def got_detail (self, data, d, (host, port)) :
        details = DetailInfo.parse(data)

        d.callback((host, port, details))

    def getNewGrfs (self, host, port, grf_list) :
        self.log("sending newgrfs query to %s:%s for: %s", host, port, grf_list)

        header = c.Container(type='UDP_CLIENT_GET_NEWGRFS', size=4+(20)*len(grf_list))
        req = c.Container(header=header, newgrf_count=len(grf_list), newgrfs=grf_list)
        self.transport.write(NewGrfQuery.build(req), (host, port))
        
        return self.deferred('newgrf', host, port, 2)

    def got_newgrf (self, data, d, (host, port)) :
        newgrfs = NewGrfInfo.parse(data)

        d.callback((host, port, newgrfs))

    def log (self, msg, *params) :
        if params :
            msg = msg % params

        print 'udp: %s' % (msg, )

def main () :
    poller = Poller()

    host, port = "88.198.193.138", 3979
    
    poller.getInfo(host, port).addCallback(_main_gotInfo, poller)

def _main_gotInfo ((host, port, info), poller) :
    print info

    poller.getDetails(host, port).addCallback(_main_gotDetails, poller, info)
    
    #poller.getServers().addCallback(_main_gotServers, poller)

def _main_gotServers (servers, poller) :
    ds = []

    for server in servers.servers :
        print '%s:%d' % (server.host, server.port)
        ds.append(poller.getInfo(server.host, server.port))

    defer.DeferredList(ds).addCallback(_main_gotInfos, poller)

def _main_gotInfos (infos, poller) :
    get_details_from = None

    for status, (host, port, info) in infos :
        if status and info :
            print "%s:%d: %s - %dx%d - %s - " % (host, port, info.basic.name, info.basic.map_width, info.basic.map_height, info.basic.revision),

            if info.ext_date :
                get_details_from = host, port, info
                print "date:[%s @ %s]" % (info.ext_date.start, info.ext_date.current)
            else :
                print "olddate:[%s @ %s]" % (info.basic.old_date.start, info.basic.old_date.current)
        else :
            print "%s:%d: failed" % (host, port)
    
    poller.getDetails(*get_details_from[:2]).addCallback(_main_gotDetails, poller, get_details_from[2])

def _main_gotDetails ((host, port, details), poller, info) :
    print details

    poller.getNewGrfs(host, port, info.newgrf_info.newgrfs).addCallback(_main_gotNewgrfs, poller, info, details)

def _main_gotNewgrfs ((host, port, newgrfs), poller, info, details) :
    print newgrfs

    reactor.stop()

if __name__ == '__main__' :
    reactor.callWhenRunning(main)
    reactor.run()

