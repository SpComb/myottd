from _ordereddict import ordereddict

import os.path
import cPickle

# these are settings that should be be changeable by the user
HIDDEN_SETTINGS = (
    ("network",     "server_name"       ),
    ("network",     "server_port"       ),
    ("network",     "server_bind_ip"    ),
    ("network",     "connect_to_ip"     ),
    ("patches",     "keep_all_autosave" ),
    ("patches",     "screenshot_format" ),
    ("patches",     "max_num_autosaves" ),
    ("patches",     "fullscreen"        ),
    ("patches",     "autosave_on_exit"  ),
    ("misc",        "sounddriver"       ),
    ("misc",        "videodriver"       ),
    ("misc",        "savegame_format"   ),
    ("misc",        "musicdriver"       ),
    ("misc",        "resolution"        ),
    ("misc",        "display_opt"       ),
    ("misc",        "language"          ),
    ("music",       "custom_1"          ),
    ("music",       "custom_2"          ),
    ("interface",   "*"                 ),
)

class Config (object) :
    def __init__ (self, server) :
        self.server = server
        self.path = '%s/openttd.cfg' % server.path

        self.sections = ordereddict()
        
        self.config_info_cache = None
        self.config_info_cache_age = None
        
        # {section.key -> (type, type_data)
        self.value_types = None

        # {category -> (section, key, type, type_data, str)}
        self.cfg_categories = None

        # [(name, min, max, step, value_names)]
        self.diff_settings = None

        # [name]
        self.diff_levels = None
    
    def updateConfigInfo (self) :
        """
            Updates the cfg_categories, value_types, diff_settings and diff_levels instance attributes
        """
        
        config_info_path = '%s/openttd_version/cfg_info.dat' % self.server.path
        config_info_mtime = os.path.getmtime(config_info_path)

        if not self.config_info_cache or self.config_info_cache_age < config_info_mtime :
            fh = open(config_info_path, 'r')
            self.cfg_categories, self.diff_settings, self.diff_levels = cPickle.load(fh)
            fh.close()

            self.config_info_cache_age = config_info_mtime
            
            self.value_types = {}

            for catName, switches in self.cfg_categories :
                for section, key, type, type_data, str in switches :
                    self.value_types["%s.%s" % (section, key)] = (type, type_data)

    def read (self) :
        fh = open(self.path, 'r')
        
        section = sectionName = None
        
        self.updateConfigInfo()

        for line in fh :
            line = line.strip()

            if not line or line.startswith('#') :
                # comment
                continue
            elif '#' in line :
                line, comment = line.split('#', 1)
                line = line.strip()
            
            if line.startswith('[') and line.endswith(']') :
                sectionName = line.strip('[]')
                section = self.sections[sectionName] = ordereddict()
            else :
                if section is None :
                    raise Exception("not in a section while parsing %r" % line)

                if '=' in line :
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                else :
                    parts = line.split(' ')
                    key = parts.pop(0)
                    value = ' '.join(parts)
                
                sectionKey = "%s.%s" % (sectionName, key)

                if sectionKey in self.value_types :
                    type, type_data = self.value_types["%s.%s" % (sectionName, key)]

                    if type == 'str' :
                        value = value.strip('"')
                    elif type == 'int' :
                        value = int(value)
                    elif type == 'bool' :
                        value = value.lower()
                        if value in ('true', '1', 'on', 'yes') :
                            value = True
                        elif value in ('false', '0', 'off', 'no') :
                            value = False
                        else :
                            raise Exception("What kind of bool value is %r?" % value)
                    elif type == 'intlist' :
                        value = [int(x) for x in value.split(',')]
                    elif type == 'omany' :
                        pass
                    elif type == 'mmany' :
                        value = value.split('|')
                    else :
                        raise Exception("unknown type %s for %s: %r" % (type, sectionKey, value))
                else :
                    # just keep it as a string
                    value = value.strip('"')

                section[key] = value
        
        fh.close()

    def write (self) :
        fh = open(self.path, 'w')

        for sectionName, section in self.sections.iteritems() :
            fh.write("[%s]\r\n" % sectionName)

            for key, value in section.iteritems() :
                if value is None :
                    fh.write("%s\r\n" % key)
                elif isinstance(value, int) :
                    fh.write("%s = %d\r\n" % (key, value))
                elif isinstance(value, bool) :
                    fh.write("%s = %s\r\n" % (key, ('false', 'true')[int(value)]))
                elif isinstance(value, basestring) :
                    fh.write('%s = "%s"\r\n' % (key, value))
                elif isinstance(value, list) :
                    if value :
                        if isinstance(value[0], int) :
                            # intlist
                            fh.write("%s = %s\r\n" % (key, ','.join(str(i) for i in value)))
                        elif isinstance(value[0], basestring) :
                            # mmany
                            fh.write("%s = %s\r\n" % (key, '|'.join(str(x) for x in value)))
                        else :
                            raise Exception("unknown list type for %s.%s: %r" % (sectionName, key, value))
                    else :
                        # empty list
                        fh.write("%s = \r\n" % (key, ))
                else :
                    raise Exception("weird type %s of %s.%s: %r" % (type(value), sectionName, key, value))
        
        fh.close()

    def getSection (self, sectionName) :
        return self.sections[sectionName]

    def getValue (self, sectionName, key, default=None) :
        return self.sections[sectionName].get(key, default)

    def setValue (self, sectionName, key, value) :
        type, type_data = self.value_types["%s.%s" % (sectionName, key)]
        
        if type == 'str' :
            default = type_data
            
            pass

        elif type == 'int' :
            min, default, max = type_data

            if isinstance(value, int) and (min <= value or min == -1) and (value <= max or max == -1) :
                pass
            else :
                raise ValueError("Value `%d' for '%s.%s' not in range (%d - %d)" % (value, sectionName, key, min, max))

        elif type == 'bool' :
            default = type_data

            pass

        elif type == 'intlist' :
            length = type_data
            
            if len(value) != length :
                raise ValueError("Intlist %r for '%s.%s' is the wrong length (should be %d)" % (value, sectionName, key, length))
            else :
                for item in value :
                    if not isinstance(item, int) :
                        raise ValueError("Item `%r' in intlist for '%s.%s' is not an integer" % (item, sectionName, key))

        elif type == 'omany' :
            default, valid = type_data

            if value not in valid :
                raise ValueError("Value `%s' for one-of-many '%s.%s' is not valid (%s)" % (value, sectionName, key, ', '.join(valid)))

        elif type == 'mmany' :
            default, valid = type_data

            invalid = [x for x in value if x not in valid]
            
            if invalid :
                raise ValueError("Value(s) %s for many-of-many '%s.%s' are/is not valid (%s)" % (', '.join(["`%s'" % x for x in invalid]), sectionName, key, ', '.join(valid)))


        else :
            raise Exception("weird type %s for %s.%s" % (type, sectionName, key))

        self.sections[sectionName][key] = value

    def setSectionOrder (self, sectionName, keys) :
        self.sections[sectionName].setkeys(keys)
    
    def getConfig (self) :
        """
            Returns a ([(category_name, (name, type, type_data, value, descr))], diff_settings, diff_levels) tuple
        """
        
        self.updateConfigInfo()

        ret = []
        
        for cat_name, patches in self.cfg_categories :
            if (cat_name, "*") in HIDDEN_SETTINGS :
                continue
                
            out = []

            for section, key, type, type_data, str in patches :
                if (section, key) in HIDDEN_SETTINGS :
                    continue
                
                value = self.getValue(section, key)

                key = "%s.%s" % (section, key)

                out.append((key, type, type_data, value, str))
            
            ret.append((cat_name, out))

        return ret, self.diff_settings, self.diff_levels

    def setNewgrfs (self, newgrfs) :
        """
            newgrfs is a [(grf_name, params)] list
        """

        self.sections['newgrf'].setitems(newgrfs)

    def applyConfig (self, new_config) :
        """
            new_config is a {section.name -> value} dict
        """

        changed = {}

        for sectionKey, value in new_config.iteritems() :
            section, key = sectionKey.split('.', 1)

            if (section, '*') in HIDDEN_SETTINGS or (section, key) in HIDDEN_SETTINGS :
                continue

            cur_value = self.getValue(section, key)

            self.setValue(section, key, value)

            if cur_value != value :
                changed[sectionKey] = (cur_value, value)
        
        if changed :    
            print "writing out, %d changed: %s" % (len(changed), changed)
            
            self.write()
            
        return changed
    
    def getNewgrfs (self) :
        return self.sections['newgrf'].items()

