<h1>Game Configuration</h1>

<form action="<% h.url_for('admin_server_config', id=c.id) %>" method="POST">

% gameopt_currency = None
% cust_diff_values = None
% diff_level = None
% for category, patches in c.config :
<fieldset class="config">
    <legend><% category.capitalize() %></legend>
    
    <table>
%   for name, type, type_data, value, desc in patches :
%       meta = None
%       if name == "gameopt.diff_custom" :
%           cust_diff_values = value
%           continue
%       elif name == "gameopt.diff_level" :
%           diff_level = value
%           continue
%       elif name == "gameopt.currency" :
%           gameopt_currency = value
%       # end if
        <tr>
            <td class="value">
%       if type == 'bool' :
                <input type="hidden" name="bb_<% name %>" value="0" />
                <input type="checkbox" name="b_<% name %>" value="1" class="checkbox" \
%           if value :
checked="checked" \
%           # end if
>
%           value = value and 'On' or 'Off'
%           meta = type_data and 'On' or 'Off'
%       elif type == 'int' :
                <input type="text" name="i_<% name %>" value="<% value %>" />
%           min, default, max = type_data
%           meta = "%d &#8804; %d &#8804; %d" % (min, default, max)
%       elif type == 'str' :
                <input type="text" name="t_<% name %>" value="<% value %>" />
%       elif type == 'intlist' :
%           for i, v in enumerate(value) :
                <input type="text" name="il_<% name %>_<% i %>" value="<% v %>" class="thin" />
%           # end for
%       elif type in ('omany', 'mmany') :
                <select name="<% type[0] %>m_<% name %>" \
%           if type == 'mmany' :
multiple="multiple" \
%           # end if
>
                    <% h.options_for_select(type_data[1], value) %>
                </select>            
%           meta = type_data[1][type_data[0]]
%       else :
%           raise ValueError(type)
%       # end if
            </td>
            <td class="meta">
%       if meta :
                <% meta.replace('-1 ', '? ') %>
%       else :
                &nbsp;
%       # end if            
            </td>
            <td>
%       if desc :            
%           if '%s' in desc :
                <% desc % str(value) | h %>
%           else :
                <% desc | h %>
%           # end if        
%       else :
                <% name | h %>
%       # end if
            </td>
        </tr>
%   # end fpr
    </table>
</fieldset>

% # end for

<fieldset>
    <legend>Difficulty</legend>
    
    <table>
        <tr>
            <td>
                <select name="i_gameopt.diff_level">
                    <% h.options_for_select([(n, i) for i, n in enumerate(c.diff_levels)], diff_level) %>
                </select>
            </td>
            <td>
                Difficulty level
            </td>
        </tr>
        <tr>
            <td colspan="2"><hr /></td>
        </tr>
% for i, (name, min, max, step, value_names) in enumerate(c.diff) :
%   value = cust_diff_values[i]
        <tr>
            <td>
%   if value_names :
                <select name="il_gameopt.diff_custom_<% i %>">
                    <% h.options_for_select([(n, i) for i, n in enumerate(value_names)], value) %>
                </select>
%   else :
%       if '<currency>' in name :
%           name = name.replace('<currency>', '')
            <select name="il_gameopt.diff_custom_<% i %>">
                <% h.options_for_select([(i*1000, i) for i in xrange(min, max, step)], value) %>
            </select> &pound;
%       elif '<percentage>' in name :
%           name = name.replace('<percentage>', '')
            <select name="il_gameopt.diff_custom_<% i %>">
                <% h.options_for_select(xrange(min, max), value) %>
            </select> %
%       else :
            <input type="text" name="il_gameopt.diff_custom_<% i %>" value="<% value %>" />
%       # end if            
%   # end if
            </td>
            <td>
                <% name.rstrip(': ') %>
            </td>
        </tr>
% # end if
    </table>
</fieldset>

<input type="submit" value="Apply Config" /> <strong>Applying the configuration will cause the server to restart</strong>
</form>
<form action="<% h.url_for('admin_server', id=c.id) %>" method="GET"><input type="submit" value="Cancel" /></form>


