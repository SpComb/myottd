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

class TemplateController(BaseController):
    def view(self, url):
        """
        This is the last place which is tried during a request to try to find a 
        file to serve. It could be used for example to display a template::
        
            def view(self, url):
                return render_response(url)
        
        Or, if you're using Myghty and would like to catch the component not
        found error which will occur when the template doesn't exist; you
        can use the following version which will provide a 404 if the template
        doesn't exist::
        
            import myghty.exception
            
            def view(self, url):
                try:
                    return render_response('/'+url)
                except myghty.exception.ComponentNotFound:
                    return Response(code=404)
        
        The default is just to abort the request with a 404 File not found
        status message.
        """
        abort(404)
