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

import os

import pylons.config
import webhelpers

from web.config.routing import make_map

def load_environment(global_conf={}, app_conf={}):
    map = make_map(global_conf, app_conf)
    # Setup our paths
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = {'root_path': root_path,
             'controllers': os.path.join(root_path, 'controllers'),
             'templates': [os.path.join(root_path, path) for path in \
                           ('components', 'templates')],
             'static_files': os.path.join(root_path, 'public')
             }
    
    # The following template options are passed to your template engines
    tmpl_options = {}
    tmpl_options['myghty.log_errors'] = True
    tmpl_options['myghty.escapes'] = dict(l=webhelpers.auto_link, s=webhelpers.simple_format)
    
    # Add your own template options config options here, note that all config options will override
    # any Pylons config options
    
    # Return our loaded config object
    return pylons.config.Config(tmpl_options, map, paths)
