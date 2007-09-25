# Copyright 2007 Tero Marttila
#
# This file is part of MyOTTD.
#
# MyOTTD is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# MyOTTD is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from web.lib.base import *

def validate (id) :
     if c.user and id and model.Server.get_by(id=id).owner != c.user.id :
        raise Exception("server's not yours")

class MeController (BaseController) :
#    def __before__ (self) :
#        super(MeController, self).__before__()
    
    @require_login
    def index (self, sub_domain) :
       c.user_servers = model.user_servers(c.view_user.id)
       c.available_versions = model.available_versions()

       return render_response('me_index.myt') 
    
    @require_login
    @form_handler
    def server_add (self) :
        s = model.server_create(c.user.id, request.params['url'], request.params['name'], int(request.params.get('version')))
        
        h.redirect_to('admin_server', id=s.id)
    
    @validate_id
    def server (self, id) :
        c.server_id = id
        c.server_name, c.owner_name, c.server_port, c.server_status, c.server_version, c.server_version_id, c.server_config_stale, c.server_password, c.server_url = model.server_info(id)
        c.server_info = rpc.server_info(id)
        c.available_versions = model.available_versions()
        
        return render_response('me_server.myt')
    
    @validate_id
    @form_handler
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
            
            server.url = request.params['url']
            server.name = request.params['name']
            server.version = request.params['version']
#           server.advertise = bool(request.params.get('advertise', 0))
            server.password = request.params['password']

            server.touch()
        
        h.redirect_to('admin_server', id=id)
    
    @validate_id
    def new_random (self, id) :
        opts = {}

        for k in ('gameopt.landscape', 'patches.map_x', 'patches.map_y') :
            if 'map_' in k :
                v = int(request.params[k])
            else :
                v = request.params[k]
            opts[k] = v

        rpc.invoke('config_apply', id=id, config=opts, start_new=True)

        h.redirect_to('admin_server', id=id)

    @validate_id
    def savegames (self, id) :
        if request.params.get('save', False) :
            rpc.invoke('save_game', id=id)

        else :
            for name in request.params.iterkeys() :
                if name.startswith('load_') :
                    _, game_id, save_id = name.split('_')
                    game_id = int(game_id)
                    save_id = int(save_id)

                    rpc.invoke('load_game', id=id, game=game_id, save=save_id)
        
        h.redirect_to('admin_server', id=id)

    def config_view (self, id) :
        c.config, c.diff, c.diff_levels = rpc.invoke('config', id=id)

        return render_response('me_server_config.myt')
    
    @validate_id
    def config_apply (self, id ) :
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

