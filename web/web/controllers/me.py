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
#           server.advertise = bool(request.params.get('advertise', 0))
            server.password = request.params['password']

            server.touch()
        
        h.redirect_to('me_server', id=id)
    
    def new_random (self, id) :
        validate(id)
        opts = {}

        for k in ('gameopt.landscape', 'patches.map_x', 'patches.map_y') :
            if 'map_' in k :
                v = int(request.params[k])
            else :
                v = request.params[k]
            opts[k] = v

        rpc.invoke('config_apply', id=id, config=opts, start_new=True)

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
    
    def config_apply (self, id ) :
        validate(id)
        
        config = {}

        for key, value in request.params.iteritems() :
            type, name = key.split('_', 1)

            if type == 'b' :
                config[name] = True
            elif type == 'bb' :
                if name not in config :
                    config[name] = False
            elif type == 'i' :
                if value :
                    config[name] = int(value)
                else :
                    config[name] = 0
            elif type == 't' :
                config[name] = value
            elif type == 'il' :
                name, i = name.rsplit('_', 1)

                i = int(i)

                if name not in config :
                    config[name] = []

                if len(config[name]) <= i :
                    config[name].extend([0 for x in xrange(len(config[name]), i + 1)])

                config[name][i] = int(value)

            elif type == 'om' :
                config[name] = value

            elif type == 'mm' :
                config[name] = request.params.getall(key)
            else :
                raise ValueError(type)

        c.changed = rpc.invoke('config_apply', id=id, config=config)
        
        return render_response('me_server_config_applied.myt')
