<script type="text/javascript">
    function changed () {
        var f = document.forms[0]

        var s = "<% c.view_user.username %>.myottd.net" + (f.url.value ? ("/" + f.url.value) : "") + " - " + f.name.value;

        var d = document.getElementById("output_name");

        d.innerHTML = s;
    }
</script>

<fieldset>
    <legend>Server options</legend>

    <form action="<% h.url_for('admin_server_edit', id=c.server_id) %>" method="POST">
        <label for="url">Url</label>
        <input type="text" name="url" value="<% c.server_url | h %>" onchange="changed()" />
% if c.server_config_stale and c.server_info :
            <span class="current">"<% c.server_info['server_url'] | h %>"</span>
% # end if
        <br />

        <label for="name">Title</label>
        <input type="text" name="name" value="<% c.server_name | h %>" onchange="changed()" />
% if c.server_config_stale and c.server_info :
            <span class="current">"<% c.server_info['server_name'] | h %>"</span>
% # end if
        <br />

        <label for="version">Version</label>
        <select name="version">
            <% h.options_for_select(c.available_versions, c.server_version_id) %>
        </select>
% if c.server_config_stale and c.server_info :
            <span class="current">"<% c.server_info['version'] %>"</span>
% # end if
        <br/>

<!--
        <label for="advertise">Advertise</label>
        <input type="checkbox" name="advertise" value="1" class="checkbox" \
% if c.server_advertise :
checked="checked" \
% # end if
/>
        <br/>
-->

        <label for="password">Password</label>
        <input type="text" name="password" value="<% c.server_password | h %>" />
% if c.server_config_stale and c.server_info :
            <span class="current">"<% c.server_info['password'] | h %>"</span>
% # end if
        <br/>

        <input type="submit" name="action" value="Apply" />
        <br />

% if c.server_config_stale :
        <strong>You must restart your server for the changes to take effect</strong>
% # end if
    </form>
    
    <p class="form_hint">Server name preview: <strong id="output_name"><% c.view_user.username %>.myottd.net<% c.server_url and "/%s" % c.server_url or '' %> - <% c.server_name %></strong></p>

    <a href="<% h.url_for('admin_server_config', id=c.id) %>">Edit game configuration</a>
</fieldset>

<fieldset>
    <legend>Controls</legend>

    <form action="<% h.url_for('admin_server_edit', id=c.server_id) %>" method="POST">
        <label for="status">Status</label>
        <span id="status"><% c.server_status %></span>
        <br />

% if c.server_status == 'online' :
        <input type="submit" name="action" value="Stop" />
        <br />

        <input type="submit" name="action" value="Restart" />
        <br/>
% elif c.server_status == 'offline' :
        <input type="submit" name="action" value="Start" />
        <br/>
% # end if

    </form>
</fieldset>

<fieldset>
    <legend>Start new random game</legend>

    <form action="<% h.url_for('admin_server_newrandom', id=c.server_id) %>" method="POST">
        <label for="gameopt.landscape">Climate</label>
        <select name="gameopt.landscape">
            <% h.options_for_select(h.climate_opts, c.server_info.get('climate', None)) %>
        </select>
        <br/>

% map_geom_opts = [(2**x, x) for x in xrange(6, 11)]
        <label for="patches.map_x patches.map_y">Map Size</label>
        <select name="patches.map_x" class="thin">
            <% h.options_for_select(map_geom_opts, c.server_info.get('map_x', None)) %>
        </select> x <select name="patches.map_y" class="thin">
            <% h.options_for_select(map_geom_opts, c.server_info.get('map_y', None)) %>
        </select>
        <br/>

        <input type="submit" value="Start" />
        <br/>
    </form>
</fieldset>

% s = c.server_info
% if s :
%   cur_game_id = str(s['game_id'])
%   cur_save_ds = s['save_date']
<fieldset>
    <legend>Savegames</legend>
    
    <form action="<% h.url_for('admin_server_savegames', id=c.server_id) %>" method="POST">
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
%   # end if
    </table>

    </form>
</fieldset>
% # end if

<& server_info.myt &>
