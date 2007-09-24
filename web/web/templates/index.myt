<h1>Servers</h1>

<table>
    <tr>
        <th>Owner</th>
        <th>Name</th>
        <th>Clients</th>
        <th>Companies</th>
        <th>Version</th>
        <th>&nbsp;</th>
    </tr>
% uid = None
% for s in c.servers :
    <tr>
        <td>
%   if uid != s['owner_uid'] :
%       uid = s['owner_uid']
            <% s['owner'] %>
%   else :
            &nbsp;
%   # end if
        </td>
        <td>
            <a href="<% h.url_for('server_info', id=s['id']) %>"><% s['server_url'] and "%s - " % s['server_url'] or '' %><% s['server_name'] %></a>
        </td>
        <td>
            <% s['cur_clients'] %> / <% s['max_clients'] %>
        </td>
        <td>
            <% s['cur_companies'] %> / <% s['max_companies'] %>
        </td>
        <td>
            <% s['version'] %>
        </td>
        <td>
%   if s['has_password'] :
            [password]
%   # end if
        </td>
    </tr>
% # end for
</table>


