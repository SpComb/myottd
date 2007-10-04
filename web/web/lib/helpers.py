# Copyright 2007 Tero Marttila
#
# This file is part of MyOTTD.
#
# MyOTTD is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# MyOTTD is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
import math

climate_opts = web.models.climateNamesToCode

def climateName (code) :
    return web.models.climateCodeToName[code]
   
def mapSize (dim) :
    return 2**dim

def fmtTimestamp (ts) :
    return datetime.fromtimestamp(ts).strftime("%Y/%m/%d %H:%M")

def fmtDatestamp (ds) :
    if ds :
        return date(year=int(ds[0:4]), month=int(ds[4:6]), day=int(ds[6:8])).strftime("%b %d %Y")
    else :
        return "Auto"

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

def res_url (url) :
    return url_for('home') + url

def fmtMoney (money) :
    html = number_to_currency(money, unit='&euro; ', precision=0, separator='.', delimiter=',')

    if money < 0 :
        html = '<span class="negative">%s</span>' % html

    return html

def mapSize2value (size) :
    return int(math.log(size, 2))

