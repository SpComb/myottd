import urllib
import simplejson
import pprint

import settings

class RpcError (Exception) :
    def __init__ (self, type, data) :
        self.type = type
        self.data = data
    
    def __str__ (self) :
        return "%s: %s" % (self.type, self.data)

def invoke (cmd, **args) :
    args = dict([(key, simplejson.dumps(value)) for key, value in args.iteritems()])
    print "%s: %s" % (cmd, args)
    fh = urllib.urlopen("http://localhost:%d/%s?%s" % (settings.RPC_PORT, cmd, urllib.urlencode(args)))
    obj = simplejson.load(fh)
    fh.close()

    code, type, data = obj

    if code == 'reply' :
        return data
    elif code == 'error' :
        raise RpcError(type, data)

def server_info (id) :
    try :
        return invoke('server_info', id=id)
    except RpcError, e :
        if e.type == "KeyError" :
            return {}
        else :
            raise

if __name__ == '__main__' :
    from sys import argv

    argv.pop(0)
    cmd = argv.pop(0)
    args = {}

    for arg in argv :
        key, value = arg.split('=', 1)
        args[key] = value

    pprint.pprint(invoke(cmd, **args))

