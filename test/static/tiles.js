// our initial (col, row) position
var g_x, g_y;

// how many tiles (wide, high) the viewport is
var g_w, g_h;

// how (wide, high) a tile is
var g_tw, g_th;

// half of viewport width/height
var g_w_half, g_h_half;

// the Draggable substrate, we get our current offset from this
var g_draggable;

// a two-dimensional array of what tiles we have loaded, indexed by absolute [col][row]
var g_loaded;

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

// called with info about the viewport
function init (x, y, w, h, tw, th, z, z_min, z_max) {
    // variable setup
    g_x = x;
    g_y = y;
    g_w = w;
    g_h = h;
    g_tw = tw;
    g_th = th;
    g_z = z;
    g_z_min = z_min;
    g_z_max = z_max;
    g_w_half = (g_w*g_tw)/2;
    g_h_half = (g_h*g_th)/2;
    
    g_loaded = [];
    g_idle = true;

    g_debug_enabled = true;

    viewp = $("viewport");
    subs = $("substrate");
    

    // were we anchored to some particular location?
    if (document.baseURI.indexOf("#") >= 0) {
        target = document.baseURI.split("#", 2);
        asdf = target[1].split("_", 3);
        
        scroll_to(
            parseInt(asdf[0]),
            parseInt(asdf[1])
        );

        update_zoom_level(
            parseInt(asdf[2])
        );

    } else {
        // scroll to the initial position
        scroll_to(g_x*g_tw, g_y*g_th);
        
        // adjust the zoom buttons
        update_zoom_level(0);
    }
    
    // create the draggable
    g_draggable = new Draggable("substrate", {
        starteffect: null, 
        endeffect: null,
        onDrag: update_after_timeout,
        onEnd: update_now
    });

    // double-click listener
    Event.observe(subs, "dblclick", viewport_dblclick);

    // mouse wheel
    Event.observe(subs, "mousewheel", viewport_mousewheel);
    Event.observe(subs, "DOMMouseScroll", viewport_mousewheel);     // mozilla

    // should we do debugging?
    if (g_debug_enabled) {
        g_debug = document.createElement("pre");
        g_debug.style.height = "100px";
        g_debug.style.overflow = "auto";
        debug("Debug output...");

        $('wrapper').appendChild(g_debug);
    }
    
    // load the tiles and set off the update timer    
    check_tiles();
    
    // the list of vehicles
    vehicle_list();
}

function debug (str) {
    if (g_debug_enabled)
        g_debug.textContent = (str + "\n") + g_debug.textContent;
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
    return zoom_to(scroll_x() + g_w_half, scroll_y() + g_h_half, delta);
}

/*
 * Zoom in/out such that the given co-ord (in current co-ord values) will be in the center of the screen
 */
function zoom_to (x, y, delta) {
    if (!update_zoom_level(delta))
        return false;

    // scroll to a new position such that the center co-ordinate is correct
    scroll_to(
        scaleByZoomDelta(x, delta) - g_w_half,
        scaleByZoomDelta(y, delta) - g_h_half
    );
    
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
    
    move(offset.x - g_w_half, offset.y - g_h_half);
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

    // Firefox's DOMMouseEvent's pageX/Y attributes are broken
    var x = parseInt(e.target.style.left) + e.layerX;
    var y = parseInt(e.target.style.top) + e.layerY;

    if (zoom_to(x, y, delta))
        debug("scrollzoom from x=" + x + " y=" + y);
}

/*
 * Updates the zoom level with the given delta. Returns true/false if it's valid or not
 * Disable/enable the zoom in/out buttons to reflect the current zoom level and the min/max zoom levels
 */
function update_zoom_level (delta) {
    var z = g_z + delta;

    if (z < g_z_min || z > g_z_max)
        return false;
    
    g_z = z;

    if (z == g_z_min)
        $("zoom_in").disable();
    else
        $("zoom_in").enable();

    if (z == g_z_max)
        $("zoom_out").disable();
    else
        $("zoom_out").enable();

    return true;
}

// tile-oriented stuff

/*
 * Has the given tile been loaded yet?
 */
function is_loaded (col, row) {
    return (g_loaded[col] && g_loaded[col][row]);
}

/*
 * Mark the given tile as haveing been loaded
 */
function mark_tile (col, row) {
    if (!g_loaded[col])
        g_loaded[col] = [];

    g_loaded[col][row] = true;
}

/*
 * Return the URL to the given tile, taking the current zoom level into account
 */
function build_url (col, row) {
    var x = col*(g_tw << g_z);
    var y = row*(g_th << g_z);

    return "/tile?x=" + x + "&y=" + y + "&w=" + g_tw + "&h=" + g_th + "&z=" + g_z + "&ts=" + new Date().getTime();
}

/*
 * Loads the given tile, assuming that it hasn't been loaded yet
 */
function load_tile (col, row) {
    if (col < 0 || row < 0)
        return;

    e = document.createElement("img");
    e.src = build_url(col, row);
    e.id = "tile_" + col + "_" + row;
    e.title = "(" + col + ", " + row + ")"
    e.style.top = g_th * row;
    e.style.left = g_tw * col;

    subs.appendChild(e);

    mark_tile(col, row);
}

/*
 * Updates the tile to the current time/zoom level
 */
function touch_tile (col, row) {
    $("tile_" + col + "_" + row).src = build_url(col, row);
}

/*
 * Compute which tiles are currently visible, and load/touch all of them.
 *
 * If we are standing still, will schedule another call in two seconds
 */
function check_tiles () {
    var x = scroll_x();
    var y = scroll_y();
    var w = g_w*g_tw;
    var h = g_h*g_th;
    
    var start_col = Math.floor(x/g_tw);
    var start_row = Math.floor(y/g_th);
    var end_col = Math.floor((x + w)/g_tw);
    var end_row = Math.floor((y + h)/g_th);

//    debug("Visible area: (" + x + ", " + y + ") -> (" + (x+w) + ", " + (y+h) + "), visible tiles: (" + start_col + ", " + start_row + ") -> (" + end_col + ", " + end_row + ")");

    for (col = start_col; col <= end_col; col++) {
        for (row = start_row; row <= end_row; row++) {
            if (!is_loaded(col, row))
                load_tile(col, row);
            else
                touch_tile(col, row);
        }
    }

    // update the link-to-this-page thing
    $("page_link").href = "#" + x + "_" + y + "_" + g_z;
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
