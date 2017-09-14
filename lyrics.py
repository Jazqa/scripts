#!/usr/bin/env python3
"""Prints the lyrics of the current Spotify song"""


import curses
import dbus
import requests
from bs4 import BeautifulSoup as bs


def get_metadata():
    """Returns the Spotify metadata"""
    session_bus = dbus.SessionBus()
    spotify_bus = session_bus.get_object("org.mpris.MediaPlayer2.spotify",
                                         "/org/mpris/MediaPlayer2")
    spotify_properties = dbus.Interface(spotify_bus, "org.freedesktop.DBus.Properties")
    return spotify_properties.Get("org.mpris.MediaPlayer2.Player", "Metadata")


def process_metadata(metadata):
    """Processes the metadata and returns artist and track names"""
    artist = metadata["xesam:artist"][0]
    track = metadata["xesam:title"]

    # Gets rid of the unnecessary tags
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
    """Prints and structures the lyrics"""
    stdscr.clear()
    stdscr.refresh()
    curses.curs_set(0)
    max_y, max_x = stdscr.getmaxyx()

    artist, track = process_metadata(get_metadata())
    lyrics = get_lyrics(artist, track)

    # Adds a sexy title to the lyrics
    title = ["║ " + artist + " - " + track + " ║"]
    title = title + ["╚" + "═" * (len(title[0]) - 2) + "╝"]
    title = ["╔" + "═" * (len(title[0]) - 2) + "╗"] + title
    title = title + [" "]

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
        pad_key = pad.getch()

        if pad_key == curses.KEY_RESIZE:
            stdscr.clear()
            stdscr.refresh()
            max_y, max_x = stdscr.getmaxyx()
            center_x = round(max_x / 2 - longest / 2)
            pad.refresh(pad_y, pad_x, 0, center_x, max_y - 1, max_x - 1)

        if pad_key == curses.KEY_DOWN:
            if pad_y + 1 + max_y > len(lyrics + title):
                pad_y = pad_y
            else:
                pad_y += 1
            pad.refresh(pad_y, pad_x, 0, center_x, max_y - 1, max_x - 1)

        if pad_key == curses.KEY_UP:
            pad_y -= 1
            if pad_y < 0:
                pad_y = 0
            pad.refresh(pad_y, pad_x, 0, center_x, max_y - 1, max_x - 1)

        if pad_key == curses.KEY_RIGHT:
            if pad_x + 1 + max_x > len(max(lyrics, key=len)):
                pad_x = pad_x
            else:
                pad_x += 1
            pad.refresh(pad_y, pad_x, 0, center_x, max_y - 1, max_x - 1)

        if pad_key == curses.KEY_LEFT:
            pad_x -= 1
            if pad_x < 0:
                pad_x = 0
            pad.refresh(pad_y, pad_x, 0, center_x, max_y - 1, max_x - 1)

        # F5 restarts the script (f.ex. if the song chages)
        if pad_key == curses.KEY_F5:
            main(stdscr)



if __name__ == "__main__":
    curses.wrapper(main)
