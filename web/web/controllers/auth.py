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

class AuthController (BaseController) :
    def login_show (self, sub_domain=None) :
        return render_response('login.myt')

    def login (self, sub_domain=None) :
        user = model.user_login(request.params['username'], request.params['password'])
        
        print "login_user: %r" % user

        if user :
            session['user_id'] = user.id
            session.save()

            sub_domain = user.username
        else :
            return Response("Bad login")
        
        h.redirect_to('admin', sub_domain=sub_domain)

    def register_show (self) :
        return render_response('register.myt')
    
    @form_handler
    def register (self) :
        if request.params['password'] != request.params['password_verify'] :
            raise ValueError("passwords don't match")
        
        user = model.register_user(request.params['username'], request.params['password'])
        
        session['user_id'] = user.id
        session.save()

        h.redirect_to('admin', sub_domain=user.username)
    
    def logout (self) :
        del session['user_id']
        session.save()

        h.redirect_to('home')
