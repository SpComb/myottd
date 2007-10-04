<script type="text/javascript">
    function changed () {
        var f = document.forms[0]

        var s = "<% c.view_user.username %>.myottd.net" + (f.url.value ? ("/" + f.url.value) : "") + " - " + f.name.value;

        var d = document.getElementById("output_name");

        d.innerHTML = s;
    }
</script>

% s = c.server_info
% if s :
<fieldset>
    <legend>Server options</legend>

    <form action="<% h.url_for('admin_server_edit', id=c.server_id) %>" method="POST">
        <label for="tag">Tag</label>
        <input type="text" name="tag" value="<% c.server_info['tag_part'] | h %>" onchange="changed()" />
        <br />

        <label for="name">Name</label>
        <input type="text" name="name" value="<% c.server_info['name_part'] | h %>" onchange="changed()" />
        <br />

        <label for="version">Version</label>
        <select name="version">
            <% h.options_for_select(c.available_versions, c.server_info['version_id']) %>
        </select>
%   if c.server_info['version_name'] != c.server_info['version'] :
            <span class="current">You must restart for this to take effect</span>
%   # end if
        <br/>

        <label for="password">Password</label>
        <input type="text" name="password" value="<% c.server_info['password_value'] | h %>" />
        <span class="hint">No whitespace at the beginning/end</span>
        <br/>
        
        <p class="form_hint">Server name preview: <strong id="output_name"><% c.view_user.username %>.myottd.net<% c.server_info['tag_part'] and "/%s" % c.server_info['tag_part'] or '' %> - <% c.server_info['name_part'] %></strong></p>

        <input type="submit" name="action" value="Apply" />
        <br />

    </form>
    
    <hr/>

    <a href="<% h.url_for('admin_server_config', id=c.id) %>">Game Configuration</a>
</fieldset>
% # end if

<fieldset>
    <legend>Controls</legend>

    <form action="<% h.url_for('admin_server_edit', id=c.server_id) %>" method="POST">
% if c.server_info :
        <input type="submit" name="action" value="Stop" />
        <br />

        <input type="submit" name="action" value="Restart" />
        <br/>
% else :
        <input type="submit" name="action" value="Start" />
        <br/>
% # end if

    </form>
</fieldset>

% if s :
<fieldset>
    <legend>Start new random game</legend>

    <form action="<% h.url_for('admin_server_newrandom', id=c.server_id) %>" method="POST">
        <label for="gameopt.landscape">Climate</label>
        <select name="gameopt.landscape">
            <% h.options_for_select(h.climate_opts, c.server_info['map_type']) %>
        </select>
        <br/>

%   map_geom_opts = [(2**x, x) for x in xrange(6, 11)]
        <label for="patches.map_x patches.map_y">Map Size</label>
        <select name="patches.map_x" class="thin">
            <% h.options_for_select(map_geom_opts, h.mapSize2value(c.server_info['map_width'])) %>
        </select> x <select name="patches.map_y" class="thin">
            <% h.options_for_select(map_geom_opts, h.mapSize2value(c.server_info['map_height'])) %>
        </select>
        <br/>

        <input type="submit" value="Start" />
        <br/>
    </form>
</fieldset>

%   cur_game_id = str(s['game_id'])
%   cur_save_ds = s['save_date']
<fieldset>
    <legend>Savegames</legend>
    
    <form action="<% h.url_for('admin_server_savegames', id=c.server_id) %>" method="POST" enctype="multipart/form-data">
        <input type="submit" name="save" value="Save" />
        <br/>

    <table class="savegames">
        <tr>
            <th>Game</th>
            <th>Savegame</th>
            <th>Action</th>
        </tr>
%   for game_id, saves in s['games'].iteritems() :
        <tr>
%       if game_id == cur_game_id :
            <th rowspan="<% len(saves) + 1 %>" id="current_game">
%       else :
            <th rowspan="<% len(saves) + 1 %>">
%       # end if        
                Game <% game_id %>
            </th>
<!--            
            <td><input type="submit" name="continue_<% game_id %>" value="Continue" /></td>
            <td>&nbsp;</td>
-->
        </tr>
%       for save_ds in saves :
%           if game_id == cur_game_id and save_ds == cur_save_ds :
        <tr id="current_save">
%           else :
        <tr>
%           # end if        
            <td><% h.fmtDatestamp(save_ds) %></td>
            <td>
%           if game_id == cur_game_id and save_ds == cur_save_ds :
                &nbsp;
%           else :
                <input type="submit" name="load_<% game_id %>_<% save_ds %>" value="Load" />
%           # end if                        
            </td>
        </tr>
%       # end if
%   # end for
    </table>
    
    <hr style="margin: 10px 0px 10px 0px;" />
    
    <label for="upload">Load Savegame</label>
    <input type="file" name="upload" />
    <br/>

    <input type="submit" value="Load" />


    </form>
</fieldset>

<fieldset id="newgrfs">
    <legend>NewGRFs</legend>
    
    <form action="<% h.url_for('admin_server_newgrfs', id=c.id) %>" method="POST" enctype="multipart/form-data">
%   if s['newgrf_config'] :
    <table class="newgrfs">
        <tr>
            <th>Enabled</th>
            <th>NewGRF name</th>
            <th>Params</th>
        </tr>
%       for filename, loaded, params in s['newgrf_config'] :
        <tr>
            <input type="hidden" name="newgrfs[]" value="<% filename %>" />
            <td><input type="checkbox" name="<% filename %>_enabled" <% loaded and 'checked="checked" ' or '' %>value="1" class="checkbox" /></td>
            <td><% filename %></td>
            <td><input type="text" name="<% filename %>_params" value="<% params or '' %>"></td>
        </tr>
%       # end for
        <tr>
            <td colspan="3"><input type="submit" value="Apply" %> <span class="hint">will cause server restart</span></td>
        </tr>
    </table>
%   else :
    <strong>No NewGRFs loaded</strong>
%   # end if    

    <hr style="margin: 10px 0px 10px 0px;" />
    
    <label for="upload">Upload GRF</label>
    <input type="file" name="upload" />
    <br/>

    <input type="submit" value="Upload" />

    </form>
</fieldset>
% # end if

<& server_info.myt &>
