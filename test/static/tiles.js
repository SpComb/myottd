// our initial (col, row) position
var g_x, g_y;

// how many pixels (wide, high) the viewport is
var g_w, g_h;

// how (wide, high) a tile is
var g_tw, g_th;

// half of viewport width/height
var g_w_half, g_h_half;

// the Draggable substrate, we get our current offset from this
var g_draggable;

// random debugging crap
var g_debug, g_debug_enabled;

// our current zoom level
var g_z;

// minimum and maximum zoom levels
var g_z_min, g_z_max;

// the viewport and substrate divs
var viewp, subs;

// the timeout used to call check_tiles
var g_timeout;

// a flag that signifies if we have updated the map due to being idle (not moving for 100ms)
var g_idle;

// a list of tiles for each zoom level
var g_tiles;

// any target that we were given in the URL
var g_target;

// called with info about the viewport
function init () {
    g_debug_enabled = false;
    fullscreen = false;

    viewp = $("viewport");
    subs = $("substrate");

    // were we anchored to some particular location?
    g_target = document.location.hash.replace("#", "");
   
    // create the draggable
    g_draggable = new Draggable("substrate", {
        starteffect: null, 
        endeffect: null,
        onStart: viewport_scroll_start,
        onDrag: viewport_scroll_move,
        onEnd: viewport_scroll_done
    });

    // double-click listener
    Event.observe(subs, "dblclick", viewport_dblclick);

    // mouse wheel
    Event.observe(subs, "mousewheel", viewport_mousewheel);
    Event.observe(subs, "DOMMouseScroll", viewport_mousewheel);     // mozilla

    // window size changes
    Event.observe(document, "resize", update_viewport_size);

    // should we do debugging?
    if (g_debug_enabled) {
        g_debug = document.createElement("pre");
        g_debug.style.height = "100px";
        g_debug.style.overflow = "auto";
        debug("Debug output...");

        $('wrapper').appendChild(g_debug);
    }
}

/*
 * Initialize this for viewing the given image parameters
 */

var g_opt_key, g_opt_value, g_refresh;
function load (x, y, tw, th, z, z_min, z_max, opt_key, opt_value, refresh) {
    // variable setup
    g_x = x;
    g_y = y;
    g_tw = tw;
    g_th = th;
    g_z = z;
    g_z_min = z_min;
    g_z_max = z_max;
    g_opt_key = opt_key;
    g_opt_value = opt_value;
    g_refresh = refresh;
    
    g_idle = true;

    g_tiles = [];
    
    viewp = $("viewport");
    subs = $("substrate");
    
    // create the zoom-level divs
    for (var zl = z_min; zl <= z_max; zl++) {
        zl_div = document.createElement("div");
        zl_div.id = "zl_" + zl;
        zl_div.style.position = "relative";

        subs.appendChild(zl_div);

        g_tiles[zl] = [];
    }

    if (g_target.indexOf("goto") == 0) {
        asdf = g_target.split("_", 4);
        
        update_zoom_level(
            parseInt(asdf[3]) - g_z
        );
        
        scroll_to(
            parseInt(asdf[1]),
            parseInt(asdf[2])
        );
    } else {
        if (g_target == "fullscreen")
            fullscreen = true;

        // scroll to the initial position
        scroll_to(g_x*g_tw, g_y*g_th);
        
        // adjust the zoom buttons
        update_zoom_level(0);
    }
    
    if (fullscreen)
        viewport_fullscreen();
    else  {
        // load the viewport size and then the tiles
        update_viewport_size();
    }
}

function unload () {
    $("substrate").innerHTML = "";
    g_tiles = [];
}


function debug (str) {
    if (g_debug_enabled)
        g_debug.textContent = (str + "\n") + g_debug.textContent;
}

// viewport-oriented stuff

/*
 * update the screen size stuff based on the actual viewport size
 */
function update_viewport_size () {
    g_w = viewp.getWidth();
    g_h = viewp.getHeight();

    g_w_half = g_w/2;
    g_h_half = g_h/2;

    check_tiles();
}

function viewport_fullscreen () {
    viewp.style.position = "absolute";
    viewp.style.top = "0px";
    viewp.style.left = "0px";
//    viewp.style.bottom = "0px";
//    viewp.style.right = "0px";
    viewp.style.width = "100%";
    viewp.style.height = "100%";
    viewp.style.borderWidth = 0;

    update_viewport_size();
}

// pixel-oriented stuff, related to where the view is scrolled to

/*
 * scroll the view to a given (x, y) pixel offset from the top-left corner
 */
function scroll_to (x, y) {
    subs.style.top = "-" + y + "px";
    subs.style.left = "-" + x + "px";
}

/*
 * Move the view dx pixels to the right, and dy pixels to the bottom in a fancy animated fashion
 */
function move (dx, dy) {
    new Effect.Move(subs, {
        x: -dx,
        y: -dy,
        duration: 0.5,  // pretty quick
        afterFinish: check_tiles
    });
}

/*
 * return the current horizontal scroll offset in pixels from the left edge
 */
function scroll_x () {
    return -parseInt(subs.style.left);
}

/*
 * return the current vertical scroll offset in pixels from the top edge
 */
function scroll_y () {
    return -parseInt(subs.style.top);
}

/*
 * scale co-ordinates by a zoom factor, if we zoom in (dz < 0), n will become larger, and if we zoom out (dz > 0), n will become smaller
 */
function scaleByZoomDelta (n, dz) {
    if (dz > 0)
        return n >> dz;
    else
        return n << -dz;
}

/*
 * From the given offset, calcuate the new_offset that would be needed for the
 * pixel at (offset+half) to be at (new_offset+half) after the given zoom delta
 * has been applied
 */
function align_center(offset, half, delta) {
    return scaleByZoomDelta(offset + half, delta) - half;
}

/*
 * change the zoom level. A positive value zooms out, a negative vlaue zooms in.
 */
function zoom (delta) {
    return zoom_center_to(
        scroll_x() + g_w_half,
        scroll_y() + g_h_half, 
        delta
    );
}

/*
 * Zoom in/out such that the given co-ord (in current co-ord values) will be in the center of the screen
 */
function zoom_center_to (x, y, delta) {
    return zoom_to(
        scaleByZoomDelta(x, delta) - g_w_half,
        scaleByZoomDelta(y, delta) - g_h_half,
        delta
     );
}

/*
 * Zoom in/out such that the given co-ord (in target co-ord values) will be in the top-left corner
 */
function zoom_to (x, y, delta) {
    if (!update_zoom_level(delta))
        return false;

    // scroll to a new position such that the center co-ordinate is correct
    scroll_to(x, y);
    
    // update view
    update_after_timeout();

    return true;
}

/*
 * Return the (x, y) co-ord of the event inside the viewport
 */
function event_offset (e) {
    var offset = viewp.cumulativeOffset();

    return {
        x: e.pointerX() - offset.left, 
        y: e.pointerY() - offset.top
    };
}

/*
 * Double-click handler
 */
function viewport_dblclick (e) {
    var offset = event_offset(e);
    
    if (!zoom_center_to(
        scroll_x() + offset.x,
        scroll_y() + offset.y,
        -1
    )) {
        // if we're already zoomed in, move o/
        move(offset.x - g_w_half, offset.y - g_h_half);
    }

}

// zoom control stuff

/*
 * Mouse wheel handler
 */
function viewport_mousewheel (e) {
    // this works in very weird ways, so it's based on code from http://adomas.org/javascript-mouse-wheel/ (stupid person didn't include any license)
    var delta;

    if (e.wheelData) {  // IE + Opera
        delta = e.wheelData;
        if (window.opera)   // Opera
            delta = -delta;
    } else if (e.detail) {  // Mozilla
        delta = -e.detail;
    }

    if (e.preventDefault)
        e.preventDefault();
    
    // delta > 0 : scroll up, zoom in
    // delta < 0 : scroll down, zoom out
    delta = delta < 0 ? 1 : -1;

    // Firefox's DOMMouseEvent's pageX/Y attributes are broken. layerN is for mozilla, offsetN for IE, seems to work
    var x = parseInt(e.target.style.left) + (e.layerX ? e.layerX : e.offsetX);
    var y = parseInt(e.target.style.top) + (e.layerY ? e.layerY : e.offsetY);
    var dx = x - scroll_x();
    var dy = y - scroll_y();

    zoom_to(
        scaleByZoomDelta(x, delta) - dx, 
        scaleByZoomDelta(y, delta) - dy, 
        delta
    );

//  if ( )    
//        debug("scrollzoom from x=" + x + " y=" + y);
}

/*
 * Updates the zoom level with the given delta. Returns true/false if it's valid or not
 * Disable/enable the zoom in/out buttons to reflect the current zoom level and the min/max zoom levels
 */
function update_zoom_level (delta) {
    var oz = g_z;
    var z = g_z + delta;
    
    // is the new zoom level valid?
    if (z < g_z_min || z > g_z_max)
        return false;
    
    g_z = z;
    
    // update the zoom buttons
    if (z == g_z_min)
        $("zoom_in").disable();
    else
        $("zoom_in").enable();

    if (z == g_z_max)
        $("zoom_out").disable();
    else
        $("zoom_out").enable();
    
    // now update the zoomlevel div's z-indexes
    zoom_showhide_fillers(true);
    var zi = 10;
    var i;
    
    // preferr the zoomed-in levels over the zoomed-out levels
    for (i = g_z_min; i < z; i++)
        $("zl_" + i).style.zIndex = zi++;
    
    // haet the zoomed-out levels
    for (i = g_z_max; i > z; i--)
        $("zl_" + i).style.zIndex = zi++;
    
    // and these are obviously the best
    $("zl_" + z).style.zIndex = zi;
    
    // now update the image sizes/positions
    var dz, w, h, tiles, tiles_len, t, ts;
    for (zi = g_z_min; zi <= g_z_max; zi++) {
        dz = z - zi;

        w = scaleByZoomDelta(g_tw, dz);
        h = scaleByZoomDelta(g_th, dz);

        tiles = g_tiles[zi];
        tiles_len = tiles.length;

        for (i = 0; i < tiles_len; i++) {
            t = tiles[i];
            ts = t.style;

            ts.width = w;
            ts.height = h;
            ts.top = h*t.__row;
            ts.left = w*t.__col;
        }
    }
    
    return true;
}

/*
 * Hide the filler layers, i.e. the ones that aren't the current zoom level
 */
function zoom_showhide_fillers (show) {
    for (var zi = g_z_min; zi <= g_z_max; zi++)
        if (zi != g_z)
            if (show)
                $("zl_" + zi).show();
            else 
                $("zl_" + zi).hide();
}

// tile-oriented stuff

/*
 * Return the URL to the given tile, taking the current zoom level into account
 */
function build_url (col, row) {
    var x = col*(g_tw << g_z);
    var y = row*(g_th << g_z);

    var u = "/tile?x=" + x + "&y=" + y + "&w=" + g_tw + "&h=" + g_th + "&z=" + g_z;

    if (g_refresh)
        u += "&ts=" + new Date().getTime();

    if (g_opt_key && g_opt_value)
        u += "&" + g_opt_key + "=" + g_opt_value;

    return u;
}

/*
 * Loads the given tile, assuming that it hasn't been loaded yet
 */
function load_tile (id, col, row) {
    if (col < 0 || row < 0)
        return;

    e = document.createElement("img");
    e.src = build_url(col, row);
    e.id = id;
    e.title = "(" + col + ", " + row + ")"
    e.style.top = g_th * row;
    e.style.left = g_tw * col;
    e.style.display = "none";
    Event.observe(e, "load", _tile_loaded);
    e.__col = col;
    e.__row = row;

    $("zl_" + g_z).appendChild(e);
    g_tiles[g_z].push(e);
}

function _tile_loaded (e) {
    this.style.display = "block";

}

/*
 * Updates the tile to the current time/zoom level
 */
function touch_tile (tile, col, row) {
    if (g_refresh)
        tile.src = build_url(col, row);
}

/*
 * Compute which tiles are currently visible, and load/touch all of them.
 *
 * If we are standing still, will schedule another call in two seconds
 */
function check_tiles () {
    var x = scroll_x();
    var y = scroll_y();
    var w = g_w;
    var h = g_h;
    
    var start_col = Math.floor(x/g_tw);
    var start_row = Math.floor(y/g_th);
    var end_col = Math.floor((x + w)/g_tw);
    var end_row = Math.floor((y + h)/g_th);

//    debug("Visible area: (" + x + ", " + y + ") -> (" + (x+w) + ", " + (y+h) + "), visible tiles: (" + start_col + ", " + start_row + ") -> (" + end_col + ", " + end_row + ")");

    var id, t;

    for (col = start_col; col <= end_col; col++) {
        for (row = start_row; row <= end_row; row++) {
            id = "tile_" + g_z + "_" + col + "_" + row;
            t = $(id);

            if (t)
                touch_tile(t, col, row);
            else
                load_tile(id, col, row);
        }
    }

    // update the link-to-this-page thing
    $("page_link").href = "#goto_" + x + "_" + y + "_" + g_z;
}

// delayed updates

/*
 * Call check_tiles in 100ms, unless we are called again
 */
function update_after_timeout () {
    g_idle = false;

    if (g_timeout)
        clearTimeout(g_timeout);

    g_timeout = setTimeout(_update_timeout, 100);  
}

function update_timeout_cancel () {
    if (g_timeout) {
        debug("Cancel timeout");
        clearTimeout(g_timeout);
    }
}

function _update_timeout () {
    g_idle = true;

    check_tiles();
}
/*
 * call check_tiles if it hasn't been called due to update_after_timeout
 */
function update_now () {
    if (g_timeout)
        clearTimeout(g_timeout);
    
    if (!g_idle)
        check_tiles();
}

// scrolling

/*
 * called on scroll start
 */
var g_scroll_x, g_scroll_y;
function viewport_scroll_start () {
    g_scroll_x = scroll_x();
    g_scroll_y = scroll_y();
}

function viewport_scroll_move () {
    update_after_timeout();

    // may still want some kind of code like this later
    // possibly: update once we scroll over 100px, regardless of if we're still or not
/*    
    var x = scroll_x();
    var y = scroll_y();

    var dx = Math.abs(g_scroll_x - x);
    var dy = Math.abs(g_scroll_y - y)

    if (dx > 100 || dy > 100) {
        debug("scrolled dx=" + dx + " dy=" + dy + " pixels, update in 100ms");

        update_after_timeout();
    }
*/
}

function viewport_scroll_done() {
    update_now();
}


// vehicles stuff

var g_vehicles = new Array();
function vehicle_list () {
    new Ajax.Request("/vehicles", {
        method: 'get',
        onSuccess: function (transport, vehicles) {
            vehicles.each(function(v){
                if (g_vehicles[v.id]) {
                    g_vehicles[v.id] = v;
                    $("veh_" + v.id + "_sprite").src = "/sprite?v=" + v.id;

                } else {
                    var row = document.createElement("tr");
                        row.id = "veh_" + v.id;

                    var left = document.createElement("td");
                        left.innerHTML = v.id;

                        row.appendChild(left);
                    
                    var img_cell = document.createElement("td");
                    var img = document.createElement("img");
                    var descr = document.createElement("span");
                        img.id = "veh_" + v.id + "_sprite";
                        img.src = "/sprite?v=" + v.id;

                        descr.innerHTML = "PROFIT THIS YEAR: &pound;" + v.profit_this_year + " (LAST YEAR: &pound;" + v.profit_last_year + ")"

                        img_cell.appendChild(img);
                        img_cell.appendChild(document.createElement("br"));
                        img_cell.appendChild(descr);

                        row.appendChild(img_cell);
                        
                    Event.observe(row, "click", function (e) {
                        vehicle_scroll_to(v.id);
                        e.stop();
                        return false;
                    });


                    g_vehicles[v.id] = v;

                    $('vehicles_list').appendChild(row);
            }});
        }
    }); 

    setTimeout(vehicle_list, 3000);
}

/*
 * scroll to a vehicle
 */
function vehicle_scroll_to (veh_id) {
    var veh = g_vehicles[veh_id];

    scroll_to(
        veh.x - g_w_half,
        veh.y - g_h_half
    );

    check_tiles();
}

// images stuff
var g_imgs;

function load_image_list () {
     new Ajax.Request("/images", {
        method: 'get',
        onSuccess: function (transport, images) {
            g_tw = images[0];
            g_th = images[1];

            var list = document.createElement("select");
            list.id = "images_list";

            images[2].each(function(img){
                var filename = img[0];
                var zoom_max = img[1];

                var item = document.createElement("option");

                item.value = filename + "/" + zoom_max;
                item.innerHTML = filename;

                list.appendChild(item);
            });

            var btn = document.createElement("input");
            btn.type = "button";
            btn.value = "View";
            Event.observe(btn, "click", change_image);

            var zoom = $('zoom');
            
            zoom.appendChild(document.createElement("br"));
            zoom.appendChild(list);
            zoom.appendChild(btn);
            
            change_image();
        }
    });
}

function change_image () {
    var data = $F("images_list").split("/");
    
    var filename = data[0];
    var zoom_max = parseInt(data[1]);

    // load (x, y, tw, th, z, z_min, z_max, opt_key, opt_value)
    unload();
    load(0, 0, g_tw, g_th, zoom_max, 0, zoom_max, "f", filename, false);
}

