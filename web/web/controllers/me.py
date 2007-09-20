from web.lib.base import *

class MeController (BaseController) :
    def index (self) :
       c.user_servers = model.user_servers(c.user.id)
       c.available_versions = model.available_versions()

       return render_response('me_index.myt') 
    
    def server_add (self) :
        s = model.server_create(c.user.id, request.params['name'], request.params.get('advertise', False), int(request.params.get('version')))
        
        h.redirect_to('me_server', id=s.id)
    
    def server (self, id) :
        c.server_id = id
        c.server_name, c.owner_name, c.server_port, c.server_status, c.server_version, c.server_version_id, c.server_config_stale, c.server_password = model.server_info(id)
        c.server_info = rpc.invoke('server_info', id=id)
        c.available_versions = model.available_versions()
        
        return render_response('me_server.myt')
    
    def server_edit (self, id) :
        action = request.params['action']

        if action == 'Stop' :
           rpc.invoke('stop', id=id)
        elif action == 'Start' :
            rpc.invoke('start', id=id)
        elif action == 'Restart' :
            rpc.invoke('restart', id=id)
        elif action == 'Apply' :
            server = model.Server.get_by(id=id)

            server.name = request.params['name']
            server.version = request.params['version']
            server.advertise = bool(request.params.get('advertise', 0))
            server.password = request.params['password']

            server.touch()
        
        h.redirect_to('me_server', id=id)
    
    def new_random (self, id) :
        opts = {}

        for k in ('climate', 'map_x', 'map_y') :
            opts[k] = request.params[k]

        rpc.invoke('restart', id=id, **opts)

        h.redirect_to('me_server', id=id)


