<h1>Your servers</h1>

<table>
    <tr>
        <th>ID</th>
        <th>Name</th>
        <th>Port</th>
        <th>Advertise</th>
        <th>Status</th>
        <th>Version</th>
    </tr>
% if c.user_servers :
%   for id, name, port, advertise, status, version in c.user_servers :
    <tr>
        <td><a href="<% h.url_for('me_server', id=id) %>"><% id %></a></td>
        <td><% name %></td>
        <td><% port %></td>
        <td><% advertise %></td>
        <td><% status.title() %></td>
        <td><% version %></td>
    </tr>
%   # end if
% else :
    <tr>
        <td colspan="5" style="text-align: center">No servers</td>
    </tr>
% # end if
</table>

<fieldset>
    <legend>Create Server</legend>

    <form action="<% h.url_for('me_server_add') %>" method="POST">
        <label for="name">Name</label>
        <input type="text" name="name" />
        <br/>

        <label for="version">Version</label>
        <select name="version">
            <% h.options_for_select(c.available_versions) %>
        </select>
        <br/>

        <label for="advertise">Advertise</label>
        <input type="checkbox" name="advertise" value="1" class="checkbox" checked="checked" />
        <br/>

        <input type="submit" value="Add" />
    </form>
</fieldset>

