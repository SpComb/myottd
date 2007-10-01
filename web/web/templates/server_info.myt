% s = c.server_info

% if s :
<h1><% s['owner'] | h %>'s <% s['server_name'] | h %></h1>

<table class="info_table">
    <tr>
        <th>Owner</th>
        <td><% s['owner'] | h %></td>
    </tr>
    <tr>
        <th>Server name</th>
        <td><% s['real_server_name'] | h %></td>
    </tr>
    <tr>
        <th>Connection info</th>
        <td>myottd.net:<% s['server_port'] %></td>
    </tr>
    <tr>
        <th>Version</th>
        <td><% s['version'] %></td>
    </tr>
    <tr>
        <th>Status</th>
        <td>
%   if s['running'] :
            Running
%   # end if
        </td>
    </tr>
    <tr>
        <th>Password</th>
        <td>
%   if s['has_password'] :
            <strong>Yes</strong>
%   else :
            No
%   # end if
        </td>
    </tr>
%   if s['running'] :    
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
        <th>Game Type</th>
        <td>
%       if s['is_random_map'] :
            Random map
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
%       elif s['save_date'] or s['game_id'] is not None :
            Savegame
        </td>
    </tr>
    <tr>
        <th>Savegame</th>
        <td>
%           if s['game_id'] is False :
            Autosave
%           else :           
            Game <% s['game_id'] %> - <% h.fmtDatestamp(s['save_date']) %>
%           # end if            
        </td>
    </tr>
%       elif s['custom_save'] :
            Uploaded savegame
        </td>
    <tr>
    <tr>
        <th>Savegame</th>
        <td>
            <% s['custom_save'] | h %>
        </td>
    </tr>
%       else :
            ???
        </td>
    </tr>
%       # end if
    <tr>
        <th>Current Date</th>
        <td><% h.fmtDatestamp(s['cur_date']) %></td>
    </tr>
%   # end if
</table>

%   if s['running'] :    
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
%       for c in s['companies'] :
    <tr>
        <td><% c['pid'] %></td>
        <td><% c['company_name'] | h %></td>
        <td><% c['color'] %></td>
        <td><% c['money'] %></td>
        <td><% c['loan'] %></td>
        <td><% c['value'] %></td>
        <td><% c['year_founded'] %></td>
        <td>T:<% c['trains'] %>, R:<% c['road_vehicles'] %>, P:<% c['planes'] %>, S:<% c['ships'] %></td>
    </tr>
%               for p in c['players'] :
    <tr>
        <td colspan="2"></td>
        <td><% p['cid'] %></td>
        <td colspan="4"><% p['name'] | h %></td>
        <td></td>
    </tr>
%               # end for
%       # end for
    <tr>
        <th colspan="2">Players:</th>
        <th>ID#</th>
        <th colspan="4">Name</th>
        <td></td>
    </tr>
</table>

%   # end if
% else :
<h1>Server offline</h1>
% # end if

