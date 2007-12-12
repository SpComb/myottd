<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
    <head>
        <title>Image tiles</title>
        <script src="/static/prototype.js" type="text/javascript"></script>
        <script src="/static/scriptaculous.js" type="text/javascript"></script>
        <script src="/static/tiles.js" type="text/javascript"></script>
        <link rel="Stylesheet" type="text/css" href="static/style.css">
    </head>
    <body>
        <div id="wrapper">
            <div id="viewport" style="width: ${viewport_width}px; height: ${viewport_height}px">
                <div id="substrate"></div>
            </div>

            <div id="zoom">
                <input type="button" id="zoom_in" onclick="zoom(-1)" value="In" /> 
                    &lt;-- zoom --&gt; 
                <input type="button" id="zoom_out" onclick="zoom(1)" value="Out" />
                <br/>

                <a href="#" id="page_link">Link to this location</a>
            </div>

            <div id="help">
                <p>
% if mode == "openttd" :                
A view into a real OpenTTD game. View updates when you drag the map. Join the OpenTTD server at <strong>myottd.net:7199</strong>.
% elif mode == "image" :
A selection of large images that you can, like, scroll around. Use the dropdown below the viewport to select the image to view
% endif
                </p>
                <p>
<strong>Moving around</strong>: Simply drag the map around with the left mouse button held down.
                </p>
                <p>
<strong>Zooming</strong>. Either use the In/Out buttons, the mouse wheel (scroll up to zoom in, scroll down to zoom out), or double-click on the map.
                </p>
            </div>

            <table id="vehicles_list" cellspacing="0" cellpadding="0">
            </table>
        </div>

        <script type="text/javascript">
            init();
% if mode == "openttd" :        
            load(${start_col}, ${start_row}, ${tile_width}, ${tile_height}, ${initial_zoom}, ${zoom_min}, ${zoom_max}, null, null, true);
            vehicle_list();
% elif mode == "image" :
            load_image_list();
% else :
            <% raise ValueError(mode) %>
% endif            
        </script>
    </body>
</html>
