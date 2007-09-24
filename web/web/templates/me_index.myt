% if c.user_servers :
<h1>Your servers</h1>

<table>
    <tr>
        <th>Name</th>
        <th>Port</th>
        <th>Advertise</th>
        <th>Status</th>
        <th>Version</th>
    </tr>
%   for id, url, name, port, advertise, status, version in c.user_servers :
    <tr>
        <td><a href="<% h.url_for('admin_server', id=id, sub_domain=c.sub_domain) %>"><% h.serverName(c.view_user.username, url, name) %></a></td>
        <td><% port %></td>
        <td><% advertise %></td>
        <td><% status.title() %></td>
        <td><% version %></td>
    </tr>
%   # end for
</table>
% else :
<h1>No servers yet</h1>
% # end if

<script type="text/javascript">
    function changed () {
        var f = document.forms[0]

        var s = "<% c.view_user.username %>.myottd.net" + (f.url.value ? ("/" + f.url.value) : "") + " - " + f.name.value;

        var d = document.getElementById("output_name");

        d.innerHTML = s;
    }
</script>

<fieldset>
    <legend>Create Server</legend>

    <form action="<% h.url_for('admin_server_add') %>" method="POST">
        <label for="url">Url</label>
        <input type="text" name="url" onchange="changed()" />
        <span class="hint">letters, numbers, some punctuation only, may be blank</span>
        <br/>

        <label for="name">Title</label>
        <input type="text" name="name" onchange="changed()" />
        <span class="hint">required</span>
        <br/>

        <label for="version">Version</label>
        <select name="version">
            <% h.options_for_select(c.available_versions) %>
        </select>
        <br/>

<!--
        <label for="advertise">Advertise</label>
        <input type="checkbox" name="advertise" value="1" class="checkbox" checked="checked" />
        <br/>
-->

        <input type="submit" value="Add" />

        <p class="form_hint">Server name: <strong id="output_name"><% c.view_user.username %>.myottd.net/&lt;url&gt; - &lt;title&gt;</strong></p>
    </form>
</fieldset>


