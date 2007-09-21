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
)

servers_table = Table('servers', metadata,
    Column('id', Integer, primary_key=True),
    Column('owner', Integer, ForeignKey('users.id')),
    Column('name', Unicode(50)),
    Column('port', Integer),
    Column('enabled', Boolean),
    Column('advertise', Boolean),
    Column('version', Integer, ForeignKey('openttd_versions.id')),
    Column('status', String(10)),
    Column('config_changed', DateTime()),
    Column('config_applied', DateTime()),
    Column('password', String(30)),
)

def get_bind () :
    return ctx.current.get_bind(None)


def simple_servers_list () :
    return select(
        [
            servers_table.c.id,
            users_table.c.username,
            servers_table.c.name,
            openttd_versions_table.c.version,
        ],

        from_obj=[users_table.join(servers_table).join(openttd_versions_table)],

        order_by=[servers_table.c.owner],

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
        ],

        servers_table.c.id == id,

        from_obj=[users_table.join(servers_table).join(openttd_versions_table)],

        bind=get_bind()
    ).execute().fetchone()

def md5 (data) :
    return _md5.md5(data).hexdigest()

def register_user (username, password) :
    u = User()
    u.username = username
    u.password = md5(password)

    u.flush()

    return u

def user_login (username, password) :
    return User.get_by(username=username, password=md5(password))

def user_servers (user_id) :
    return select(
        [
            servers_table.c.id, 
            servers_table.c.name, 
            servers_table.c.port, 
            servers_table.c.advertise, 
            servers_table.c.status,
            openttd_versions_table.c.version,
        ], 
        
        servers_table.c.owner == user_id, 
        
        from_obj=[servers_table.join(openttd_versions_table)],

        bind=get_bind()
    ).execute()

def server_create (owner, name, advertise, version) :
    s = Server()
    s.owner = owner
    s.name = name
    s.advertise = advertise
    s.status = 'offline'
    s.enabled = True
    s.version = version

    ports = [p for p, in select([servers_table.c.port], order_by=[asc(servers_table.c.port)], bind=get_bind()).execute()]
    
    print "ports:", ports

    for port in xrange(settings.PORT_MIN, settings.PORT_MAX) :
        if port not in ports :
            s.port = port
            break

    if s.port :
        s.flush()
        return s
    else :
        raise Exception("All ports in use")

def available_versions () :
    return [(v, id) for v, id in select(
        [
            openttd_versions_table.c.version,
            openttd_versions_table.c.id,
        ],

        order_by=[openttd_versions_table.c.id],

        bind=get_bind()
    ).execute()]

climateCodeToName = {
    'normal': 'Temperate',
    'desert': 'Desert',
    'hilly': 'Arctic',
    'candy': 'Toyland',
}

climateNamesToCode = dict([(v, k) for k, v in climateCodeToName.iteritems()])

class User (object) :
    pass

class Server (object) :
    def touch (self) :
        self.config_changed = datetime.utcnow()
        self.flush()

class Version (object) :
    pass

assign_mapper(ctx, User, users_table)
assign_mapper(ctx, Server, servers_table)
assign_mapper(ctx, Version, openttd_versions_table)

