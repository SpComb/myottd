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
A view into a real OpenTTD game. View updates when you drag the map. Join the OpenTTD server at <strong>myottd.net:7199</strong>.
                </p>
                <p>
<strong>Moving around</strong>: You can drag the map around with the left mouse button held down, or alternatively double-click on the map to center on that location (complete with fancy scroll effect).
                </p>
                <p>
<strong>Zooming</strong>. Use either the In/Out buttons, or the mouse wheel (scroll up to zoom in, scroll down to zoom out, this also centers the map on where the mouse is).
                </p>
            </div>

            <table id="vehicles_list" cellspacing="0" cellpadding="0">
            </table>
        </div>

        <script type="text/javascript">init(${start_col}, ${start_row}, ${tile_width}, ${tile_height}, ${initial_zoom}, ${zoom_min}, ${zoom_max});</script>
    </body>
</html>
