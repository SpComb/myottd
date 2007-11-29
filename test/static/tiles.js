var g_x, g_y, g_w, g_h, g_tw, g_th, g_draggable, g_loaded, g_debug, g_debug_enabled;

var viewp, subs;

function init (x, y, w, h, tw, th) {
    g_x = x;
    g_y = y;
    g_w = w;
    g_h = h;
    g_tw = tw;
    g_th = th;

    viewp = $("viewport");
    subs = $("substrate");
    
    g_draggable = new Draggable("substrate", {
        starteffect: function () {}, 
        endeffect: function() {},
        onDrag: viewport_drag_motion,
        onEnd: viewport_drag_end
    });

    g_loaded = [];

    for (col = 0; col < g_w; col++) {
        for (row = 0; row < g_h; row++) {
            load_tile(col, row);
        }
    }
    
    g_debug_enabled = false;
    
    if (g_debug_enabled) {
        g_debug = document.createElement("pre");
        g_debug.style.height = "100px";
        g_debug.style.overflow = "auto";
        debug("Debug output...");

        $('wrapper').appendChild(g_debug);
    }
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

function load_tile (col, row) {
    e = document.createElement("img");
    e.src = "/tile_img?x=" + (g_x + col) + "&y=" + (g_y + row);
    e.title = "(" + col + ", " + row + ")"
    e.style.top = g_th * row;
    e.style.left = g_tw * col;

    subs.appendChild(e);

    mark_tile(col, row);
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
        }
    }
}

var g_drag_timeout;
function viewport_drag_motion (d) {
    if (g_drag_timeout)
        clearTimeout(g_drag_timeout);

    g_drag_timeout = setTimeout(check_tiles, 100);
}

function viewport_drag_end (d) {
    if (g_drag_timeout)
        clearTimeout(g_drag_timeout);

    check_tiles();
}

