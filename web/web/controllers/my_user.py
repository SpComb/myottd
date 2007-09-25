from web.lib.base import *

class MyUserController (BaseController) :
    def index (self) :
        try :
            return self.view_server('', c.sub_domain)
        except ValueError :
            c.servers = rpc.invoke('servers')

            return render_response('index.myt')

    def view_server (self, url, sub_domain) :
        c.id = model.get_server_id_by_username(sub_domain, url)

        c.server_info = rpc.invoke('server_info', id=c.id)

        return render_response('server_info.myt')

