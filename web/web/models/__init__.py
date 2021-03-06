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

from pylons import config
from sqlalchemy import *
from sqlalchemy.ext.assignmapper import assign_mapper
from pylons.database import session_context as ctx

import md5 as _md5
from datetime import datetime

from web.lib import settings

metadata = MetaData()

users_table = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('username', Unicode(50)),
    Column('password', String(32)),
    Column('signup_at', DateTime()),
)

openttd_versions_table = Table('openttd_versions', metadata,
    Column('id', Integer, primary_key=True),
    Column('version', String(32)),
    Column('name', String(32)),
)

servers_table = Table('servers', metadata,
    Column('id', Integer, primary_key=True),
    Column('owner', Integer, ForeignKey('users.id')),
    Column('name', Unicode(20)),
    Column('port', Integer),
    Column('enabled', Boolean),
    Column('advertise', Boolean),
    Column('version', Integer, ForeignKey('openttd_versions.id')),
    Column('status', String(10)),
    Column('config_changed', DateTime()),
    Column('config_applied', DateTime()),
    Column('password', String(30)),
    Column('url', String(20)),
)

def get_bind () :
    return ctx.current.get_bind(None)


def simple_servers_list () :
    return select(
        [
            servers_table.c.id,
            users_table.c.username,
            servers_table.c.url,
            servers_table.c.name,
            openttd_versions_table.c.version,
        ],

        from_obj=[users_table.join(servers_table).join(openttd_versions_table)],

        order_by=[servers_table.c.owner, servers_table.c.url, servers_table.c.name],

        bind=get_bind()
    ).execute()

def server_info (id) :
    return select(
        [
            servers_table.c.name,
            users_table.c.username,
            servers_table.c.port,
            servers_table.c.status,
            openttd_versions_table.c.version,
            openttd_versions_table.c.id,
            servers_table.c.config_changed > servers_table.c.config_applied,
            servers_table.c.password,
            servers_table.c.url,
        ],

        servers_table.c.id == id,

        from_obj=[users_table.join(servers_table).join(openttd_versions_table)],

        bind=get_bind()
    ).execute().fetchone()

def md5 (data) :
    return _md5.md5(data).hexdigest()

def register_user (username, password) :
    if not username or not password :
        raise ValueError("Username/Password can't be empty strings")

    u = User()
    u.username = username
    u.password = md5(password)

    u.flush()

    return u

def user_login (username, password) :
    return User.get_by(username=username, password=md5(password))

def user_servers (user_id) :
    return list(select(
        [
            servers_table.c.id, 
            servers_table.c.url,
            servers_table.c.name, 
            servers_table.c.port, 
            servers_table.c.enabled,
            openttd_versions_table.c.version,
        ], 
        
        servers_table.c.owner == user_id, 
        
        from_obj=[servers_table.join(openttd_versions_table)],

        bind=get_bind()
    ).execute())
   
def server_create (owner, url, name, version) :
    s = Server()
    s.owner = owner
    s.url = url
    s.name = name
    s.advertise = True
    s.status = 'offline'
    s.enabled = True
    s.version = version

    ports = [p for p, in select([servers_table.c.port], order_by=[asc(servers_table.c.port)], bind=get_bind()).execute()]
    
    for port in settings.PORTS :
        if port not in ports :
            s.port = port
            break

    if s.port :
        s.flush()
        return s
    else :
        raise Exception("All ports in use")

def available_versions () :
    return list(select(
        [
            openttd_versions_table.c.name,
            openttd_versions_table.c.version,
            openttd_versions_table.c.id,
        ],

        order_by=[desc(openttd_versions_table.c.id)],

        bind=get_bind()
    ).execute())

def get_server_id_by_username (username, server_url) :
    res = select(
        [
            servers_table.c.id
        ],

        and_(
            func.lower(users_table.c.username) == username.lower(),
            func.coalesce(func.lower(servers_table.c.url), '') == server_url.lower()
        ),

        from_obj=[users_table.join(servers_table).join(openttd_versions_table)],

        bind=get_bind()
    ).execute().fetchone()

    if res :
        return res[0]
    else :
        raise ValueError("No such user/server: %s/%s" % (username, server_url))

def get_user_by_username (username) :
    return User.query().filter_by(func.lower(User.c.username) == username.lower()).first()

climateCodeToName = {
    'normal': 'Temperate',
    'desert': 'Desert',
    'hilly': 'Arctic',
    'candy': 'Toyland',
}

climateNamesToCode = dict([(v, k) for k, v in climateCodeToName.iteritems()])

class User (object) :
    def canManage (self, user) :
        return self is user

class Server (object) :
    def touch (self) :
        self.config_changed = datetime.utcnow()
        self.flush()

class Version (object) :
    pass

assign_mapper(ctx, User, users_table)
assign_mapper(ctx, Server, servers_table)
assign_mapper(ctx, Version, openttd_versions_table)

