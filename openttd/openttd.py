#!/usr/bin/env python

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

import os, os.path
import re
import subprocess
from pprint import pprint
import cPickle

def applyTypes (vars, *types) :
    ret =  []
    
#    print "apply types %s to:\n\t%s" % (types, vars)

    for i, t in enumerate(types) :
       v = parseVar(vars[i], t)

       ret.append(v)

    return ret

def parseVar (var, t) :
    var = var.strip()
    
    if t == 'lit' :
        pass
    elif t == 'str' :
        var = var.strip('"')
    elif t == 'cast' :
        _, var = var.split(')(')
        var = var.rstrip(')')
    elif t == 'int' :
        try :
            var = int(var)
        except ValueError :
            print "Can't parse int: %s" % var
            var = -1
    elif t == 'bool' :
        if var == 'true' :
            var = True
        elif var == 'false' :
            var = False
        else :
            raise ValueError("weird literal for bool: %s" % var)
    elif t == 'flags' :
        var = var.split('|')
        var = [v.strip() for v in var]
        var = [v for v in var if v != '0']
    elif t == 'many' :
        var = var.strip('(")')
        var = var.split('|')
    else :
        raise Exception(t)
    
    if var == "((void *)0" :
        return ""

    return var

meta_re = re.compile(r"\{.*?\}")
def load_lang (lang_path) :
    print "Reading lang data from %s" % lang_path

    fh = open(lang_path, 'r')

    strs = {}
    next = {}

    prev = None

    for line in fh :
        line = line.strip()

        if not line or line.startswith('#') :
            continue

#        print "line: ", line

        key, value = line.split(':', 1)
        key = key.strip()
        
        value = value.replace("{COMMA}%", "<percentage>")
        value = value.replace("{CURRENCY}", "<currency>")
        value = value.replace("%", "%%")
        value = value.replace("{STRING1}", "%s")

        value = meta_re.sub('', value)

        strs[key] = value

        if prev :
            next[prev] = key

        prev = key

    return strs, next

# {NSD_GENERAL(name, def, sdt_cmd, guiflags, min, max, interval, full, str, proc), SLEG_GENERAL(sle_cmd, var, type | flags, length, from, to)}
#   #define NSD_GENERAL(name, def, cmd, guiflags, min, max, interval, many, str, proc) {name, (const void*)(def), cmd, guiflags, min, max, interval, many, str, proc}
#   #define SLEG_GENERAL(cmd, variable, type, length, from, to) {cmd, type, length, from, to, (void*)&variable}
# {{"map_x", (const void*)(8), SDT_NUMX, 0, 6, 11, 0, ((void *)0), STR_CONFIG_PATCHES_MAP_X, ((void *)0)}, {SL_VAR, SLE_UINT8 | SLF_SAVE_NO | SLF_NETWORK_NO, 1, 0, 255, (void*)__builtin_offsetof (Patches, map_x)}},

settings_re = re.compile(r"const SettingDesc(?:GlobVarList)? _(.*?)_settings\[\] = \{(.*?)};", re.DOTALL)


def handle_settings (settings_path, lang) :
    strs = lang

    print "Inspecting settings at %s" % settings_path
    
    source = subprocess.Popen(["gcc", "-DENABLE_NETWORK", "-E", settings_path], stdout=subprocess.PIPE).communicate()[0]

    print "Looking for settings blocks..."
    
    patches = {}

    block_names = {
        'patch': 'patches',
    }

    for m in settings_re.finditer(source) :
        block_name = m.group(1)
        block_data = m.group(2)

        block_name = block_names.get(block_name, block_name)

        print "Found %d chars of settings for block %s at %s-%s" % (len(block_data), block_name, m.start(0), m.end(0))

        handle_block(block_data, patches, block_name, lang)

        print "Have %d settings" % len(patches)

    return patches

sanitize_re = re.compile(r"{([0-9A-Z_]+)}")
setting_re = re.compile(r"{{(.*?)}, {(.*?)}},")

def handle_block (block_data, patches, block_name, strs) :
    print "Scanning for patches in block %s" % block_name
    print "Sanitizing nested brackets... (ugh)"
    
    block_data = sanitize_re.sub(r"\1", block_data)

    print "block data:\n\t%s" % block_data
    for m in setting_re.finditer(block_data) :
        nsd_spec = m.group(1)
        sleg_spec = m.group(2)

        print "\t nsd: %s\n\tsleg: %s" % (nsd_spec, sleg_spec)
        
        nsd_vars = [v.strip() for v in nsd_spec.split(', ')]
        sleg_vars = [v.strip() for v in sleg_spec.split(', ')]

# #define SDTG_GENERAL(name, sdt_cmd, sle_cmd, type, flags, guiflags, var, length, def, min, max, interval, full, str, proc, from, to) {NSD_GENERAL(name, def, sdt_cmd, guiflags, min, max, interval, full, str, proc), SLEG_GENERAL(sle_cmd, var, type | flags, length, from, to)}
#   #define NSD_GENERAL(name, def, cmd, guiflags, min, max, interval, many, str, proc) {name, (const void*)(def), cmd, guiflags, min, max, interval, many, str, proc}
#   #define SLEG_GENERAL(cmd, variable, type, length, from, to) {cmd, type, length, from, to, (void*)&variable}


        name, def_, sdt_cmd, guiflags, min, max, interval, many, str, proc = applyTypes(nsd_vars, 'str', 'cast', 'lit', 'flags', 'int', 'int', 'int', 'many', 'lit', 'lit')
        sle_cmd, type, length, from_, to, variable = applyTypes(sleg_vars, 'lit', 'flags', 'int', 'int', 'int', 'lit')
        en_str = strs.get(str, str)

        if '.' in name :
            cat, key = name.split('.')
        else :
            cat = block_name
            key = name

        config_name = (cat, name)
        
#  #define SDT_CONDVAR(base, var, type, from, to, flags, guiflags, def, min, max, interval, str, proc) SDT_GENERAL(#var, SDT_NUMX, SL_VAR, type, flags, guiflags, base, var, 1, def, min, max, interval, NULL, str, proc, from, to)
#  #define SDT_VAR(base, var, type, flags, guiflags, def, min, max, interval, str, proc) SDT_CONDVAR(base, var, type, 0, SL_MAX_VERSION, flags, guiflags, def, min, max, interval, str, proc)
# {{"map_x", (const void*)(8), SDT_NUMX, 0, 6, 11, 0, ((void *)0), STR_CONFIG_PATCHES_MAP_X, ((void *)0)}, {SL_VAR, SLE_UINT8 | SLF_SAVE_NO | SLF_NETWORK_NO, 1, 0, 255, (void*)__builtin_offsetof (Patches, map_x)}},
        if sdt_cmd == "SDT_NUMX" :
            def_ = parseVar(def_, 'int')

#            print "%25s: %d - %d : int %d < %d < %d, str=%s" % (name, from_, to, min, def_, max, en_str)

            patches[name] = (cat, key, 'int', (min, def_, max), en_str)
        
# {{"vehicle_speed", (const void*)(true), SDT_BOOLX, 0, 0, 1, 0, ((void *)0), STR_CONFIG_PATCHES_VEHICLESPEED, ((void *)0)}, {SL_VAR, SLE_BOOL | SLF_SAVE_NO | SLF_NETWORK_NO, 1, 0, 255, (void*)__builtin_offsetof (Patches, vehicle_speed)}},
        elif sdt_cmd == "SDT_BOOLX" :
            def_ = parseVar(def_, 'bool')

#            print "%25s: %d - %d: bool default=%s, str=%s" % (name, from_, to, def_, en_str)
            
            patches[name] = (cat, key, 'bool', (def_), en_str)

# {{"diff_custom", (const void*)(0), SDT_INTLIST, 0, 0, 0, 0, ((void *)0), STR_NULL, ((void *)0)}, {SL_ARR, (SLE_FILE_I16 | SLE_VAR_I32) | 0, 17, 0, 3, (void*)__builtin_offsetof (GameOptions, diff)}},
# {{"diff_custom", (const void*)(0), SDT_INTLIST, 0, 0, 0, 0, ((void *)0), STR_NULL, ((void *)0)}, {SL_ARR, (SLE_FILE_I16 | SLE_VAR_I32) | 0, 18, 4, 255, (void*)__builtin_offsetof (GameOptions, diff)}},
        elif sdt_cmd == "SDT_INTLIST" :
            patches[name] = (cat, key, 'intlist', (length), en_str)

# SDT_OMANY(GameOptions, landscape, SLE_UINT8, 0, 0, 0,     3, "normal|hilly|desert|candy", STR_NULL, NULL),
# #define SDT_OMANY(base, var, type, flags, guiflags, def, max, full, str, proc) SDT_CONDOMANY(base, var, type, 0, SL_MAX_VERSION, flags, guiflags, def, max, full, str, proc)
# #define SDT_CONDOMANY(base, var, type, from, to, flags, guiflags, def, max, full, str, proc) SDT_GENERAL(#var, SDT_ONEOFMANY, SL_VAR, type, flags, guiflags, base, var, 1, def, 0, max, 0, full, str, proc, from, to)
# {{"landscape", (const void*)(0), SDT_ONEOFMANY, 0, 0, 3, 0, "normal|hilly|desert|candy", STR_NULL, ((void *)0)}, {SL_VAR, SLE_UINT8 | 0, 1, 0, 255, (void*)__builtin_offsetof (GameOptions, landscape)}}
        elif sdt_cmd == "SDT_ONEOFMANY" :
            def_ = parseVar(def_, 'int')

            patches[name] = (cat, key, 'omany', (def_, many), en_str)

# {{"extmidi", (const void*)("timidity"), SDT_STRING, 0, 0, 0, 0, ((void *)0), STR_NULL, ((void *)0)}, {SL_STR, SLE_STRB | SLF_SAVE_NO | SLF_NETWORK_NO, (sizeof(((MusicFileSettings*)8)->extmidi)/sizeof(((MusicFileSettings*)8)->extmidi[0])), 0, 255, (void*)__builtin_offsetof (MusicFileSettings, extmidi)}},
        elif sdt_cmd == "SDT_STRING" :
            def_ = parseVar(def_, 'str')

            patches[name] = (cat, key, 'str', (def_), en_str)

# {{"display_opt", (const void*)((DO_SHOW_TOWN_NAMES|DO_SHOW_STATION_NAMES|DO_SHOW_SIGNS|DO_FULL_ANIMATION|DO_FULL_DETAIL|DO_TRANS_BUILDINGS|DO_WAYPOINTS)), SDT_MANYOFMANY, 0, 0, 0, 0, "SHOW_TOWN_NAMES|SHOW_STATION_NAMES|SHOW_SIGNS|FULL_ANIMATION|TRANS_BUILDINGS|FULL_DETAIL|WAYPOINTS", STR_NULL, ((void *)0)}, {SL_VAR, SLE_UINT8 | SLF_SAVE_NO | SLF_NETWORK_NO, 0, 0, 255, (void*)&_display_opt}},

        elif sdt_cmd == "SDT_MANYOFMANY" :
            def_ = parseVar(def_, 'many')

            patches[name] = (cat, key, 'mmany', (def_, many), en_str)

        else :
            print "Unknown type %s: %s + %s" % (sdt_cmd, 
                ', '.join(["%20s" % (v) for v in nsd_vars]),
                ', '.join(["%20s" % (v) for v in sleg_vars]),
            )

    return patches

def handle_categories (setting_gui_path, patches, lang) :
    lang = lang

    cat_names = {
        'ui':           'STR_CONFIG_PATCHES_GUI',
        'construction': 'STR_CONFIG_PATCHES_CONSTRUCTION', 
        'stations':     'STR_CONFIG_PATCHES_STATIONS', 
        'economy':      'STR_CONFIG_PATCHES_ECONOMY', 
        'ai':           'STR_CONFIG_PATCHES_AI', 
        'vehicles':     'STR_CONFIG_PATCHES_VEHICLES',
        'network':      'STR_NETWORK_MULTIPLAYER', 
        'gameopt':      'STR_02C3_GAME_OPTIONS', 
        'music':        'STR_01D3_SOUND_MUSIC', 
        'currency':     'STR_CURRENCY_WINDOW',
        'misc':         'STR_RES_OTHER',
        'pathfinding':  'STR_RES_PATHFINDING',
    }

    prefix_mapping = {
        'yapf': 'pathfinding',
        'npf': 'pathfinding',
    }

    cat_names = dict([(k, lang.get(s, k)) for k, s in cat_names.iteritems()])
    cat_patches = dict([(k, []) for k in cat_names])

    fh = open(setting_gui_path, 'r')
    data = fh.read()
    fh.close()

    ret = []
    
    # first, pull all of the patches in which are configureable in the normal patch GUI
    for mo in re.finditer(r"static const char \*_patches_(.*?)\[\] = \{(.*?)\};", data, re.DOTALL) :
        code, patches_raw = mo.group(1), mo.group(2)

        cat_name = cat_names[code]
        l =  []
        
        for mo in re.finditer(""""(.*?)",""", patches_raw) :
            patch_name = mo.group(1)

            if patch_name in patches :
                l.append(patches.pop(patch_name))
            else :
                print "skip %s, not found" % patch_name
        
        ret.append((cat_name, l))
    
    # them pull in the rest
    for patch_name, patch_data in patches.iteritems() :
        section, key, type, type_data, descr = patch_data
        
        for prefix, target in prefix_mapping.iteritems() :
            if patch_name.startswith(prefix) :
                section = target
                break

        if section in cat_patches :
            cat_patches[section].append(patch_data)
        else :
            cat_patches['misc'].append(patch_data)
    
    ret.extend([(n, p) for n, p in cat_patches.iteritems() if p])

    return ret

def calc_difficulties (setting_gui_path, lang, next) :
    fh = open(setting_gui_path, 'r')
    data = fh.read()
    fh.close()

    mo = re.search("static const GameSettingData _game_setting_info\[\] = {(.*?)};", data, re.DOTALL)

    if mo :
        setting_data = mo.group(1)

        settings = []

        diff_name_id = 'STR_6805_MAXIMUM_NO_COMPETITORS'

        for mo in re.finditer("{\s*(\d+),\s*(\d+),\s*(\d+),\s*(\w+)},", setting_data) :
            min = int(mo.group(1))
            max = int(mo.group(2))
            step = int(mo.group(3))
            base_value_str_id = mo.group(4)

            name = lang[diff_name_id]
            diff_name_id = next[diff_name_id]

            value_names = []
            
            if base_value_str_id != "STR_NULL" :
                value_str_id = base_value_str_id

                for i in xrange(min, max + 1, step) :
                    value_names.append(lang[value_str_id])
                    value_str_id = next[value_str_id]

            settings.append((name, min, max, step, value_names))
        
        levels = []
        
        diff_level_str_id = 'STR_6801_EASY'

        for i in xrange(0, 4) :
            levels.append(lang[diff_level_str_id])
            diff_level_str_id = next[diff_level_str_id]

        return settings, levels
    else :
        raise Exception("can't find difficulty setting info")

def save_patch_info (path, patch_info, diff_settings, diff_levels) :
    print "Saving patch/diff info to %s" % path

    fh = open(path, 'w')
    cPickle.dump((patch_info, diff_settings, diff_levels), fh)
    fh.close()

def main (version, legacy) :
    print "Handling OpenTTD version %s" % version
    
    if legacy :
        print "Using legacy paths..."
        lang_path = os.path.join(version, "lang", "english.txt")
        settings_path = os.path.join(version, "settings.c")
        settings_gui_path = os.path.join(version, "settings_gui.c")
        info_path = os.path.join(version, "cfg_info.dat")
    else :
        lang_path = os.path.join(version, "src", "lang", "english.txt")
        settings_path = os.path.join(version, "src", "settings.cpp")
        settings_gui_path = os.path.join(version, "src", "settings_gui.cpp")
        info_path = os.path.join(version, "bin", "cfg_info.dat")

    lang, next = load_lang(lang_path)
    patches = handle_settings(settings_path, lang)
    categories = handle_categories(settings_gui_path, patches, lang)
    diff_settings, diff_levels = calc_difficulties(settings_gui_path, lang, next)
    
    for name, patches in categories :
        print "%s:" % name

        for cat, name, type, data, str in patches :
            print "\t%8s.%-30s %4s %20s   %s" % (cat, name, type, data, str)
    
    print "Difficulty settings:"
    for name, min, max, step, value_names in diff_settings :
        print "%3d - %-3d @ %d  %s" % (min, max, step, name)

        for value in value_names :
            print "\t%s" % value

    save_patch_info(info_path, categories, diff_settings, diff_levels)

if __name__ == '__main__' :
    from sys import argv

    argv.pop(0)

    legacy = False

    if len(argv) > 1 :
        if argv[1] == "--legacy" :
            legacy = True
        else :
            print "Unknown argument '%s'" % argv[1]

    if argv :
        main(argv[0], legacy)
    else :
        print "specify the name of the new OpenTTD version as a command-line argument"

