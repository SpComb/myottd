from twisted.web import resource, server
from twisted.internet import protocol, reactor, defer
import simplejson
import traceback

import settings
import main

def writeRequest (request, type, subtype, data) :
    """
    Write a [type, data] tuple/list to the request, setting content-type to application/json
    """
    request.setHeader('Content-Type', 'text/plain')
    
    json = simplejson.dumps((type, subtype, data))
    
    request.setHeader('X-JSON', json)

    request.write(json)  # should be a str, not unicode
    
    request.finish()
    
def error (request, type, value) :
    """
    Write an error of type <type> and value <value>
    """
    
    writeRequest(request, 'error', type, value)
    
def reply (request, type, params) :
    """
    Write a reply of type <type> with params <param> (which should be a dict)
    """
    
    writeRequest(request, 'reply', type, params)

class RpcResource (resource.Resource) :
    isLeaf = True

    def __init__ (self, main) :
        self.main = main

        resource.Resource.__init__(self)

    def render_GET (self, request) :
        try :
            self.render_RPC(request, **dict((k, simplejson.loads(request.args[k][0])) for k in request.args))
        except Exception, e :
            error(request, e.__class__.__name__, str(e))
            print "Error in http_api:"
            traceback.print_exc()
            
        return server.NOT_DONE_YET
        
    def render_RPC (self, req, **kwargs) :
        """
            This is the method that you implement
        """
        
    def failure (self, failure, request) :
        error(request, failure.type.__name__, str(failure.value))
        
        return failure

class StartQuery (RpcResource) :
    def render_RPC (self, request, id, sg=None) :
        defer.maybeDeferred(self.main.startServer, int(id), sg).addCallback(self.started, request).addErrback(self.failure, request)

    def started (self, ret, request) :
        reply(request, 'start', 'ok')

class StopQuery (RpcResource) :
    def render_RPC (self, request, id) :
        defer.maybeDeferred(self.main.stopServer, int(id)).addCallback(self.stopped, request).addErrback(self.failure, request)

    def stopped (self, ret, request) :
        reply(request, 'stop', 'ok')

class RestartQuery (RpcResource) :
    def render_RPC (self, request, id, sg) :
        defer.maybeDeferred(self.main.restartServer, int(id), sg).addCallback(self.restarted, request).addErrback(self.failure, request)

    def restarted (self, ret, request) :
        reply(request, 'restart', 'ok')

class ServersQuery (RpcResource) :
    def render_RPC (self, request) :
        deferreds = []

        for server in self.main.servers.itervalues() :
            deferreds.append(server.getServerOverview())
        
        defer.DeferredList(deferreds).addCallback(self._gotInfos, request)

    def _gotInfos (self, infos, request) :
        reply(request, 'servers', [info for status, info in infos if status])

class ServerInfoQuery (RpcResource) :
    def render_RPC (self, request, id) :
        self.main.servers[int(id)].getServerDetails().addCallback(self._gotDetails, request).addErrback(self.failure, request)

    def _gotDetails (self, res, request) :
        reply(request, 'server_info', res)

class SaveGameQuery (RpcResource) :
    def render_RPC (self, r, id) :
        self.main.servers[int(id)].saveGame().addCallback(self._done, r).addErrback(self.failure, r)

    def _done (self, res, r) :
        reply(r, 'save_game', res)

class LoadGameQuery (RpcResource) :
    def render_RPC (self, r, id, game, save=None) :
        id = int(id)
        game = int(game)

        self.main.servers[id].loadGame(game, save).addCallback(self._done, r).addErrback(self.failure, r)

    def _done (self, res, r) :
        reply(r, 'load_game', res)

class ConfigQuery (RpcResource) :
    def render_RPC (self, r, id) :
        reply(r, 'config', self.main.servers[int(id)].getConfig())

class ConfigApplyQuery (RpcResource) :
    def render_RPC (self, r, id, config, start_new=False) :
        self.main.servers[int(id)].applyConfig(config, bool(start_new)).addCallback(self._done, r).addErrback(self.failure, r)

    def _done (self, res, r) :
        reply(r, 'config_apply', res)

class DebugQuery (RpcResource) :
    def render_RPC (self, request) :
        reply(request, 'reload', {'id': id(self.main.servers), 'value': self.main.servers})

class Site (server.Site) :
    def __init__ (self, main) :
        self.main = main

        root = self.root = resource.Resource()

        root.putChild('start', StartQuery(main))
        root.putChild('stop', StopQuery(main))
        root.putChild('restart', RestartQuery(main))
        root.putChild('debug', DebugQuery(main))
        root.putChild('servers', ServersQuery(main))
        root.putChild('server_info', ServerInfoQuery(main))
        root.putChild('save_game', SaveGameQuery(main))
        root.putChild('load_game', LoadGameQuery(main))
        root.putChild('config', ConfigQuery(main))
        root.putChild('config_apply', ConfigApplyQuery(main))

        server.Site.__init__(self, root)

        reactor.listenTCP(settings.RPC_PORT, self)

