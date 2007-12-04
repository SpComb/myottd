from twisted.python import log
from twisted.web2 import server, http, resource, channel, stream, responsecode, http_headers, static
from twisted.internet import reactor
import os, os.path

TILE_SIZE = (150, 150)
VIEW_SIZE = (5, 3)
START_POS = (25, 25)
INITIAL_ZOOM = 0
ZOOM_MIN = 0    # the closest level of zoom
ZOOM_MAX = 3    # the furthest level of zoom

class Root (resource.Resource) :
    addSlash = True
    
    def render (self, r) :
        view_w, view_h = VIEW_SIZE
        start_row, start_col = START_POS
        end_row = start_row + view_h
        end_col = start_col + view_w
        
        tile_w, tile_h = TILE_SIZE

        images = []
        
        return http.Response(stream="""
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
    <head>
        <title>Image tiles</title>
        <script src="/static/prototype.js" type="text/javascript"></script>
        <script src="/static/scriptaculous.js" type="text/javascript"></script>
        <script src="/static/tiles.js" type="text/javascript"></script>
        <link rel="Stylesheet" type="text/css" href="static/style.css">
    </head>
    <body>
        <div id="wrapper">
            <div id="viewport" style="width: %dpx; height: %dpx">
                <div id="substrate">
%s        
                </div>
            </div>

            <div id="zoom">
                <input type="button" id="zoom_in" onclick="zoom(-1)" value="In" /> 
                    &lt;-- zoom --&gt; 
                <input type="button" id="zoom_out" onclick="zoom(1)" value="Out" />
                <br/>

                <a href="#" id="page_link">Link to this location</a>
            </div>

            <div id="help">
                <p>
A view into a real OpenTTD game. View updates when you drag the map. Join the OpenTTD server at <strong>myottd.net:7199</strong>.
                </p>
                <p>
<strong>Moving around</strong>: You can drag the map around with the left mouse button held down, or alternatively double-click on the map to center on that location (complete with fancy scroll effect).
                </p>
                <p>
<strong>Zooming</strong>. Use either the In/Out buttons, or the mouse wheel (scroll up to zoom in, scroll down to zoom out, this also centers the map on where the mouse is).
                </p>
            </div>

            <table id="vehicles_list"></table>
        </div>

        <script type="text/javascript">init(%d, %d, %d, %d, %d, %d, %d, %d, %d);</script>
    </body>
</html>""" % (view_w*tile_w, view_h*tile_h, '\n'.join(images), start_col, start_row, view_w, view_h, tile_w, tile_h, INITIAL_ZOOM, ZOOM_MIN, ZOOM_MAX))

root = Root()
root.putChild("static", static.File("static/"))
site = server.Site(root)

# direct HTTP
chan = channel.HTTPFactory(site)
port = 'tcp:8119'

# FastCGI
#chan = channel.FastCGIFactory(site)
#port = 'tcp:6531'

from twisted.application import service, strports
application = service.Application("imagetiles")
s = strports.service(port, chan)
s.setServiceParent(application)

import openttd

def startup (mode) :
    log.msg("imagetiles.startup")

    mode.startup(root)
    
reactor.callWhenRunning(startup, openttd)

