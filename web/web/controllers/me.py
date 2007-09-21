from web.lib.base import *

def validate (id) :
     if c.user and id and model.Server.get_by(id=id).owner != c.user.id :
        raise Exception("server's not yours")

class MeController (BaseController) :
#    def __before__ (self) :
#        super(MeController, self).__before__()

    def index (self) :
       c.user_servers = model.user_servers(c.user.id)
       c.available_versions = model.available_versions()

       return render_response('me_index.myt') 
    
    def server_add (self) :
        s = model.server_create(c.user.id, request.params['name'], request.params.get('advertise', False), int(request.params.get('version')))
        
        h.redirect_to('me_server', id=s.id)
    
    def server (self, id) :
        validate(id)
        c.server_id = id
        c.server_name, c.owner_name, c.server_port, c.server_status, c.server_version, c.server_version_id, c.server_config_stale, c.server_password = model.server_info(id)
        c.server_info = rpc.server_info(id)
        c.available_versions = model.available_versions()
        
        return render_response('me_server.myt')
    
    def server_edit (self, id) :
        validate(id)
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
        validate(id)
        opts = {}

        for k in ('climate', 'map_x', 'map_y') :
            opts[k] = request.params[k]

        rpc.invoke('restart', id=id, force_new=True, **opts)

        h.redirect_to('me_server', id=id)

    def savegames (self, id) :
        validate(id)

        if request.params.get('save', False) :
            rpc.invoke('save_game', id=id)

        else :
            for name in request.params.iterkeys() :
                if name.startswith('load_') :
                    _, game_id, save_id = name.split('_')
                    game_id = int(game_id)
                    save_id = int(save_id)

                    rpc.invoke('load_game', id=id, game=game_id, save=save_id)
        
        h.redirect_to('me_server', id=id)

    def config_view (self, id) :
#        validate(id)

        c.config, c.diff, c.diff_levels = rpc.invoke('config', id=id)

        return render_response('me_server_config.myt')

