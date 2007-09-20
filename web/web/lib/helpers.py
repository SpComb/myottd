"""
Helper functions

All names available in this module will be available under the Pylons h object.
"""
from webhelpers import *
from pylons.helpers import log
from pylons.i18n import get_lang, set_lang

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
        return "&lt;auto&gt;"

    return date(year=int(ds[:4]), month=int(ds[4:6]), day=int(ds[6:8])).strftime("%b %d %Y")

def fmtDateDict (dd) :
    return date(year=dd['year'], month=dd['month'], day=dd['day']).strftime("%b %d %Y")

