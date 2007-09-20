
<fieldset>
    <legend>Edit server</legend>

    <form action="<% h.url_for('me_server_edit', id=c.server_id) %>" method="POST">
        <label for="name">Name</label>
        <input type="text" name="name" value="<% c.server_name %>"/>
% if c.server_config_stale :
            <span class="current">"<% c.server_info['server_name'] %>"</span>
% # end if
        <br />

        <label for="version">Version</label>
        <select name="version">
            <% h.options_for_select(c.available_versions, c.server_version_id) %>
        </select>
% if c.server_config_stale :
            <span class="current">"<% c.server_info['version'] %>"</span>
% # end if
        <br/>

        <label for="advertise">Advertise</label>
        <input type="checkbox" name="advertise" value="1" class="checkbox" \
% if c.server_advertise :
checked="checked" \
% # end if
/>
        <br/>

        <label for="password">Password</label>
        <input type="text" name="password" value="<% c.server_password | h %>" />
% if c.server_config_stale :
            <span class="current">"<% c.server_info['password'] %>"</span>
% # end if
        <br/>

        <input type="submit" name="action" value="Apply" />
        <br />

% if c.server_config_stale :
        <strong>You must restart your server for the changes to take effect</strong>
% # end if
    </form>
</fieldset>

<fieldset>
    <legend>Controls</legend>

    <form action="<% h.url_for('me_server_edit', id=c.server_id) %>" method="POST">
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

    <form action="<% h.url_for('me_server_newrandom', id=c.server_id) %>" method="POST">
        <label for="climate">Climate</label>
        <select name="climate">
            <% h.options_for_select(('normal', 'desert', 'hilly', 'candy'), c.server_info['climate']) %>
        </select>
        <br/>

% map_geom_opts = [(2**x, x) for x in xrange(6, 11)]
        <label for="map_x map_y">Map Size</label>
        <select name="map_x" class="thin">
            <% h.options_for_select(map_geom_opts, c.server_info['map_x']) %>
        </select> x <select name="map_y" class="thin">
            <% h.options_for_select(map_geom_opts, c.server_info['map_y']) %>
        </select>
        <br/>

        <input type="submit" value="Start" />
        <br/>
    </form>
</fieldset>

<& server_info.myt &>
