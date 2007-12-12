import PIL
import PIL.Image
import os, os.path
import cStringIO
import cPickle
import math

from twisted.python import log
from twisted.web2 import resource, responsecode, stream, http, http_headers

def load (data) :
    return cPickle.loads(data)

def dump (obj) :
    return cPickle.dumps(obj)

class ImageCollection (object) :
    def __init__ (self, dir, cache) :
        self.dir = dir
        self.images = {}

        self.cache = cache

    def path (self, *parts) :
        return os.path.join(self.dir, *parts)

    def getImage (self, filename) :
        if filename in self.images :
            return self.images[filename]

        i = self.images[filename] = Image(self, filename)

        return i
    
    IMAGELIST_VERSION = 7

    def getImageList (self) :
        return self.cache.get("%d:images:%s" % (self.IMAGELIST_VERSION, os.stat(self.dir).st_mtime)).addCallback(self._cachedImageList)

    def _cachedImageList (self, (flags, value)) :
        if not value :
            files = os.listdir(self.dir)
            
            imgs = []
            for file in files :
                if not os.path.isdir(file) :
                    img = self.getImage(file)
                    
                    imgs.append((file, img.zoom_max))

            self.cache.set("%d:images:%s" % (self.IMAGELIST_VERSION, os.stat(self.dir).st_mtime), dump(imgs))
        else :
            imgs = load(value)

        return (TILE_WIDTH, TILE_HEIGHT, imgs)

TILE_WIDTH = 256
TILE_HEIGHT = 256
VIEW_WIDTH = 3*TILE_WIDTH
VIEW_HEIGHT = 3*TILE_HEIGHT

class Image (object) :
    def __init__ (self, dir, filename) :
        self.dir = dir
        self.filename = filename
        self.path = self.dir.path(filename)

        basename, ext = os.path.splitext(filename)
        
        self.ext = {
            'jpg'   : 'jpeg',
            'jpeg'  : 'jpeg',

            'png'   : 'png',
        }.get(ext.strip('.').lower())
        
        log.msg("Loading image `%s'..." % filename)
        self.img = PIL.Image.open(self.path, 'r')
        self.width, self.height = self.img.size
        
        self.zoom_min = 0
        self.zoom_max = int(math.ceil(max(
            math.log(self.width/VIEW_WIDTH, 2),
            math.log(self.height/VIEW_HEIGHT, 2)
        )))

        self.zoom_initial = self.zoom_max

    def getTile (self, x, y, w, h, z) :
        if 0 <= x <= self.width and 0 <= y <= self.height :
            key = "2:%s:%s:%s:%s:%s:%s"% (self.filename, x, y, w, h, z)

            return self.dir.cache.get(key).addCallback(self._gotCache, key, x, y, w, h, z)
        else :
            raise ValueError((x, y))

    def _gotCache (self, (flags, value), key, x, y, w, h, z) :
        if not value :
            log.msg("Cache miss on %s" % key)
            value = self.generateTile(x, y, w, h, z)

            self.dir.cache.set(key, value)
        else :
            log.msg("Cache hit on %s" % key)
        
        return self.ext, value

    def generateTile (self, x, y, w, h, z) :
#        log.msg("Generate %dx%d@%d tile of `%s' at (%d, %d)" % (w, h, z, self.filename, x, y))
        
        tile = self.img.crop((x, y, x+(w << z), y+(h << z)))

        if z > 0 :
            tile = tile.resize((w, h), PIL.Image.ANTIALIAS)

        buf = cStringIO.StringIO()

        tile.save(buf, self.ext)

        return buf.getvalue()


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

class Tile (resource.Resource) :
    def __init__ (self, images) :
        self.images = images

    def render (self, r) :
        f = r.args['f'][0]
        x = int(r.args['x'][0])
        y = int(r.args['y'][0])
        w = int(r.args['w'][0])
        h = int(r.args['h'][0])
        z = int(r.args['z'][0])
        
        return self.images.getImage(f).getTile(x, y, w, h, z).addCallback(self._respond)

    def _respond (self, (ext, data)) :
        return http.Response(
            responsecode.OK,
            {
                'Content-Type': http_headers.MimeType('image', ext)
            },
            stream.MemoryStream(data)
        )

import simplejson

class Images (resource.Resource) :
    def __init__ (self, images) :
        self.images = images

    def render (self, r) :
        d = self.images.getImageList()

        d.addCallback(self._respond)

        return d

    def _respond (self, images) :
        json = simplejson.dumps(images)

        r = http.Response(
            responsecode.OK,
            {
                'Content-Type': http_headers.MimeType('text', 'javascript'),

                # Not cacheable
                'Cache-Control': {'no-store': None},
                'Expires': 100,
            },
            stream.MemoryStream(json)
        )
        
        r.headers.addRawHeader('X-JSON', json)
        
        return r

from twisted.internet import protocol, reactor

from lib import memcache

def startup (root) :
    log.msg("Connecting to memcached...")
    protocol.ClientCreator(reactor, memcache.MemCacheProtocol).connectTCP("localhost", memcache.DEFAULT_PORT).addCallback(_gotCache, root)

def _gotCache (cache, root) :
    log.msg("Got memcached, adding HTTP resource")

    images = ImageCollection("images", cache)

    root.putChild("tile", Tile(images))
    root.putChild("images", Images(images))

