from web.lib.base import *

class MyUserController (BaseController) :
    def index (self, sub_domain) :
        c.sub_domain = sub_domain

        return Response('user index: %s' % sub_domain)

    def view_server (self, url, sub_domain) :
        c.id = model.get_server_id_by_username(sub_domain, url)

        c.server_info = rpc.invoke('server_info', id=c.id)

        return render_response('server_info.myt')

