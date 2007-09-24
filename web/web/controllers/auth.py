from web.lib.base import *

class AuthController (BaseController) :
    def login_show (self, sub_domain=None) :
        return render_response('login.myt')

    def login (self, sub_domain=None) :
        user = model.user_login(request.params['username'], request.params['password'])
        
        if user :
            session['user_id'] = user.id
            session.save()

            sub_domain = user.username
        else :
            return Response("Bad login")
        
        h.redirect_to('admin', sub_domain=sub_domain)

    def register_show (self) :
        return render_response('register.myt')
    
    @form_handler
    def register (self) :
        if request.params['password'] != request.params['password_verify'] :
            raise ValueError("passwords don't match")
        
        user = model.register_user(request.params['username'], request.params['password'])
        
        session['user_id'] = user.id
        session.save()

        h.redirect_to('admin', sub_domain=user.username)
    
    def logout (self) :
        del session['user_id']
        session.save()

        h.redirect_to('home')
