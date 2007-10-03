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

from pylons import Response, c, g, cache, request, session
from pylons.controllers import WSGIController
from pylons.decorators import jsonify, validate, decorator
from pylons.templating import render, render_response
from pylons.helpers import abort, redirect_to, etag_cache
from pylons.i18n import N_, _, ungettext
import web.models as model
import web.lib.helpers as h
from web.lib import rpc, settings
import sqlalchemy.exceptions

class BaseController(WSGIController):
    def __before__ (self) :
        if 'user_id' in session :
            c.auth_user = model.User.get_by(id=session['user_id'])
        else :
            c.auth_user = False

        c.sub_domain = request.environ['pylons.routes_dict']['sub_domain']

        if c.sub_domain :
            c.view_user = model.get_user_by_username(c.sub_domain)
        else :
            c.view_user = False

        print "sub_domain:", c.sub_domain
        print "auth_user:", c.auth_user
        print "view_user:", c.view_user

    def __call__(self, environ, start_response):
        # Insert any code to be run per request here. The Routes match
        # is under environ['pylons.routes_dict'] should you want to check
        # the action or route vars here
        return WSGIController.__call__(self, environ, start_response)

@decorator
def form_handler (func, *args, **kwargs) :
    try :
        # fsking routes and its magical function arguments crap
        
        return func(*args, **kwargs)
    except sqlalchemy.exceptions.SQLError, e :
        error = "Database: %s" % e.orig.pgerror
    except rpc.RpcError, e :
        error = "Internal MyOTTD Daemon error: %s" % e
    except ValueError, e :
        error = "Invalid value: %s" % e
    
    c.error = error
    return render_response('error.myt')

@decorator
def require_login (func, *args, **kwargs) :
    if c.auth_user and c.view_user and c.auth_user.canManage(c.view_user) :
        return func(*args, **kwargs)
    else :
        h.redirect_to('login')

@decorator
def validate_id (func, self, id, *args, **kwargs) :
    if c.auth_user and c.view_user and c.auth_user.canManage(c.view_user) :
        if c.view_user and c.auth_user.canManage(c.view_user) :
            c.admin_server = model.Server.get_by(id=id)
            return func(self, id, *args, **kwargs)
        else :
            return Response("Not your server")
    else :
        h.redirect_to('login')

# who gives
import md5
import time
import datetime
import random
import os
from myghtyutils.session import Session
from paste.deploy import CONFIG

COOKIE_DOMAIN = CONFIG.current_conf()['app_conf']['cookie_domain']

def _my_create_id (self) :
    # copy-pasted from session.py
    self.id = md5.new(
        md5.new("%f%s%f%d" % (time.time(), id({}), random.random(), os.getpid()) ).hexdigest(), 
    ).hexdigest()
    self.is_new = True
    if self.use_cookies:
        self.cookie[self.key] = self.id
        self.cookie[self.key]['path'] = '/'
        self.cookie[self.key]["domain"] = COOKIE_DOMAIN
        if self.cookie_expires is not True:
            if self.cookie_expires is False:
                expires = datetime.datetime.fromtimestamp( 0x7FFFFFFF )
            elif isinstance(self.cookie_expires, datetime.timedelta):
                expires = datetime.datetime.today() + self.cookie_expires
            elif isinstance(self.cookie_expires, datetime.datetime):
                expires = self.cookie_expires
            else:
                raise ValueError("Invalid argument for cookie_expires: %s" % repr(self.cookie_expires))
            self.cookie[self.key]['expires'] = expires.strftime("%a, %d-%b-%Y %H:%M:%S GMT" )
        
        self.request.headers_out.add('set-cookie', self.cookie[self.key].output(header=''))

Session._create_id = _my_create_id

# Include the '_' function in the public names
__all__ = [__name for __name in locals().keys() if not __name.startswith('_') \
           or __name == '_']
