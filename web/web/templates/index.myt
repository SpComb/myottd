% if c.view_user :
<h1><% c.view_user.username.capitalize() %>'s servers</h1>
% else :
<h1>Servers</h1>
% # end if

<%python>
    # sort the servers list
    def my_cmp (s1, s2) :
        return cmp((s1['owner_uid'], s1['server_url']), (s2['owner_uid'], s2['server_url']))

    c.servers.sort(cmp=my_cmp)
</%python>

<table>
    <tr>
% if not c.view_user :    
        <th>Owner</th>
% # end if        
        <th>Name</th>
        <th>Clients</th>
        <th>Companies</th>
        <th>Version</th>
        <th>&nbsp;</th>
    </tr>
% uid = None
% for s in c.servers :
%   if c.view_user and s['owner_uid'] != c.view_user.id :
%       continue
%   # end if
    <tr>
%   if not c.view_user :
        <td>
%       if uid != s['owner_uid'] :
%           uid = s['owner_uid']
            <a href="<% h.url_for('user', sub_domain=s['owner']) %>"><% s['owner'] %></a>
%        else :
            &nbsp;
%        # end if
        </td>
%   # end if        
        <td>
            <a href="<% h.url_for('server', sub_domain=s['owner'], url=s['server_url']) %>"><% s['server_url'] and "%s - " % s['server_url'] or '' %><% s['server_name'] %></a>
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


