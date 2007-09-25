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

#
# Copyright (c) 2007 Tero Marttila
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal 
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from twisted.enterprise import adbapi

from pyPgSQL import PgSQL

import settings

# fdsaf, for some reason this doesn't have any effect on the value of useUTCtimeValue in the PgSQL code
#PgSQL.useUTCtimeValue = True    # give all timestamps as UTC, plz
# so we assume all timestamps are localtime

def on_connect (connection) :
    #print "Setting client_encoding to unicode"
    c = connection.cursor()
    c.execute("SET CLIENT_ENCODING TO unicode")
    c.execute("SET TIME ZONE 'UTC'")
    c.close()
    
    # let's try it here
    PgSQL.useUTCtimeValue = True

class ConnectionPool (adbapi.ConnectionPool) :
    """
        Extends twisted.enterprise.adbapi.ConnectionPool
    """
    
    def __init__ (self) :
        adbapi.ConnectionPool.__init__(self, 'pyPgSQL.PgSQL', 
            user=settings.DATABASE_USER,
            database=settings.DATABASE_NAME, 
            password=settings.DATABASE_PASSWD, 
            client_encoding='utf-8',
            unicode_results=1,
            cp_openfun=on_connect,
            cp_reconnect=True,  # yay!
            cp_noisy=False,
        )
        
    def query (self, sql, params=None) :
        """
            A DB-API cursor will will be invoked with cursor.execute(sql, params). 
            The result of a subsequent cursor.fetchall() will be fired to the
            Deferred which is returned. If either the 'execute' or 'fetchall'
            methods raise an exception, the transaction will be rolled back and a 
            Failure returned.    
            
            This is meant to be used for queries that return results, like SELECT
        """
        
        if params :
            return self.runQuery(sql, params)     
        else :
            return self.runQuery(sql)

    def execute (self, sql, params=None) :
        """
            Similar to query, but simply callbacks with None on success instead
            of trying to fetch results. This is mean for manipulation queries like
            INSERT or DELETE
        """
        
        return self.runOperation(sql, params)

    def insertForID (self, id_seq, sql, params=None) :
        return self.execute(sql, params).addCallback(self._didInsert, id_seq)

    def _didInsert (self, res, id_seq) :
        return self.query("SELECT last_value FROM %s" % id_seq).addCallback(self._gotID)
    
    def _gotID (self, res) :
        return res[0][0]

cp = ConnectionPool()

def logthru (func) :
    def _thrulogger (query, *args):
        print "Running SQL query \"%s\" with params %s" % (query, args)
        return func(query, args)
    return _thrulogger

query = logthru(cp.query)
execute = logthru(cp.execute)
insertForID = cp.insertForID

