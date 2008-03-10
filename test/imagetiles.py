from twisted.python import log
from twisted.web2 import server, http, resource, channel, stream, responsecode, http_headers, static
from twisted.internet import reactor
import os, os.path
from mako.template import Template
from mako.lookup import TemplateLookup
from mako import exceptions

TILE_SIZE = (256, 256)
VIEW_SIZE = (3*256, 2*256)
START_POS = (10, 10)
INITIAL_ZOOM = 1
ZOOM_MIN = 0    # the closest level of zoom
ZOOM_MAX = 3    # the furthest level of zoom

# yay templates
templates = TemplateLookup(directories=['templates'], module_directory='cache/templates', output_encoding='utf-8')

class Root (resource.Resource) :
    addSlash = True
    
    def render (self, r) :
        view_w, view_h = VIEW_SIZE
        start_row, start_col = START_POS
        end_row = start_row + view_h
        end_col = start_col + view_w
        
        tile_w, tile_h = TILE_SIZE
        
        tpl = templates.get_template("index.myt")
        
        try :
            data = tpl.render(
                    viewport_width      = view_w,
                    viewport_height     = view_h,
                    start_col           = start_col,
                    start_row           = start_row,
                    tile_width          = tile_w,
                    tile_height         = tile_h,
                    initial_zoom        = INITIAL_ZOOM,
                    zoom_min            = ZOOM_MIN,
                    zoom_max            = ZOOM_MAX,
                    mode                = mode.__name__,
            )
            response = responsecode.OK
        except :
            data = exceptions.html_error_template().render()
            response = responsecode.INTERNAL_SERVER_ERROR

        return http.Response(
            response,
            {
                'Content-Type': http_headers.MimeType('text', 'html', [('charset', 'utf-8')])
            },
            data
        )

root = Root()
root.putChild("static", static.File("static/"))
site = server.Site(root)

from sys import argv

import openttd
import image

if 'mode_openttd.py' in argv :
    mode = openttd
    http_port = 'tcp:8119'
    fcgi_port = 'tcp:6531'
elif 'mode_images.py' in argv :
    mode = image
    http_port = 'tcp:8118'
    fcgi_port = 'tcp:6532'
else :
    mode = None

#chan = channel.HTTPFactory(site)
#port = http_port
chan = channel.FastCGIFactory(site)
port = fcgi_port

from twisted.application import service, strports
application = service.Application("imagetiles")
s = strports.service(port, chan)
s.setServiceParent(application)

def startup (mode) :
    log.msg("imagetiles.startup")

    root.mode = mode

    mode.startup(root)


reactor.callWhenRunning(startup, mode)

