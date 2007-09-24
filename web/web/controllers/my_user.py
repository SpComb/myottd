from web.lib.base import *

class MyUserController (BaseController) :
    def index (self) :
        
        return render_response('user_index.myt')

    def view_server (self, url, sub_domain) :
        c.id = model.get_server_id_by_username(sub_domain, url)

        c.server_info = rpc.invoke('server_info', id=c.id)

        return render_response('server_info.myt')

