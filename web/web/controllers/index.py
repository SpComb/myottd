from web.lib.base import *

class IndexController (BaseController) :
    def view (self) :
        c.servers = rpc.invoke('servers')

        return render_response('index.myt')

