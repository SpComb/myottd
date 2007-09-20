from web.lib.base import *

class ServerController (BaseController) :
    def view (self, id) :
        c.server_id = id
        c.server_info = rpc.invoke('server_info', id=id)

        return render_response('server_info.myt')

