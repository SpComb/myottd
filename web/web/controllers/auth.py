from web.lib.base import *

class AuthController (BaseController) :
    def login_show (self) :
        return render_response('login.myt')

    def login (self) :
        user = model.user_login(request.params['username'], request.params['password'])
        
        if user :
            session['user_id'] = user.id
            session.save()
        else :
            return Response("Bad login")
        
        h.redirect_to('me')

    def register_show (self) :
        return render_response('register.myt')
    
    @form_handler
    def register (self) :
        if request.params['password'] != request.params['password_verify'] :
            raise ValueError("passwords don't match")
        
        user = model.register_user(request.params['username'], request.params['password'])
        
        session['user_id'] = user.id
        session.save()

        h.redirect_to('me')
    
    def logout (self) :
        del session['user_id']
        session.save()

        h.redirect_to('main')
