from twisted.python import log
from twisted.web2 import server, http, resource, channel, stream, responsecode, http_headers, static
import PIL.Image
import cStringIO, cPickle
import struct
import os, os.path

TILE_SIZE = (150, 150)
VIEW_SIZE = (5, 3)
START_POS = (25, 25)

def load_cache (filename) :
    fh = open(filename, 'r')

    width, height = struct.unpack('HH', fh.read(4))

    print "Cache contains %dx%d tiles" % (width, height)
    
    rows = []

    for row in xrange(0, height) :
        row = []

        for col in xrange(0, width) :
            len, = struct.unpack('H', fh.read(2))
            row.append(fh.read(len))

        rows.append(row)

    fh.close()

    return rows

def write_cache (filename, tiles) :
    fh = open(filename, 'w')

    fh.write(struct.pack('HH', len(tiles[0]), len(tiles)))

    for row in tiles :
        for tile in row :
            fh.write(struct.pack('H', len(tile)))
            fh.write(tile)
    
    fh.close()

def load_image (filename) :
    tile_w, tile_h = TILE_SIZE

    cache_fname = "cache/%s_%dx%d" % (filename, tile_w, tile_h)
    
    if os.path.exists(cache_fname) :
        img_mtime = os.stat(filename).st_mtime
        cache_mtime = os.stat(cache_fname).st_mtime

        if cache_mtime >= img_mtime :
            log.msg("Loading tiles from cache at %s" % cache_fname)
            
            return load_cache(cache_fname)
        else :
            log.msg("Cache exists, but img file is newer")

    log.msg("Loading image from %s..." % filename)
    img = PIL.Image.open(filename, 'r')

    img_w, img_h = img.size

    rows = []
    
    log.msg("Image of %dx%d px, splitting into %dx%d tiles" % (img_w, img_h, tile_w, tile_h))

    for y_offset in xrange(0, img_h, tile_h) :
        row = []

        for x_offset in xrange(0, img_w, tile_w) :
            buf = cStringIO.StringIO()

            img.crop((
                x_offset, 
                y_offset, 
                x_offset + tile_w, 
                y_offset + tile_h
            )).save(buf, 'png')
            
            row.append(buf.getvalue())

        rows.append(row)
    
    log.msg("Have %d rows of %d columns, writing to cache..." % (len(rows), rows and len(rows[0]) or 0))
    
    write_cache(cache_fname, rows)

    return rows

class OpenttdImage (resource.Resource) :
    def __init__ (self, openttd) :
        self.openttd = openttd

    def render (self, r) :
        x = int(r.args['x'][0])
        y = int(r.args['y'][0])
        w = int(r.args['w'][0])
        h = int(r.args['h'][0])
        z = int(r.args['z'][0])

        d = self.openttd.getScreenshot(x, y, w, h, z)

        d.addCallback(self._respond)

        return d

    def _respond (self, image_data) :
        return http.Response(
            responsecode.OK,
            {
                'Content-Type': http_headers.MimeType('image', 'png')
            },
            stream.MemoryStream(image_data)
        )

class Tile (resource.Resource) :
    def __init__ (self, tiles) :
        self.tiles = tiles

    def render (self, r) :
        col = int(r.args['x'][0])
        row = int(r.args['y'][0])

        tile_data = self.tiles[row][col]

        return http.Response(
            responsecode.OK,
            {
                'Content-Type': http_headers.MimeType('image', 'png')
            },
            stream.MemoryStream(tile_data)
        )

class Root (resource.Resource) :
    addSlash = True
    
    def render (self, r) :
        view_w, view_h = VIEW_SIZE
        start_row, start_col = START_POS
        end_row = start_row + view_h
        end_col = start_col + view_w
        
        tile_w, tile_h = TILE_SIZE
        
        return http.Response(stream="""
<html>
    <head>
        <title>Image tiles</title>
        <script src="/static/prototype.js" type="text/javascript"></script>
        <script src="/static/scriptaculous.js" type="text/javascript"></script>
        <script src="/static/tiles.js" type="text/javascript"></script>
        <link rel="Stylesheet" type="text/css" href="static/style.css" />
    </head>
    <body>
        <div id="wrapper">
            <div id="viewport" style="width: %dpx; height: %dpx">
                <div id="substrate">
%s        
                </div>
            </div>
        </div>

        <script type="text/javascript">init(%d, %d, %d, %d, %d, %d);</script>
    </body>
</html>""" % (view_w*tile_w, view_h*tile_h, '\n'.join(images), start_col, start_row, view_w, view_h, tile_w, tile_h))

root = Root()


# tile stuff
filename = "image.png"
#tiles = load_image(filename)
#root.putChild("tile_img", Tile(tiles))

# openttd stuff
import openttd
ottd = openttd.Openttd()
root.putChild("openttd_img", OpenttdImage(ottd))
root.putChild("static", static.File("static/"))

site = server.Site(root)

from twisted.application import service, strports
application = service.Application("imagetiles")
s = strports.service('tcp:8119', channel.HTTPFactory(site))
s.setServiceParent(application)

