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

import urllib
import simplejson
import pprint

import settings

def invoke (cmd, **args) :
    fh = urllib.urlopen("http://localhost:%d/%s?%s" % (settings.RPC_PORT, cmd, urllib.urlencode(args)))
    obj = simplejson.load(fh)
    fh.close()

    return obj

if __name__ == '__main__' :
    from sys import argv

    argv.pop(0)
    cmd = argv.pop(0)
    args = {}

    for arg in argv :
        key, value = arg.split('=', 1)
        args[key] = value

    pprint.pprint(invoke(cmd, **args))

