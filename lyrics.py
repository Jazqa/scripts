#!/usr/bin/env python3
"""Prints the lyrics of the current Spotify song"""


import curses
import requests
from sys import platform as pf
from bs4 import BeautifulSoup as bs

# Different operating systems store Spotify data differently
if pf == "linux" or pf == "linux2":
    import dbus
elif pf == "darwin":
    from subprocess import Popen, PIPE
# elif pf == "win32" or "win64"

def get_info():
    """Returns the currently playing artist and track"""
    if pf == "linux" or pf == "linux2":
        # On Linux, data is available via dbus
        spotify = dbus.Interface(dbus.SessionBus().get_object("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2"),
                                 "org.freedesktop.DBus.Properties").Get("org.mpris.MediaPlayer2.Player", "Metadata")
        artist = spotify["xesam:artist"][0]
        track = spotify["xesam:title"]

    elif pf == "darwin":
        # On MacOS, data has to be fetched with applescript
        get_artist = """
        on run {}
            tell application "Spotify"
                return artist of current track as string
            end tell
        end run
        """

        get_track = """
        on run {}
            tell application "Spotify"
                return name of current track as string
            end tell
        end run
        """

        p = Popen(['/usr/bin/osascript', '-'], stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        stdout, stderr = p.communicate(get_artist)
        artist = stdout.strip()

        p = Popen(['/usr/bin/osascript', '-'], stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        stdout, stderr = p.communicate(get_track)
        track = stdout.strip()

    # elif pf == "win32" or "win64":

    return artist, track


def process_info(artist, track):
    """
    Processes the track information, removing unnecessary substrings,
    such as "Remaster", "Mono Version" and so forth.
    F.ex. process_info("Black Sabbath", "Into The Void - 2004 Remaster")
    returns "Black Sabbath", "Into The Void
    """
    if track.find(" - ") != -1:
        track = track[:track.index(" - ")]
    if track.find("(Mono") != -1:
        track = track[:track.index("(Mono")]
    if track.find("[Mono") != -1:
        track = track[:track.index("[Mono")]

    return artist, track


def get_lyrics(artist, track):
    """Processes the URL http://lyrics.wikia.com/wiki/artist:track and returns the lyrics"""
    lyrics = bs(requests.get("http://lyrics.wikia.com/wiki/" +
                             artist + ":" + track).content, "lxml")

    # Finds the wanted div from the lyrics
    lyrics = str(lyrics.find("div", {"class": "lyricbox"}))

    # Wikia lyrics contain html leftovers [:22] & [-38:]
    lyrics = lyrics[22:-38]

    # Transfers each line to an array entry
    lyrics = lyrics.split("<br/>")

    # Replaces the lyrics italics tags
    lyrics = [line.replace("<i>", "") for line in lyrics]
    lyrics = [line.replace("</i>", "") for line in lyrics]

    return lyrics


def main(stdscr):
    """Initializes the curses interface and prints the lyrics"""
    stdscr.clear()
    stdscr.refresh()
    curses.curs_set(0)
    max_y, max_x = stdscr.getmaxyx()

    artist, track = get_info()
    artist, track = process_info(artist, track)
    lyrics = get_lyrics(artist, track)

    # Adds a title to the lyrics
    title = [artist + " - " + track]
    title = [" "] + title + [" "] + [" "]

    longest = len(max(lyrics + title, key=len))

    pad_h = len(lyrics) + len(title) + 1
    pad_w = longest

    # Creates a pad according to the size of the lyrics
    pad = curses.newpad(pad_h, pad_w)
    pad.keypad(1)

    pad_y = 0
    pad_x = 0
    center_x = round(max_x / 2 - longest / 2)

    i = 0
    for line in title:
        pad.addstr(i, round((longest - len(line)) / 2), line)
        i += 1

    for line in lyrics:
        pad.addstr(i, round((longest - len(line)) / 2), line)
        i += 1

    pad.refresh(pad_y, pad_x, 0, center_x, max_y - 1, max_x - 1)

    while True:
        # Compares the currently playing track to the displayed track
        # If a different track is playing, updates the lyrics
        pad.timeout(999)
        if track != process_info(get_info()[0], get_info()[1])[1]:
            main(stdscr)

        pad_key = pad.getch()

        if pad_key == curses.KEY_RESIZE:
            stdscr.clear()
            stdscr.refresh()
            max_y, max_x = stdscr.getmaxyx()
            center_x = round(max_x / 2 - longest / 2)
            pad.refresh(pad_y, pad_x, 0, center_x, max_y - 1, max_x - 1)

        # Movement keys
        elif pad_key == curses.KEY_DOWN:
            if pad_y + 1 + max_y > len(lyrics + title):
                pad_y = pad_y
            else:
                pad_y += 1
            pad.refresh(pad_y, pad_x, 0, center_x, max_y - 1, max_x - 1)

        elif pad_key == curses.KEY_UP:
            pad_y -= 1
            if pad_y < 0:
                pad_y = 0
            pad.refresh(pad_y, pad_x, 0, center_x, max_y - 1, max_x - 1)

        elif pad_key == curses.KEY_RIGHT:
            if pad_x + 1 + max_x > len(max(lyrics, key=len)):
                pad_x = pad_x
            else:
                pad_x += 1
            pad.refresh(pad_y, pad_x, 0, center_x, max_y - 1, max_x - 1)

        elif pad_key == curses.KEY_LEFT:
            pad_x -= 1
            if pad_x < 0:
                pad_x = 0
            pad.refresh(pad_y, pad_x, 0, center_x, max_y - 1, max_x - 1)

        # F5 restarts the script
        elif pad_key == curses.KEY_F5:
            main(stdscr)



if __name__ == "__main__":
    curses.wrapper(main)
