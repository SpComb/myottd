import urllib
import simplejson
import pprint

import settings

def invoke (cmd, **args) :
    fh = urllib.urlopen("http://localhost:%d/%s?%s" % (settings.RPC_PORT, cmd, urllib.urlencode(args)))
    obj = simplejson.load(fh)
    fh.close()

    code, type, data = obj

    if code == 'reply' :
        return data
    elif code == 'error' :
        raise Exception("RPC error: %s %s" % (type, data))

if __name__ == '__main__' :
    from sys import argv

    argv.pop(0)
    cmd = argv.pop(0)
    args = {}

    for arg in argv :
        key, value = arg.split('=', 1)
        args[key] = value

    pprint.pprint(invoke(cmd, **args))

