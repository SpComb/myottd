<%python>
    # sort the servers list
    def my_cmp (s1, s2) :
        return cmp((s1['owner_id'], s1['server_name']), (s2['owner_id'], s2['server_name']))

    c.servers.sort(cmp=my_cmp)

    # how many servers does each player have?
    player_servers = {}

    for s in c.servers :
        uid = s['owner_id']
        player_servers[uid] =  player_servers.get(uid, 0) + 1

</%python>

<table id="server_list" cellspacing="1">
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
% uid = show_username = None
% i = -1
% for s in c.servers :
%   if c.view_user and s['owner_id'] != c.view_user.id :
%       continue
%   elif uid != s['owner_id'] :
%       uid = s['owner_id']
%       i += 1
%       show_username = True
%   else :
%       show_username = False
%   # end if
    <tr class="<% i % 2 and 'even' or 'odd' %>">
%   if not c.view_user and show_username :
            <td rowspan="<% player_servers[uid] %>">
                <a href="<% h.url_for('user', sub_domain=s['owner']) %>"><% s['owner'] %></a>
            </td>
%   # end if        
        <td>
            <a href="<% h.url_for('server', sub_domain=s['owner'], url=s['tag']) %>"><% s['tag'] and "%s - " % s['tag'] or '' %><% s['_server_name'] %></a>
        </td>
        <td>
            <% s['client_count'] %> / <% s['client_max'] %>
        </td>
        <td>
            <% s['company_count'] %> / <% s['company_max'] %>
        </td>
        <td>
            <% s['version'] %>
        </td>
        <td>
%       if s['password'] :
            <img src="<% h.res_url("icons/lock.png") %>" />
%       # end if
        </td>
    </tr>
% # end for
</table>


