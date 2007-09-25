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

import os.path
from paste import fileapp
from pylons.middleware import media_path, error_document_template
from pylons.util import get_prefix
from web.lib.base import *

class ErrorController(BaseController):
    """
    Class to generate error documents as and when they are required. This behaviour of this
    class can be altered by changing the parameters to the ErrorDocuments middleware in 
    your config/middleware.py file.
    """

    def document(self):
        """
        Change this method to change how error documents are displayed
        """
        page = error_document_template % {
            'prefix': get_prefix(request.environ),
            'code': request.params.get('code', ''),
            'message': request.params.get('message', ''),
        }
        return Response(page)

    def img(self, id):
        return self._serve_file(os.path.join(media_path, 'img', id))
        
    def style(self, id):
        return self._serve_file(os.path.join(media_path, 'style', id))

    def _serve_file(self, path):
        fapp = fileapp.FileApp(path)
        return fapp(request.environ, self.start_response)
