import curses
import sys
import time
import redis

lines = 4
columns = 80

class QuitNonError(Exception):
    pass

def pause(window, time_for_pause):
    window.nodelay(True)
    c = window.getch()

    # In non-blocking mode, the getch method returns -1 except when any key is pressed.
    if -1 != c:
        raise QuitNonError()
    else:
        time.sleep(time_for_pause)


def clear_window(window):
    for line in range(lines):
        for column in range(columns):
            if (line == lines-1) and (column == columns - 1):
                window.delch(line, column)
            else:
                window.move(line, column)
                window.addch(line, column, ' ')
            window.refresh()
            pause(window, 0.01)

def main(argv):
    global changed

    r = redis.Redis(host='localhost', port=6379, db=0)

    r = redis.StrictRedis.from_url('redis://localhost:6379/0')
    r.config_set('notify-keyspace-events', 'KEA')

    pubsub = r.pubsub()
    pubsub.psubscribe("*")

    # Initialize the curses object.
    stdscr = curses.initscr()

    # Do not echo keys back to the client.
    curses.noecho()

    # Non-blocking or cbreak mode... do not wait for Enter key to be pressed.
    curses.cbreak()

    # Turn off blinking cursor
    curses.curs_set(True)

    # Enable color if we can...
    if curses.has_colors():
        curses.start_color()

    # Optional - Enable the keypad. This also decodes multi-byte key sequences
    # stdscr.keypad(True)

    caughtExceptions = ""
    try:
        # First things first, make sure we have enough room!
        if curses.COLS <= 88 or curses.LINES <= 11:
            raise Exception("This terminal window is too small.\r\n")

        stdscr.addstr(curses.LINES-1, 0, "Press a key to quit.")
        stdscr.refresh() 

        windowObj = curses.newwin(lines, columns, 0, 0)

        while True:
            found_something = False
            while True:
                message = pubsub.get_message()
                if not message is None:
                    if message['type'] == 'pmessage':
                        channel = message['channel']
                        try1 = channel.decode('utf-8').split(':')[1]
                        try2 = message['data'].decode('utf-8')
                        if try1 == 'expire' or try2 == 'expire':
                            pass
                        else:
                            found_something = True
                else:
                    break

            if found_something:    
                line_count = 0

                clear_window(windowObj)

                keys = r.scan_iter('*')

                sorted_keys = sorted(keys, key=lambda k: r.ttl(k))
                
                for key in sorted_keys:
                    if line_count < 4:
                        current_key = key.decode('utf-8')
                        current_value = r.get(key).decode('utf-8')
                        windowObj.addstr(line_count, 0, "%s %s" % (current_key, current_value), 0)
                        line_count = line_count + 1

                    else:
                        r.expire(key, 60)

                windowObj.refresh()
                windowObj.nodelay(True)
                found_something = False

            pause(windowObj, 1)

    except Exception as err:
        # Just printing from here will not work, as the program is still set to
        # use ncurses.
        # print ("Some error [" + str(err) + "] occurred.")
        if type(err) != QuitNonError:
            caughtExceptions = str(err)

    # End of Program...
    # Turn off cbreak mode...
    curses.nocbreak()

    # Turn echo back on.
    curses.echo()

    # Restore cursor blinking.
    curses.curs_set(True)

    # Turn off the keypad...
    # stdscr.keypad(False)

    # Restore Terminal to original state.
    curses.endwin()

    # Display Errors if any happened:
    if "" != caughtExceptions:
        print("Got error(s) [" + caughtExceptions + "]")


if __name__ == "__main__":
    main(sys.argv[1:])
