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
import ConfigParser
from datetime import date
import re
import cPickle
import time

import rpc
import db
from settings import BASE_PATH
import udp

SIGTERM = 15

CONFIG_SETTINGS = (
    ('server_name', 'network',   'server_name',        'str'    ),
    ('port',        'network',   'server_port',        'int'    ),
    ('advertise',   'network',   'server_advertise',   'bool'   ),
    ('password',    'network',   'server_password',    'str'    ),
#    ('game_climate','gameopt',   'landscape',          'str'    ),
#    ('map_x',       'patches',   'map_x',              'int'    ),
#    ('map_y',       'patches',   'map_y',              'int'    ),
)

CONFIG_CONSTANTS = (
    ('network', 'lan_internet', 0),
)

HIDDEN_SETTINGS = (
    ("network", "server_name"),
    ("network", "server_port"),
    ("network", "server_bind_ip"),
    ("network", "connect_to_ip"),
    ("patches", "keep_all_autosave"),
    ("patches", "screenshot_format"),
    ("patches", "max_num_autosaves"),
    ("patches", "fullscreen"),
    ("patches", "autosave_on_exit"),
#    ("patches", ""),
    ("misc", "sounddriver"),
    ("misc", "videodriver"),
    ("misc", "savegame_format"),
    ("misc", "musicdriver"),
    ("misc", "resolution"),
    ("misc", "display_opt"),
    ("misc", "language"),
    ("music", "custom_1"),
    ("music", "custom_2"),
#    ("misc", ""),
#    ("", ""),
    ("interface", "*"),
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

# monkey-patch ConfigParser to not fail on value-less settings
ConfigParser.RawConfigParser.OPTCRE = re.compile(r'(?P<option>[^:=\s][^:=]*)\s*(?P<vi>[:=]?)\s*(?P<value>.*)$')
ConfigParser.RawConfigParser.optionxform = str

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

class Openttd (protocol.ProcessProtocol) :
    def __init__ (self, main, id, *stuff) :
        self.main = main
        self.id = id
        self.startup = None
        self.running = False

        self.game_id = None
        self.save_date = None
        self.random_map = None
        self.custom_save = None
        
        self.out_queue = []
        self.out_wait = False

        self.cmd_count = 1
        self.cmd_queue = []
        self.cmd_deferred = None
        self.cmd_str = None
        self.reply_buffer = []
        self.delim_token = None
        
        self.path = '%s/servers/%d' % (BASE_PATH, self.id)

        self._setStuff(*stuff)
        
        self._var_cache = {}

    def _setStuff (self, username, server_name, port, advertise, password, version, owner_uid, url, version_id) :
        self.username = username
        self._server_name = server_name
        self.url = url
        self.server_name = "%s.myottd.net%s - %s" % (username, url and '/%s' % url or '', server_name)
        self.port = port
        self.advertise = advertise
        self.password = password
        self.version = version
        self.owner_uid = owner_uid

        # new naming convention
        self.owner_part     = username
        self.tag_part       = url
        self.name_part      = server_name
        self.version_id     = version_id
        self.version_name   = version

    def log (self, msg) :
        print '%d: %s' % (self.id, msg)

    def start (self, savegame=None, _fetchDb=True) :
        """
            Prepare the environment and start the openttd server
        """

        assert not self.running and not self.startup

        self.startup = defer.Deferred()
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

        if _fetchDb :
            db.query(SERVER_QUERY_BASE + " AND s.id=%s", self.id).addCallback(self._gotServerSettings, savegame)
        else :
            self._start2(savegame)

        return self.startup

    def _gotServerSettings (self, res, savegame) :
        row = res[0]

        self._setStuff(*(row[1:]))  # chop off the id column

        self._start2(savegame)

    def _start2 (self, savegame=None) :
        self.checkFilesystem()
        self.updateConfig()

        args = ['openttd', '-D']
        
        if savegame :
            args.extend(['-g', savegame])
        
        self.log("starting openttd... with args: ./%s" % " ".join(args))
        reactor.spawnProcess(self, '%s/openttd' % self.path, args=args, path=self.path, usePTY=True)

    def checkFilesystem (self) :
        """
            Check that the directory for the server exists
        """

        self.log("checking existance of server directory...")

        if not os.path.exists(self.path) :
            self.log("server directory does not exist yet, copying over skel")
            
            shutil.copytree('%s/servers/skel' % BASE_PATH, self.path, symlinks=True)
        
        ver_symlink_path = '%s/openttd_version' % self.path
        version_path = '%s/openttd/%s' % (BASE_PATH, self.version)
        cur_version_path = os.path.normpath(os.path.join(os.path.dirname(self.path + '/'), os.readlink(ver_symlink_path)))
        cur_version = cur_version_path.split('/')[-1]

        if version_path != cur_version_path :
            self.log("different openttd version, going from %s -> %s (%s -> %s)" % (cur_version, self.version, cur_version_path, version_path))
            os.unlink(ver_symlink_path)
            os.symlink(version_path, ver_symlink_path)
        else :
            self.log("version '%s' == '%s', '%s' == '%s'" % (cur_version, self.version, cur_version_path, version_path))
    
    def _getConfigValue (self, config, section, key, type, new_value=None, type_data=None) :
        try :
            default = None

            if type == 'str' :
                if type_data :
                    default = type_data

                value = config.get(section, key)

                print "value for str %s.%s is: %s" % (section, key, repr(value))
                
                if new_value is None :
                    new_value_raw = default
                else :
                    new_value_raw = new_value

            elif type == 'int' :
                if type_data :
                    min, default, max = type_data

                value = config.getint(section, key)
                
                if new_value is None :
                    new_value_raw = default
                elif not type_data or (min <= new_value or min == -1) and (new_value <= max or max == -1) :
                    new_value_raw = new_value
                else :
                    raise ValueError("Value `%d' for '%s.%s' not in range (%d - %d)" % (new_value, section, key, min, max))

            elif type == 'bool' :
                if type_data :
                    default = type_data

                value = config.getboolean(section, key)

                if new_value is None :
                    new_value_raw = default
                elif new_value :
                    new_value_raw = 'true'
                else :
                    new_value_raw = 'false'

            elif type == 'intlist' :
                if type_data :
                    length = type_data
                    default = ','.join(['0' for x in xrange(length)])

                value = config.get(section, key)

                value = [int(x) for x in value.split(',')]

                if new_value :
                    new_value_raw = ','.join([str(x) for x in new_value])
                else :
                    new_value_raw = default
            
            elif type == 'omany' :
                if type_data :
                    default, valid = type_data

                value = config.get(section, key)

                if new_value is None:
                    new_value_raw = default
                elif not type_data or new_value in valid :
                    new_value_raw = str(new_value)
                else :
                    raise ValueError("`%s' is not valid (%s)" % (value, ', '.join(valid)))
                    
            elif type == 'mmany' :
                if type_data :
                    default, valid = type_data

                value = config.get(section, key).split('|')

                if new_value is None :
                    new_value_raw = default
                else :
                    if type_data :
                        invalid = [x for x in new_value if x not in valid]

                    if not type_data or not invalid :
                        new_value_raw = '|'.join(new_value)
                    else :
                        raise ValueError("Values %s are not valid (%s)" % (', '.join(["`%s'" % x for x in invalid]), ', '.join(valid)))

            else :
                raise ValueError(type)

            return value, new_value_raw

        except ConfigParser.NoOptionError :
            return default, default

    def updateConfig (self) :
        """
            Update the openttd.cfg with the new config vlues
        """

        config_path = '%s/openttd.cfg' % self.path

        self.log('updating openttd.cfg...')

        config = ConfigParser.RawConfigParser()
        config.read([config_path])

        dirty = False


        for attr_name, section, key, type in CONFIG_SETTINGS :
            new_value = getattr(self, attr_name)
            
            value, new_value_raw = self._getConfigValue(config, section, key, type, new_value)
                    
            self.log('   %10s.%-20s: %20s -> %-20s' % (section, key, value, new_value))

            if value != new_value :
                dirty = True
                self.log('    changed!')
                config.set(section, key, new_value_raw)

        if dirty :
            self.log('writing out new openttd.cfg')
            fo = open(config_path, 'w')
            config.write(fo)
            fo.close()
       
        return dirty
    
    # RPC
    def _loadConfigInfo (self) :
        config_path = '%s/openttd.cfg' % self.path
        patch_path = '%s/openttd_version/cfg_info.dat' % self.path

#        self.log('reading openttd.cfg...')

        config = ConfigParser.RawConfigParser()
        config.read([config_path])
    
#        self.log("reading patches.dat...")
        
        fh = open(patch_path, 'r')
        categories, diff_settings, diff_levels = cPickle.load(fh)
        fh.close()

        return config, categories, diff_settings, diff_levels
    
    def _writeConfigObj (self, config) :
        config_path = '%s/openttd.cfg' % self.path

        fo = open(config_path, 'w')
        config.write(fo)
        fo.close()

    def getConfig (self) :
        """
            Returns a category_name -> [(name, type, type_data, value, descr)] dict
        """

        config, categories, diff_settings, diff_levels = self._loadConfigInfo()
        self.log("computing config...")

        ret = []
        
        for cat_name, patches in categories :
            if (cat_name, "*") in HIDDEN_SETTINGS :
                continue
                
            out = []

            for section, key, type, type_data, str in patches :
                if (section, key) in HIDDEN_SETTINGS :
                    continue

                value, _ = self._getConfigValue(config, section, key, type)

                key = "%s.%s" % (section, key)

                out.append((key, type, type_data, value, str))
            
            ret.append((cat_name, out))

        return ret, diff_settings, diff_levels

    def applyNewgrfs (self, newgrfs) :
        """
            Modify the config file to run the specified set of newgrfs
        """
 
        if self.running :
            return self.stop().addCallback(self._doApplyNewgrfs_stopped, newgrfs, True)
        else :
            return self._doApplyNewgrfs_stopped(None, new_config, False)

    def _doApplyNewgrfs_stopped (self, res, newgrfs, start) :
        config = ConfigParser.RawConfigParser()
        config.read(['%s/openttd.cfg' % self.path])
        
        config.remove_section('newgrf')
        config.add_section('newgrf')
        
        self.log("applying newgrfs: %s" % (newgrfs, ))
        for newgrf, params in newgrfs :
            config.set('newgrf', newgrf, params)

        self._writeConfigObj(config)

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
        config, categories, diff_settings, diff_levels = self._loadConfigInfo()
        
        config_types = {}

        for cat_name, patches in categories :
            if (cat_name, "*") in HIDDEN_SETTINGS :
                continue
                
            out = []

            for section, key, type, type_data, str in patches :
                if (section, key) in HIDDEN_SETTINGS :
                    continue

                config_types["%s.%s" % (section, key)] = type, type_data
        
        print "applying %d config items (%d known items)" % (len(new_config), len(config_types))

        changed = {}

        for key, value in new_config.iteritems() :
            section, name = key.split('.', 1)

            type, type_data = config_types[key]

            cur_value, new_value_raw = self._getConfigValue(config, section, name, type, value, type_data)

            config.set(section, name, new_value_raw)

            if cur_value != value :
                changed[key] = (cur_value, value)
        
        print "writing out, %d changed: %s" % (len(changed), changed)

        self._writeConfigObj(config)
        
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

    def connectionMade (self) :
        """
            openttd started
        """

        self.running = True
        self.log("running")
        
        startup = self.startup
        self.startup = None

        db.execute("UPDATE servers SET status='online', config_applied=NOW() WHERE id=%s", self.id).chainDeferred(startup)

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
    
    def writeLine (self, line) :
        #self.log("write: %s" % line)
        
        self.transport.write(line + '\n')

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
 
    def processEnded (self, reason) :
        """
            Shut down
        """

        self.running = False
        self.log("ended: %s" % reason)

        db.execute("UPDATE servers SET status='offline' WHERE id=%s", self.id)

        if self.cmd_deferred :
            self._cmdOver()
    
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
           
    # Game-based perspective
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
    # console commands
    #
    def getVar (self, name, cache=True) :
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
        if isinstance(value, basestring) :
            value = str(value).strip()

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
    # Utility functions to handle internal info for the below functions
    #
    def setServerName (self, tag, name) :
        self.tag_part = tag
        self.name_part = name

        if tag :
            tag = "/%s" % tag

        server_name = "%s.myottd.net%s - %s" % (self.owner_part, tag, self.name_part)

        return self.setVar('server_name', server_name)

    def getSavegameInfo (self) :         
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
        newgrf_path = "%s/data" % self.path
        newgrfs = []
        config = ConfigParser.RawConfigParser()
        config.read(['%s/openttd.cfg' % self.path])
        
        # newgrf info from the config file
        cfg_grfs = {}
        for name, params in config.items('newgrf') :
            cfg_grfs[name] = params
        
        # from the filesystem
        self.log("looking for .grfs in %s" % newgrf_path)
        queue = list(os.walk(newgrf_path))
        
        for dirpath, dirnames, filenames in queue :
            path_part = dirpath.split(newgrf_path)[1].lstrip('/')
            
            for dir in dirnames :
                path = os.path.join(dirpath, dir)

                if os.path.islink(path) :
                    self.log("recursing into %s" % path)
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
            return defer.suceed(None)

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
            owner_id        = self.owner_uid,
            owner           = self.owner_part,
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

    def _rpcGetDetails_gotInfo (self, (info, newgrfs)) :
        return poller.getDetails("127.0.0.1", self.port).addCallback(self._rpcGetDetails_gotDetails, info, newgrfs)

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
            Update the game with the given params. Changing the version will require an explicit restart
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

COLS = "u.username, s.name, s.port, s.advertise, s.password, o_v.version, u.id, s.url, o_v.id"
SERVER_QUERY_BASE = "SELECT s.id, %s FROM servers s INNER JOIN users u ON s.owner = u.id INNER JOIN openttd_versions o_v ON s.version = o_v.id WHERE s.enabled" % COLS

class ServerManager (object) :
    def __init__ (self) :
        self.servers = {}
        self.rpc = rpc.Site(self)

        db.query(SERVER_QUERY_BASE).addCallback(self._gotServers).addErrback(failure)

    def _startServer (self, row, sg=None) :
        id = row[0]
        s = self.servers[id] = Openttd(self, *row)
        return s.start(sg, _fetchDb=False)

    def _gotServers (self, rows) :
        if not rows :
            print 'no servers in db'
            return
        
        for row in rows :
            id = row[0]
            
            print 'found server %d' % id
            self._startServer(row)


    def startServer (self, id, sg=None) :
        if id in self.servers :
            return self.servers[id].start(sg)
        else :
            return db.query(SERVER_QUERY_BASE + " AND s.id=%s", id).addCallback(self._gotServerInfo, id, sg)

    def _gotServerInfo (self, res, id, sg) :
        if not res :
            raise KeyError(id)

        row = res[0]

        return self._startServer(row, sg)
    
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


