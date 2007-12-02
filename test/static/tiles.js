var g_x, g_y, g_w, g_h, g_tw, g_th, g_draggable, g_loaded, g_debug, g_debug_enabled, g_z;

var viewp, subs;

function init (x, y, w, h, tw, th, z) {
    g_x = x;
    g_y = y;
    g_w = w;
    g_h = h;
    g_tw = tw;
    g_th = th;
    g_z = z;

    if (document.baseURI.indexOf("#") >= 0) {
        target = document.baseURI.split("#", 2);
        asdf = target[1].split("_", 2);

        g_x += parseInt(asdf[0]);
        g_y += parseInt(asdf[1]);

    }

    viewp = $("viewport");
    subs = $("substrate");
    
    g_draggable = new Draggable("substrate", {
        starteffect: function () {}, 
        endeffect: function() {},
        onDrag: viewport_drag_motion,
        onEnd: viewport_drag_end
    });

    g_loaded = [];
    g_idle = true;

    check_tiles();

    g_debug_enabled = false;
    
    if (g_debug_enabled) {
        g_debug = document.createElement("pre");
        g_debug.style.height = "100px";
        g_debug.style.overflow = "auto";
        debug("Debug output...");

        $('wrapper').appendChild(g_debug);
    }

    vehicles_list();
}

function debug (str) {
    if (g_debug_enabled)
        g_debug.textContent = (str + "\n") + g_debug.textContent;
}

function is_loaded (col, row) {
    return (g_loaded[col] && g_loaded[col][row]);
}

function mark_tile (col, row) {
    if (!g_loaded[col])
        g_loaded[col] = [];

    g_loaded[col][row] = true;
}

function zoom (delta) {
    g_z += delta;
}

function build_url (col, row) {
    return "/tile?x=" + ((g_x + col)*g_tw) + "&y=" + ((g_y + row)*g_th) + "&w=" + g_tw + "&h=" + g_th + "&z=" + g_z + "&ts=" + new Date().getTime();
}

function load_tile (col, row) {
    e = document.createElement("img");
    e.src = build_url(col, row);
    e.id = "tile_" + col + "_" + row;
    e.title = "(" + col + ", " + row + ")"
    e.style.top = g_th * row;
    e.style.left = g_tw * col;

    subs.appendChild(e);

    mark_tile(col, row);
}


function touch_tile (col, row) {
    $("tile_" + col + "_" + row).src = build_url(col, row);
}

function check_tiles () {
    var delta = g_draggable.currentDelta()
    var x = -delta[0];
    var y = -delta[1];
    var w = g_w*g_tw;
    var h = g_h*g_th;
    
    var start_col = Math.floor(x/g_tw);
    var start_row = Math.floor(y/g_th);
    var end_col = Math.floor((x + w)/g_tw);
    var end_row = Math.floor((y + h)/g_th);

    debug("Visible area: (" + x + ", " + y + ") -> (" + (x+w) + ", " + (y+h) + "), visible tiles: (" + start_col + ", " + start_row + ") -> (" + end_col + ", " + end_row + ")");

    for (col = start_col; col <= end_col; col++) {
        for (row = start_row; row <= end_row; row++) {
            if (!is_loaded(col, row))
                load_tile(col, row);
            else
                touch_tile(col, row);
        }
    }

    // don't set the timeout now, it's set in tile_loaded
    if (g_idle)
        g_timeout = setTimeout(check_tiles, 2000);
}

var g_timeout, g_idle;
function viewport_drag_motion (d) {
    g_idle = false;

    if (g_timeout)
        clearTimeout(g_timeout);

    g_timeout = setTimeout(check_tiles, 100);
}

function viewport_drag_end (d) {
    g_idle = true;

    if (g_timeout)
        clearTimeout(g_timeout);

    check_tiles();
}

var g_vehicle_images = [];
function vehicles_list () {
    $('vehicles_list').innerHTML = "";
    
    new Ajax.Request("/vehicles", {
        method: 'get',
        onSuccess: function (transport, vehicles) {
            vehicles.each(function(v){
                var id = v[0];
                var type = v[1];

                var row = document.createElement("tr");

                var header = document.createElement("th");
                var link = document.createElement("a");
                link.href = "/tile?v=" + id + "&w=300&h=150&z=" + g_z;
                link.innerHTML = id;
                header.appendChild(link);
                row.appendChild(header);
                
                var type_cell = document.createElement("td");
                type_cell.innerHTML = type;
                row.appendChild(type_cell);

                var img_cell = document.createElement("td");
                var img = document.createElement("img");
                img_cell.appendChild(img);
                row.appendChild(img_cell);

                g_vehicle_images[id] = img;

                $('vehicles_list').appendChild(row);
            });
        }
    }); 

    update_vehicle_list();
}

function update_vehicle_list () {
    for (var id = 0; id < g_vehicle_images.length; id++) {
        if (g_vehicle_images[id])
            g_vehicle_images[id].src = "/tile?v=" + id + "&w=300&h=150&z=" + g_z + "&ts=" + new Date().getTime();
    }

    setTimeout(update_vehicle_list, 2500);
}

