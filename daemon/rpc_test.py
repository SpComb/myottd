import subprocess

import rpc2
import buffer

openttd = None
player_joined = False

def main () :
    global openttd, player_joined

    openttd = subprocess.Popen(
        args=['/home/terom/my_ottd/openttd/trunk/bin/openttd', '-A', '-D', '0.0.0.0:8118'],
        bufsize=0,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,

    )

    print "OpenTTD running..."
    
    buf = ''

    while True :
#        print "Reading with %d bytes in the buffer..." % len(buf)

        read = openttd.stdout.read(1)

        buf += read

#        print "Read %d bytes for a total of %d bytes" % (len(read), len(buf))
        
        i = buffer.Buffer(buf)
        
        i.processWith(readCommand)

        buf = i.read()

        if player_joined :
            writeCommand("CMD_OUT_PLAYERS")
            player_joined = False

IN_COMMANDS = [x.strip() for x in """
    CMD_IN_NULL,
    CMD_IN_CONSOLE,
    CMD_IN_WARNING,
    CMD_IN_ERROR,
    CMD_IN_DEBUG,
    CMD_IN_NETWORK_EVENT,
    CMD_IN_PLAYERS_REPLY,
    CMD_IN_SCREENSHOT_REPLY,
    CMD_IN_ERROR_REPLY
""".strip().split(',\n')]

OUT_COMMANDS = [x.strip() for x in """
    CMD_OUT_NULL,
    CMD_OUT_CONSOLE_EXEC,
    CMD_OUT_PLAYERS,
    CMD_OUT_SCREENSHOT
""".strip().split(',\n')]

NETWORK_EVENTS = [x.strip() for x in """
	NETWORK_ACTION_JOIN,
	NETWORK_ACTION_LEAVE,
	NETWORK_ACTION_SERVER_MESSAGE,
	NETWORK_ACTION_CHAT,
	NETWORK_ACTION_CHAT_COMPANY,
	NETWORK_ACTION_CHAT_CLIENT,
	NETWORK_ACTION_GIVE_MONEY,
	NETWORK_ACTION_NAME_CHANGE
""".strip().split(',\n')]    

def readCommand (i) :
    global player_joined

    cmd = i.readEnum(IN_COMMANDS)

    args = rpc2._read_list(i)

    if cmd == "CMD_IN_NETWORK_EVENT" :
        args[0] = NETWORK_EVENTS[args[0]]

        if args[0] == "NETWORK_ACTION_JOIN" :
            player_joined = True

    print "Read %s:" % cmd

    for arg in args :
        print "\t%20s : %s" % (type(arg), arg)

    print

def writeCommand (command, *args) :
    print "Write %s:" % command

    for arg in args :
        print "\t%20s : %s" % (type(arg), arg)

    print

    buf = buffer.Buffer()

    buf.writeEnum(OUT_COMMANDS, command)

    rpc2._write_list(buf, args)

    openttd.stdin.write(buf.getvalue())

if __name__ == '__main__' :
    main()

