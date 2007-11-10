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

from twisted.internet import reactor, protocol, defer

import os
import os.path
import shutil
from datetime import date
import re
import cPickle
import time

import rpc
import db
from settings import BASE_PATH
import udp

import config

SIGTERM = 15

CONFIG_SETTINGS = (
    ('server_name', 'network',   'server_name'),
    ('port',        'network',   'server_port'),
)

CONFIG_CONSTANTS = (
    ('network', 'lan_internet', 0),
    ('network', 'min_players', 1),
)

BUILTIN_NEWGRFS = [
    'sample.cat',
    'trg1r.grf',
    'trgcr.grf',
    'trghr.grf',
    'trgir.grf',
    'trgtr.grf',
    '2ccmap.grf',
    'airports.grf',
    'autorail.grf',
    'canalsw.grf',
    'dosdummy.grf',
    'elrailsw.grf',
    'nsignalsw.grf',
    'openttd.grf',
    'opntitle.dat',
    'trkfoundw.grf'
]

def ignoreResult (callable) :
    def _wrap (*args) :
        callable()

    return _wrap

def game_id (fname) :
    if fname.startswith('game_') :
        return int(fname.split('_')[1])
        
    else :
        return None

def save_date (fname) :
    fname, ext = os.path.splitext(fname)

    if fname.startswith('save_') :
        return fname.split('_')[1]
    else :
        return None

class Delay (defer.Deferred) :
    def __init__ (self, delay, what=None) :
        self._timer = reactor.callLater(delay, self.callback, what)

        defer.Deferred.__init__(self)

# create the poller
poller = udp.Poller()

class Server (protocol.ProcessProtocol) :
    """
        I am an OpenTTD server of ours
    """

    def __init__ (self, main, id, owner_id, owner_name, port, tag_part, name_part, version_id, version_name, enabled) :
        # the ServerManager
        self.main = main

        # our ID
        self.id = id

        # our owner
        self.owner_id = owner_id
        self.owner_name = owner_name

        # some other info from the DB
        self.port = port
        self.tag_part = tag_part
        self.name_part = name_part
        self.version_id = version_id
        self.version_name = version_name

        # set the server name
        self.server_name = self._fmtServerName(owner_name, tag_part, name_part)
        
        # are we supposed to be running?
        self.enabled = enabled

        # a deferred that's set when launching and callbacked once it's running
        self.startup = None

        # the are-we-running-or-not flag
        self.running = False
        
        # the currently loaded game, or None
        self.game_id = None

        # the date of the currently loaded save, or None (if game_id is not None, and this is, it means it's an autosave)
        self.save_date = None

        # are we running a freshly generated random map?
        self.random_map = None

        # is this a custom savegame that the user has uploaded onto this server?
        self.custom_save = None
        
        # command stuff
        self.out_queue = []
        self.out_wait = False
        self.cmd_count = 1
        self.cmd_queue = []
        self.cmd_deferred = None
        self.cmd_str = None
        self.reply_buffer = []
        self.delim_token = None
        
        # the filesystem path to our server dir
        self.path = '%s/servers/%d' % (BASE_PATH, self.id)

        # cached values of various OpenTTD variables
        self._var_cache = {}

        # the config
        self.config = config.Config(self)
        
        # must do this before trying to read the config
        self.checkFilesystem()

        self.config.read()

    def log (self, msg) :
        print '%d: %s' % (self.id, msg)

    def start (self, savegame=None) :
        """
            Prepare the environment and start the openttd server
        """

        if not self.enabled :
            self.log("Not enabled")
            return defer.succeed(None)

        assert not self.running and not self.startup

        startup = self.startup = defer.Deferred()
        self.game_id = self.save_date = None

        autosave_path = "%s/save/auto.sav" % self.path
        game_id_path = "%s/save/game_id.txt" % self.path

        if savegame is None and os.path.exists(autosave_path) :
            if os.path.exists(game_id_path) :
                self.log("found game_id.txt")
                fh = open(game_id_path, 'r')
                self.game_id = int(fh.read())
                self.save_date = None
            else :
                self.game_id = False

            self.log("resuming autosave with game_id=%s" % self.game_id)
            savegame = autosave_path
        else :
            self.log("not resuming, starting new random map")

        self.random_map = (savegame is None)

        self.updateConfig()
        self.checkFilesystem()

        args = ['openttd', '-D']
        
        if savegame :
            args.extend(['-g', savegame])
        
        self.log("starting openttd... with args: ./%s" % " ".join(args))
        reactor.spawnProcess(self, '%s/openttd' % self.path, args=args, path=self.path, usePTY=True)
        
        return startup

    def checkFilesystem (self) :
        """
            Check that the directory for the server exists
        """

        self.log("checking existance of server directory...")

        if not os.path.exists(self.path) :
            self.log("server directory does not exist yet, copying over skel")
            
            shutil.copytree('%s/servers/skel' % BASE_PATH, self.path, symlinks=True)
        
        ver_symlink_path = '%s/openttd_version' % self.path
        version_path = '%s/openttd/%s' % (BASE_PATH, self.version_name)
        cur_version_path = os.path.normpath(os.path.join(os.path.dirname(self.path + '/'), os.readlink(ver_symlink_path)))
        cur_version = cur_version_path.split('/')[-1]

        if version_path != cur_version_path :
            self.log("different openttd version, going from %s -> %s (%s -> %s)" % (cur_version, self.version_name, cur_version_path, version_path))
            os.unlink(ver_symlink_path)
            os.symlink(version_path, ver_symlink_path)
        else :
            self.log("version '%s' == '%s', '%s' == '%s'" % (cur_version, self.version_name, cur_version_path, version_path))
    

    def updateConfig (self) :
        """
            Update the openttd.cfg with the new config vlues
        """

        self.config.applyConfig(dict([
            ("%s.%s" % (section, key), getattr(self, attr_name)) for (attr_name, section, key) in CONFIG_SETTINGS
        ]))
        self.config.applyConfig(dict([
            ("%s.%s" % (section, key), value) for (section, key, value) in CONFIG_CONSTANTS
        ]))
    
    # RPC
    def getConfig (self) :
        return self.config.getConfig()

    def applyNewgrfs (self, newgrfs) :
        """
            Modify the config file to run the specified set of newgrfs
        """
 
        if self.running :
            return self.stop().addCallback(self._doApplyNewgrfs_stopped, newgrfs, True)
        else :
            return self._doApplyNewgrfs_stopped(None, new_config, False)

    def _doApplyNewgrfs_stopped (self, res, newgrfs, start) :
        self.config.setNewgrfs(newgrfs)
        self.config.write()

        if start :
            return self.start().addCallback(self._doApplyNewgrfs_started)
        else :
            return defer.succeed(None)

    def _doApplyNewgrfs_started (self, _) :
        return None

    def applyConfig (self, new_config, start_new=False) :
        """
            Stop the server, write out the config, and then start it again
        """
        
        if self.running :
            return self.stop().addCallback(self._doApplyConfig_stopped, new_config, True, start_new)
        else :
            return self._doApplyConfig_stopped(None, new_config, False, start_new)

    def _doApplyConfig_stopped (self, res, new_config, start, start_new) :
        changed = self.config.applyConfig(new_config)

        if start_new :
            sg = False
        else :
            sg = None
        
        self.log("start=%r, start_new=%r, sg=%r" % (start, start_new, sg))

        if start :
            return self.start(sg).addCallback(self._doApplyConfig_started, changed)
        else :
            return defer.succeed(changed)

    def _doApplyConfig_started (self, res, changed) :
        return changed

    #
    # The process state stuff
    #
    def connectionMade (self) :
        """
            openttd started
        """

        self.running = True
        self.log("running")
        
        startup = self.startup
        self.startup = None

        startup.callback(None)

    def outReceived (self, data) :
        """
            Read in data
        """

#        self.log("console: %s" % (repr(data)))
        
        while '\r\n' in data :
            line, data = data.split('\r\n', 1)

            self.lineReceived(line)

    def lineReceived (self, line) :
        """
            Got a line of text on the console
        """

        if self.cmd_deferred :
            if line == self.cmd_delim :
                self._cmdOver()
            else :
                self.reply_buffer.append(line)
        elif line.startswith('dbg: [NET][UDP] Queried from') :
            pass
        else :
            # handle events later, perhaps
            self.log("event: %s" % line)
            
    def processEnded (self, reason) :
        """
            Shut down
        """

        self.running = False
        self.log("ended: %s" % reason)

        if self.cmd_deferred :
            self._cmdOver()
    
    def writeLine (self, line) :
        #self.log("write: %s" % line)
        
        self.transport.write(line + '\n')
    
    #
    # Command/Response stuff
    #
    def command (self, cmd, *args) :
        """
            Run the given command on the console and return a deferred that callbacks with a list of the reply lines
        """

        if not self.running :
            raise Exception("not running")

        # escape the arguments as needed
        args2 = ['']
        for arg in args :
            if isinstance(arg, basestring) :
                args2.append('"%s"' % arg)
            else :
                args2.append(str(arg))
        
        # compose the command string
        cmd_str = self.cmd_str = '%s%s' % (cmd, ' '.join(args2))
        
        # compose the delimiter
        cmd_count = self.cmd_count
        self.cmd_count +=1

        delim = self.cmd_delim = 'delim-%d-%s' % (cmd_count, time.time())

        # the deferred and other stuff
        d = self.cmd_deferred = defer.Deferred()
        self.reply_buffer = []
        
        # run them
        self.log('running command: %s' % cmd_str)
        
        self.writeLine(cmd_str)
        self.writeLine('echo "%s"' % delim)

        # return deferred
        return d

    def _cmdOver (self) :
        """
            Callback the deferred
        """
        buf = self.reply_buffer
        d = self.cmd_deferred

        self.cmd_deferred = self.reply_buffer = None

        #self.log("Got response to command `%s`:\n    %s" % (self.cmd_str, '\n    '.join(buf)))

        d.callback(buf)
 
    
    # cd command
    def cmdCd (self, dir) :
        self.log("changing to directory %s" % dir)

        return self.command('cd', dir).addCallback(self._cmdCd_ok)

    def _cmdCd_ok (self, lines) :
        for line in lines :
            if line.endswith("No such file or directory.") :
                raise Exception("No such directory")

        return None

    # save command
    def cmdSave (self, filename) :
        self.log("saving to %s" % filename)

        return self.command('save', filename).addCallback(self._cmdSave_ok)

    def _cmdSave_ok (self, lines) :
        path = None

        for line in lines :
            if line.startswith("Map sucessfully saved to") :
                path = line.split(' ')[-1]

        if path :
            return path
        else :
            raise Exception("Save failed: %s" % lines)

    # load command
    def cmdLoad (self, filename) :
        self.log("loading savegame %s" % filename)

        return self.command('load', filename).addCallback(self._cmdLoad_ok)

    def _cmdLoad_ok (self, lines) :
        for line in lines :
            if line.endswith("No such file or directory.") :
                raise Exception("No such savegame")
            elif line.endswith("Cannot read savegame header, aborting.") :
                raise Exception("Corrupt savegame")
        
        # we can only assume...
        return None

    # stop command
    def stop (self) :
        self.log("stopping...")

        return self.cmdSave('auto').addCallback(self._doStop_saved)

    def _doStop_saved (self, res) :
        game_id_path = "%s/save/game_id.txt" % self.path

        if self.game_id :
            fh = open(game_id_path, 'w')
            fh.write(str(self.game_id))
            fh.close()
        elif os.path.exists(game_id_path) :
            os.unlink(game_id_path)

        return self.command('quit')

    def _waitStop (self, ret) :
        return Delay(2)
        
    # restart (stop + start)
    def restart (self, savegame=None) :
        if self.running :
            self.log("restarting...")

            return self.stop().addCallback(self._doRestart_stopped, savegame)
        else :
            self.log("not running, will just start")

            self.start(savegame)

    def _doRestart_stopped (self, res, savegame) :
        self.start(savegame)
    
    #
    # Savegame stuff
    #
    def _getNewestSave (self, game_id) :
        """
            Returns an (date, dir, fname) tuple
        """

        files = []

        for filename in os.listdir(savedir_path) :
            if filename.startswith('save_') :
                s_date = save_date(filename)

                files.append((s_date, savedir, filename))

        if files :
            files.sort(reverse=True)
            
            return files[0]
        else :
            return "", "", ""

    def saveGame (self) :
        """
            Save the current game
        """

        if self.game_id :
            return self._doSaveGame_gotId(self.game_id)
        else :
            self.log("inserting new game")
            return db.insertForID("games_id_seq", "INSERT INTO games (server) VALUES (%s)", self.id).addCallback(self._doSaveGame_gotId).addErrback(failure)

    def _doSaveGame_gotId (self, game_id) :
        self.game_id = game_id
        
        # check that the dir exists
        savedir_path = "%s/save/game_%d" % (self.path, game_id)

        if not os.path.exists(savedir_path) :
            self.log("save dir %s does not exist, creating" % savedir_path)
            os.mkdir(savedir_path)

        return poller.getInfo("127.0.0.1", self.port).addCallback(self._doSaveGame_gotDate, game_id)

    def _doSaveGame_gotDate (self, (host, port, info), game_id) :
        date = info.ext_date.current.strftime("%Y%m%d")

        new_save_path = "game_%d/save_%s" % (game_id, date)
        
        self.log("saving game_id=%s, date=%s" % (game_id, date))

        return self.cmdSave(new_save_path).addCallback(self._doSaveGame_saved, game_id, date)

    def _doSaveGame_saved (self, res, game_id, date) :
        self.save_date = date

        return dict(game_id=game_id, save_date=date)

    def loadGame (self, game_id, save_date=None) :
        """
            Continue the given game, loading either the given savegame, or the newest one
        """

        if not save_date :
            save_date, save_dir, save_fname = self._getNewestSave(game_id)
        else :
            save_dir = "game_%d" % game_id
            save_fname = "save_%s.sav" % save_date
            
        if self.running :
            self.log("loading game_id=%d, save_date=%s from %s as %s" % (game_id, save_date, save_dir, save_fname))

            return self.cmdCd(save_dir).addCallback(self._doLoadGame_inDir, game_id, save_date, save_fname)
        else :
            self.log("not running yet, so starting up with savegame at %s" % save_path)

            return self.start("%s/%s/%s" % (self.path, save_dir, save_fname)).addCallback(self._doLoadGame_started, game_id, save_date)

    def _doLoadGame_started (self, res, game_id, save_date) :
        self.game_id = game_id
        self.save_date = save_date
        self.random_map = False
        self.custom_save = None

        return dict(game_id=game_id, save_date=save_date)
    
    def _doLoadGame_inDir (self, res, game_id, save_date, save_fname) :
        return self.cmdLoad(save_fname).addCallback(self._doLoadGame_loaded, game_id, save_date)

    def _doLoadGame_loaded (self, res, game_id, save_date) :
        self.game_id = game_id
        self.save_date = save_date
        self.random_map = False
        self.custom_save = None

        return self.cmdCd("..").addCallback(self._doLoadGame_done, dict(game_id=game_id, save_date=save_date))

    def _doLoadGame_done (self, res, ret) :
        return ret

    def loadCustom (self, name) :
        """
            Load the 'custom' savegame file, saveing the current game if it exists
        """
        self.log("loading custom savegame")

        if self.game_id :
            self.log("saveing current game")
            return self.saveGame().addCallback(self._doLoadCustom_load, name)
        else :
            return self._doLoadCustom_load(None, name)

    def _doLoadCustom_load (self, res, name) :
        if self.running :
            return self.cmdLoad('custom').addCallback(self._doLoadCustom_loaded, name)
        else :
            return self.start(sg="%s/save/custom" % self.path).addCallback(self._doLoadCustom_loaded, name)

    def _doLoadCustom_loaded (self, res, name) :
        self.game_id = None
        self.save_id = None
        self.random_map = None
        self.custom_save = name

        return None
    
    #
    # OpenTTD variables
    #
    def getVar (self, name, cache=True) :
        """
            Get the value of the given variable, will be read from a cache by default
        """

        if cache and name in self._var_cache :
            return defer.succeed(self._var_cache[name])
        else :
            return self.command(name).addCallback(self._getVar_result, name, cache)

    def _getVar_result (self, lines, name, cache) :
        for line in lines :
            if line.startswith("Current value for '%s' is:") :
                _, value = line.split(':', 1)
                value = value.strip()
                
                if cache :
                    self._var_cache[name] = value
                
                return value
            elif line.startswith("ERROR") :
                raise Exception(line)

        return None

    def setVar (self, name, value) :
        """
            Change the value of the given variable, will be stored in the cache
        """

        if isinstance(value, basestring) :
            value = str(value).strip()

        if not value :
            raise ValueError("The value for variable '%s' cannot be blank" % name)

        return self.command(name, value).addCallback(self._setVar_result, name, value)

    def _setVar_result (self, lines, name, value) :
        for line in lines :
            if line.startswith("'%s' changed to:" % name) :
                _, value = line.split(':',  1)

                value = value.strip()

                self._var_cache[name] = value

                return value
            elif line.startswith("ERROR") :
                raise Exception(line)

        return None

    #
    # Methods to handle complex internal state info for use by the rpc* methods
    #

    def _fmtServerName (self, username, tag, name) :
        if tag :
            tag = "/%s" % tag

        return "%s.myottd.net%s - %s" % (username, tag, name)
       
    def setServerName (self, tag, name) :
        """
            Set the server name from the given tag, name and the owner username (which can't change)
        """

        self.tag_part = tag
        self.name_part = name
        
        server_name = self._fmtServerName(self.owner_name, tag, name)

        return self.setVar('server_name', server_name)

    def getSavegameInfo (self) :
        """
            Returns an {id -> [date_stamp]} dict
        """

        games = {}

        for dirpath, dirnames, filenames in os.walk("%s/save" % self.path) :
            head, tail = os.path.split(dirpath.rstrip('/'))

            g_id = game_id(tail)

            if g_id :
                g = games[g_id] = []
                
                for fname in filenames :
                    s_date = save_date(fname)

                    if s_date :
                        g.append(s_date)

                g.sort()

        return games

    def getNewgrfConfig (self) :
        """
            Returns a newgrf_path, [(fpath, loaded, params)] tuple
        """

        newgrf_path = "%s/data" % self.path
        newgrfs = []
        
        # newgrf info from the config file
        cfg_grfs = dict(self.config.getNewgrfs())
        
        # from the filesystem
        self.log("looking for .grfs in %s" % newgrf_path)
        queue = list(os.walk(newgrf_path))
        
        for dirpath, dirnames, filenames in queue :
            path_part = dirpath.split(newgrf_path)[1].lstrip('/')
            
            for dir in dirnames :
                path = os.path.join(dirpath, dir)

                if os.path.islink(path) :
                    #self.log("recursing into %s" % path)
                    queue.extend(os.walk(path))

            for fname in filenames :
                fpath = os.path.join(path_part, fname)

                if fpath in BUILTIN_NEWGRFS :
                    continue

                if fpath in cfg_grfs :
                    params = cfg_grfs[fpath]
                    loaded = True
                else :
                    params = None
                    loaded = False

                newgrfs.append((fpath, loaded, params))

        return newgrf_path, newgrfs

    #
    # New UDP-based status stuff
    #
    def rpcGetInfo (self, includeNewGrfs=False, _attempts=0) :
        """
            Return a dict with the info needed for showing this server in a list of servers
        """

        if _attempts > 3 :
            raise Exception("No response from server")
        
        if self.running :
            return poller.getInfo("127.0.0.1", self.port).addCallback(self._rpcGetInfo_result, includeNewGrfs, _attempts)
        else :
            return defer.succeed(None)

    def _rpcGetInfo_result (self, (host, port, info), includeNewGrfs, _attempts) :
        if info is None :
            return self.rpcGetInfo(includeNewGrfs, _attempts + 1)

        ret = dict(
            port            = port,
            server_name     = info.basic.name,
            client_count    = info.basic.clients_current,
            client_max      = info.basic.clients_max,
            company_count   = info.ext_limits.companies_current,
            company_max     = info.ext_limits.companies_max,
            version         = info.basic.revision,
            map_type        = info.basic.map_type,
            map_width       = info.basic.map_width,
            map_height      = info.basic.map_height,
            date_start      = info.ext_date.start,
            date_now        = info.ext_date.current,
            spectator_count = info.basic.spectators_current,
            spectator_max   = info.ext_limits.spectators_max,
            password        = bool(info.basic.password),

            # internal pieces of data
            id              = self.id,
            owner_id        = self.owner_id,
            owner           = self.owner_name,
            tag_part        = self.tag_part,
            name_part       = self.name_part,
            version_id      = self.version_id,
            version_name    = self.version_name,
        )

        if includeNewGrfs :
            return ret, info.newgrf_info.newgrfs
        else :
            return ret

    def rpcGetDetails (self) :
        """
            Return what getInfo returns, but a LOT more details
        """

        if self.running :
            return self.rpcGetInfo(True).addCallback(self._rpcGetDetails_gotInfo)
        else :
            return defer.succeed(None)

    def _rpcGetDetails_gotInfo (self, ret) :
        if ret :
            info, newgrfs = ret
            return poller.getDetails("127.0.0.1", self.port).addCallback(self._rpcGetDetails_gotDetails, info, newgrfs)
        else :
            return None

    def _rpcGetDetails_gotDetails (self, (host, port, details), info, newgrfs) :
        info.update(dict(
            companies=[dict(
                id                  = c.id,
                name                = c.name,
                start_year          = c.inaugurated,
                value               = c.company_value,
                balance             = c.balance,
                income              = c.income,
                performance         = c.performance,
                veh_trains          = c.vehicles.trains,
                veh_trucks          = c.vehicles.trucks,
                veh_busses          = c.vehicles.busses,
                veh_planes          = c.vehicles.planes,
                veh_ships           = c.vehicles.ships,
                stn_trains          = c.stations.trains,
                stn_trucks          = c.stations.trucks,
                stn_busses          = c.stations.busses,
                stn_planes          = c.stations.planes,
                stn_ships           = c.stations.ships,
                clients             = c.has_clients and [dict(
                    name            = p.name,
                    joined          = p.joined
                ) for p in c.clients] or [],
                password            = bool(c.password),
            ) for c in details.players],
            spectators=[dict(
                name                = s.name,
                joined              = s.joined,
            ) for s in details.spectators],
            
            # some internal info, not from UDP
            random_map      = self.random_map,
            game_id         = self.game_id,
            save_date       = self.save_date,
            custom_save     = self.custom_save,
        ))
        
        if newgrfs :
            return poller.getNewGrfs("127.0.0.1", self.port, newgrfs).addCallback(self._rpcGetDetails_gotNewGrfs, info)
        else :
            info.update(dict(
                newgrfs             = [],
            ))

            return info

    def _rpcGetDetails_gotNewGrfs (self, (host, port, newgrfs), info) :
        info.update(dict(
            newgrfs=[dict(
                grfid               = g.grfid,
                md5                 = g.md5,
                name                = g.name,
            ) for g in newgrfs.newgrfs],
        ))

        return info

    def rpcGetAdminInfo (self) :
        """
            Return what getDetails returns, but with some more internal info for use in the admin pages
        """
        
        if self.running :
            return self.rpcGetDetails().addCallback(self._rpcGetAdmin_gotDetails)
        else :
            return defer.succeed(None)
    
    def _rpcGetAdmin_gotDetails (self, info) :
        info.update(dict(
            games                   = self.getSavegameInfo(),
        ))

        info['newgrf_path'], info['newgrf_config'] = self.getNewgrfConfig()

        return self.getVar('server_pw').addCallback(self._rpcGetAdmin_gotVars, info)
    
    def _rpcGetAdmin_gotVars (self, server_pw, info) :
        info.update(dict(
            password_value      = server_pw,
        ))

        return info

    def rpcApply (self, tag_part, name_part, version_id, password) :
        """
            A way to conveniently change a couple core settings, like the server name and password, which can be changed at runtime. 
            Changing the server will require a explicit restart
        """
        
        if version_id != self.version_id :
            self.version_id = version_id
            return db.query("SELECT version FROM openttd_versions WHERE id=%s", version_id).addCallback(self._rpcApply_gotVersionName, tag_part, name_part, password)
        else :
            return self._rpcApply_doServerName(tag_part, name_part, password)

    def _rpcApply_gotVersionName (self, res, tag_part, name_part, password) :
        self.version_name = res[0][0]

        return self._rpcApply_doServerName(tag_part, name_part, password)

    def _rpcApply_doServerName (self, tag_part, name_part, password) :
        return self.setServerName(tag_part, name_part).addCallback(self._rpcApply_setName, password)
      
    def _rpcApply_setName (self, res, password) :
        if not password :
            password = "*"

        return self.setVar('server_pw', password)

def failure (failure) :
    print 'FAILURE: %s' % failure


COLS = "u.id, u.username, s.port, s.url, s.name, o_v.id, o_v.version, s.enabled"
SERVER_QUERY_BASE = "SELECT s.id, %s FROM servers s INNER JOIN users u ON s.owner = u.id INNER JOIN openttd_versions o_v ON s.version = o_v.id" % COLS

class ServerManager (object) :
    def __init__ (self) :
        self.servers = {}
        self.rpc = rpc.Site(self)

        db.query(SERVER_QUERY_BASE).addCallback(self._gotServers).addErrback(failure)

    def _gotServers (self, rows) :
        if not rows :
            print 'no servers in db'
            return
        
        for row in rows :
            id = row[0]
            
            print 'found server %d' % id
            self._startServer(row)

    def initServer (self, id, **opts) :
       s = self.servers[id] = Server(self, id, **opts)

       return s.start()

    def startServer (self, id, sg=None) :
        if id in self.servers :
            s = self.servers[id]
            s.enabled = True

            return s.start(sg)
        else :
            return db.query(SERVER_QUERY_BASE + " AND s.id=%s", id).addCallback(self._gotServerInfo, id, sg)

    def _gotServerInfo (self, res, id, sg) :
        if not res :
            raise KeyError(id)

        row = res[0]

        return self._startServer(row, sg)
 
    def _startServer (self, row, sg=None) :
        id = row[0]
        
        try :
            s = self.servers[id] = Server(self, *row)
            return s.start(sg)
        except Exception, e :
            print "Error starting server %d: %s" % (id, e)
            return defer.fail(e)
   
    def stopServer (self, id) :
        return self.servers[id].stop()

    def restartServer (self, id, sg=None) :
        return self.servers[id].restart(sg)

    def shutdown (self) :
        d = []

        for server in self.servers.itervalues() :
            if server.running :
                d.append(server.stop())

        return defer.DeferredList(d)

def main () :
    db.execute("UPDATE servers SET status='offline'")
    
    main = ServerManager()
    
    reactor.addSystemEventTrigger("before", "shutdown", main.shutdown)

if __name__ == '__main__' :
    print "Startup"

    reactor.callWhenRunning(main)
    reactor.run()


