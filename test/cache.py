
import cStringIO, cPickle
import struct

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

