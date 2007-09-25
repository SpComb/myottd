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

"""
Setup your Routes options here
"""
import os
from routes import Mapper

def make_map (global_conf={}, app_conf={}) :
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    map = Mapper(directory=os.path.join(root_path, 'controllers'))

    map.sub_domains = True
    map.sub_domains_ignore = ['www']
    
    # This route handles displaying the error page and graphics used in the 404/500
    # error pages. It should likely stay at the top to ensure that the error page is
    # displayed properly.
    map.connect('error/:action/:id', controller='error')

    # sub_domain optional
    map.connect('login',                    '/login', controller='auth', action='login_show', conditions=dict(method='GET'))
    map.connect('login_post',               '/login', controller='auth', action='login', conditions=dict(method='POST'))

    # sub_domain required
    map.connect('admin',                    '/admin', controller='me', action='index', conditions=dict(sub_domain=True))
    map.connect('admin_server_add',         '/admin/add', controller='me', action='server_add', conditions=dict(method='POST', sub_domain=True))
    map.connect('admin_server',             '/admin/:id', controller='me', action='server', conditions=dict(method='GET', sub_domain=True))
    map.connect('admin_server_edit',        '/admin/:id', controller='me', action='server_edit', conditions=dict(method='POST', sub_domain=True))
    map.connect('admin_server_newrandom',   '/admin/:id/newrandom', controller='me', action='new_random', conditions=dict(method='POST', sub_domain=True))
    map.connect('admin_server_savegames',   '/admin/:id/savegames', controller='me', action='savegames', conditions=dict(method='POST', sub_domain=True))
    map.connect('admin_server_config',      '/admin/:id/config', controller='me', action='config_view', conditions=dict(method='GET', sub_domain=True))
    map.connect('admin_server_config_post', '/admin/:id/config', controller='me', action='config_apply', conditions=dict(method='POST', sub_domain=True))
    
    map.connect('user',                     '/', controller='my_user', action='index', conditions=dict(sub_domain=True))
    map.connect('server',                   '/*url', controller='my_user', action='view_server', conditions=dict(sub_domain=True))

    # sub_domainless
    map.connect('home',                     '/', controller='index', action='view')

    map.connect('register_post',            '/register', controller='auth', action='register', conditions=dict(method='POST'))
    map.connect('register',                 '/register', controller='auth', action='register_show', conditions=dict(method='GET'))
    map.connect('logout',                   '/logout', controller='auth', action='logout')
    
    return map
