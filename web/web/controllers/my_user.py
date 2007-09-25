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

class MyUserController (BaseController) :
    def index (self) :
        try :
            return self.view_server('', c.sub_domain)
        except ValueError :
            c.servers = rpc.invoke('servers')

            return render_response('index.myt')

    def view_server (self, url, sub_domain) :
        c.id = model.get_server_id_by_username(sub_domain, url)

        c.server_info = rpc.invoke('server_info', id=c.id)

        return render_response('server_info.myt')

