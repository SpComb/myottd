"""
Setup your Routes options here
"""
import os
from routes import Mapper

def make_map (global_conf={}, app_conf={}) :
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    map = Mapper(directory=os.path.join(root_path, 'controllers'))
    
    # This route handles displaying the error page and graphics used in the 404/500
    # error pages. It should likely stay at the top to ensure that the error page is
    # displayed properly.
    map.connect('error/:action/:id', controller='error')
    
    map.connect('main', '/', controller='index', action='view')
    map.connect('server_info', '/servers/:id', controller='server', action='view')

    map.connect('auth_register_post', '/register', controller='auth', action='register', conditions=dict(method='POST'))
    map.connect('auth_register', '/register', controller='auth', action='register_show', conditions=dict(method='GET'))
    map.connect('auth_login_post', '/login', controller='auth', action='login', conditions=dict(method='POST'))
    map.connect('auth_login', '/login', controller='auth', action='login_show', conditions=dict(method='GET'))
    map.connect('auth_logout', '/logout', controller='auth', action='logout')

    map.connect('me', '/me', controller='me', action='index')
    map.connect('me_server_add', '/me/servers/add', controller='me', action='server_add', conditions=dict(method='POST'))
    map.connect('me_server_edit', '/me/servers/:id', controller='me', action='server_edit', conditions=dict(method='POST'))
    map.connect('me_server_newrandom', '/me/servers/:id/newrandom', controller='me', action='new_random', conditions=dict(method='POST'))
    map.connect('me_server', '/me/servers/:id', controller='me', action='server', conditions=dict(method='GET'))

    # Define your routes. The more specific and detailed routes should be defined first,
    # so they may take precedent over the more generic routes. For more information, refer
    # to the routes manual @ http://routes.groovie.org/docs/
    map.connect(':controller/:action/:id')
    map.connect('*url', controller='template', action='view')

    return map
