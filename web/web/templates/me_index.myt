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
%   for id, url, name, port, enabled, version in c.user_servers :
    <tr>
        <td><a href="<% h.url_for('admin_server', id=id, sub_domain=c.sub_domain) %>"><% h.serverName(c.view_user.username, url, name) %></a></td>
        <td><% port %></td>
        <td><% enabled and 'Enabled' or 'Disabled' %></td>
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

        var s = "<% c.view_user.username %>.myottd.net" + (f.tag.value ? ("/" + f.tag.value) : "") + " - " + f.name.value;

        var d = document.getElementById("output_name");

        d.innerHTML = s;
    }
</script>

<fieldset>
    <legend>Create Server</legend>

    <form action="<% h.url_for('admin_server_add') %>" method="POST">
        <label for="tag">Tag</label>
        <input type="text" name="tag" onchange="changed()" />
        <span class="hint">A short tag to tell servers apart. Letters, numbers, some punctuation only, may be blank for one server</span>
        <br/>

        <label for="name">Title</label>
        <input type="text" name="name" onchange="changed()" />
        <span class="hint">A suitable descriptive title. Required</span>
        <br/>

        <label for="version">Version</label>
        <select name="version">
            <% h.options_for_select((h.format_version(name, version), id) for  (name, version, id) in c.available_versions) %>
        </select>
        <br/>

<!--
        <label for="advertise">Advertise</label>
        <input type="checkbox" name="advertise" value="1" class="checkbox" checked="checked" />
        <br/>
-->

        <input type="submit" value="Add" />

        <p class="form_hint">Server name: <strong id="output_name"><% c.view_user.username %>.myottd.net/&lt;tag&gt; - &lt;title&gt;</strong></p>
    </form>
</fieldset>


