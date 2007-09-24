"""
Helper functions

All names available in this module will be available under the Pylons h object.
"""
from webhelpers import *
from pylons.helpers import log
from pylons.i18n import get_lang, set_lang
from pylons import c

import web.models
from datetime import datetime, date

climate_opts = web.models.climateNamesToCode

def climateName (code) :
    return web.models.climateCodeToName[code]
   
def mapSize (dim) :
    return 2**dim

def fmtTimestamp (ts) :
    return datetime.fromtimestamp(ts).strftime("%Y/%m/%d %H:%M")

def fmtDatestamp (ds) :
    if ds == "auto" :
        return "Auto"

    if not ds :
        return "N/A"

    return date(year=int(ds[:4]), month=int(ds[4:6]), day=int(ds[6:8])).strftime("%b %d %Y")

def fmtDateDict (dd) :
    return date(year=dd['year'], month=dd['month'], day=dd['day']).strftime("%b %d %Y")

def serverName (username, url, title) :
   return "%s.myottd.net%s - %s" % (username, (url and "/%s" % url or ''), title)

_url_for = url_for
def url_for (name, **params) :
    if 'sub_domain' not in params :
        params['sub_domain'] = c.sub_domain

    return _url_for(name, **params)

_redirect_to = redirect_to
def redirect_to (name, **params) :
    if 'sub_domain' not in params :
        params['sub_domain'] = c.sub_domain

    return _redirect_to(name, **params)

