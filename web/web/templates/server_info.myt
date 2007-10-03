% s = c.server_info

% if s :
<table id="server_info">
    <tr>
        <td colspan="4" id="server_title">
            <% s['server_name'] | h %>
        </td>
        <td>
            <p>Address</p>
            myottd.net:<% s['port'] %>
        </td>
        <td>
            <p>Clients</p>
            <% s['client_count'] %> / <% s['client_max'] %>
        </td>
        <td>
            <p>Companies</p>
            <% s['company_count'] %> / <% s['company_max'] %>
        </td>
        <td>
            <p>Version</p>
            <% s['version'] %>
        </td>
    </tr>
    <tr id="info_row">
        <td class="left_align">
            <img src="<% h.res_url("icons/landscape_normal.png") %>" />
        </td>
        <td>
            <p>Map Size</p>
            512x512
        </td>
        <td>
            <p>Map Type</p>
            Random Game
        </td>
        <td>
            <p>Game Start</p>
            <% h.fmtDatestamp(s['date_start']) %>
        </td>
        <td>
            <p>Game Date</p>
            <% h.fmtDatestamp(s['date_now']) %>
        </td>
        <td>
            <p>Specatators</p>
            <% s['spectator_count'] %> / <% s['spectator_max'] %>
        </td>
    </tr>
    <tr>
        <td colspan="10">
            <table id="company_list" cellspacing="1">
                <tr>
                    <th>#</th>
                    <th>Company</th>
                    <th>Start</th>
                    <th>Value</th>
                    <th>Balance</th>
                    <th>Income</th>
                    <th>Score</th>
                    <th colspan="5">Vehicles</th>
                    <th colspan="5">Stations</th>
                    <th>Players</th>
                    <th></th>
                </tr>
                <tr>
                    <td colspan="7"></td>
%  for veh_type in ('trains', 'trucks', 'busses', 'planes', 'ships')*2 :
                    <td><img src="<% h.res_url("icons/vehicle_%s.png" % veh_type) %>" /></td>
%  # end for
                    <td colspan="2"></td>
                </tr>
%  for i, c in enumerate(s['companies']) :
                <tr class="<% i % 2 and 'even' or 'odd' %>">
                    <td><% c['id'] %></td>
                    <td class="left_align"><% c['name'] | h %></td>
                    <td><% c['start_year'] %></td>
                    <td class="right_align"><% h.fmtMoney(c['value']) %></td>
                    <td class="right_align"><% h.fmtMoney(c['balance']) %></td>
                    <td class="right_align"><% h.fmtMoney(c['income']) %></td>
                    <td><% c['performance'] %></td>
                    <td><% c['veh_trains'] %></td>
                    <td><% c['veh_trucks'] %></td>
                    <td><% c['veh_busses'] %></td>
                    <td><% c['veh_planes'] %></td>
                    <td><% c['veh_ships'] %></td>                   
                    <td><% c['stn_trains'] %></td>
                    <td><% c['stn_trucks'] %></td>
                    <td><% c['stn_busses'] %></td>
                    <td><% c['stn_planes'] %></td>
                    <td><% c['stn_ships'] %></td>
                    <td><% " ".join([p['name'] for p in c['clients']]) %></td>
                    <td>
%   if c['password'] :
                        <img src="<% h.res_url("icons/locked.png") %>" />
%   # end if                        
                    </td>
                </tr>
%  # end for
            </table>
        </td>
    </tr>
</table>
% else :
<h1>Server offline</h1>
% # end if
