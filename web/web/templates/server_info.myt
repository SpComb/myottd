% s = c.server_info
<h1>Info on server <% s['server_name'] %></h1>

<table class="info_table">
    <tr>
        <th>Owner</th>
        <td><% s['owner'] %></td>
    </tr>
    <tr>
        <th>Server name</th>
        <td>MyOTTD - <% s['owner'] %> - <% s['server_name'] %></td>
    </tr>
    <tr>
        <th>Connection info</th>
        <td>zapotekII.paivola.fi:<% s['server_port'] %></td>
    </tr>
    <tr>
        <th>Version</th>
        <td><% s['version'] %></td>
    </tr>
    <tr>
        <th>Status</th>
        <td>
% if s['running'] :
            Running
% # end if
        </td>
    </tr>
    <tr>
        <th>Password</th>
        <td>
% if s['has_password'] :
            <strong>Yes</strong>
% else :
            No
% # end if
        </td>
    </tr>
% if s['running'] :    
    <tr>
        <th>Clients</th>
        <td>
            <% s['cur_clients'] %> / <% s['max_clients'] %>
        </td>
    </tr>
    <tr>
        <th>Companies</th>
        <td>
            <% s['cur_companies'] %> / <% s['max_companies'] %>
        </td>
    </tr>
    <tr>
        <th>Spectators</th>
        <td>
            <% s['cur_spectators'] %> / <% s['max_spectators'] %>
        </td>
    </tr>
    <tr>
        <th>Climate</th>
        <td>
            <% h.climateName(s['climate']) %>    
        </td>
    </tr>
    <tr>
        <th>Map size</th>
        <td>
            <% h.mapSize(s['map_x']) %> x <% h.mapSize(s['map_y']) %>
        </td>
    </tr>   
% # end if
</table>

<h1>Company List</h1>
<table border="1">
    <tr>
        <th>ID#</th>
        <th>Name</th>
        <th>Color</th>
        <th>Balance</th>
        <th>Loan</th>
        <th>Value</th>
        <th>Inagurated</th>
        <th>Vehicle Fleet</th>
    </tr>
% for c in s['companies'] :
    <tr>
        <td><% c['pid'] %></td>
        <td><% c['company_name'] %></td>
        <td><% c['color'] %></td>
        <td><% c['money'] %></td>
        <td><% c['loan'] %></td>
        <td><% c['value'] %></td>
        <td><% c['year_founded'] %></td>
        <td>T:<% c['trains'] %>, R:<% c['road_vehicles'] %>, P:<% c['planes'] %>, S:<% c['ships'] %></td>
    </tr>
%   for p in c['players'] :
    <tr>
        <td colspan="2"></td>
        <td><% p['cid'] %></td>
        <td colspan="4"><% p['name'] %></td>
        <td></td>
    </tr>
%   # end for
% # end for
    <tr>
        <th colspan="2">Players:</th>
        <th>ID#</th>
        <th colspan="4">Name</th>
        <td></td>
    </tr>
</table>

