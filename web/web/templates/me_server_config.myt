<h1>Configuration of server <% c.server_name | h %></h1>

<form action="<% h.url_for('me_server_config', id=c.id) %>" method="POST">

% gameopt_currency = None
% cust_diff_values = None
% diff_level = None
% for category, patches in c.config :
<fieldset class="config">
    <legend><% category.capitalize() %></legend>
    
    <table>
%   for name, type, type_data, value, desc in patches :
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
        <input type="checkbox" name="<% name %>" class="checkbox" \
%           if value :
checked="checked" \
%           # end if
>
%           value = value and 'On' or 'Off'
%       elif type == 'int' :
        <input type="text" name="<% name %>" value="<% value %>" />
%       elif type == 'str' :
        <input type="text" name="<% name %>" value="<% value %>" />
%       elif type == 'intlist' :
%           for i, v in enumerate(value) :
        <input type="text" name="<% name %>_<% i %>" value="<% v %>" class="thin" />
%           # end for
%       elif type in ('omany', 'mmany') :
            <select name="<% name %>" \
%           if type == 'mmany' :
multiple="multiple" \
%           # end if
>
                <% h.options_for_select(type_data[1], value) %>
            </select>            
%       else :
%           raise ValueError(type)
%       # end if
            </td>
            <td>
%       if desc :            
%           if '%s' in desc :
        <% desc % str(value) %>
%           else :
        <% desc %>
%           # end if        
%       else :
        <% name %>
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
                <select name="diff_level">
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
                <select name="diff_custom_<% i %>">
                    <% h.options_for_select([(n, i) for i, n in enumerate(value_names)], value) %>
                </select>
%   else :
%       if '<currency>' in name :
%           name = name.replace('<currency>', '')
            <select name="diff_custom_<% i %>">
                <% h.options_for_select([(i*1000, i) for i in xrange(min, max, step)], value) %>
            </select> &pound;
%       elif '<percentage>' in name :
%           name = name.replace('<percentage>', '')
            <select name="diff_custom_<% i %>">
                <% h.options_for_select(xrange(min, max), value) %>
            </select> %
%       else :
            <input type="text" name="diff_custom_<% i %>" value="<% value %>" />
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

</form>
