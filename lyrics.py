#!/usr/bin/env python3
"""Prints the lyrics of the current Spotify song"""


import os
import requests
from sys import platform as pf
from bs4 import BeautifulSoup as bs


# Different operating systems store Spotify data differently
if pf == "linux" or pf == "linux2":
    import dbus
elif pf == "darwin":
    from subprocess import Popen, PIPE
elif pf == "win32" or "win64":
    import pywintypes
    import win32gui


def get_info_linux():
    # On Linux, data is available via dbus
    spotify = dbus.Interface(dbus.SessionBus().get_object("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2"),
                                "org.freedesktop.DBus.Properties").Get("org.mpris.MediaPlayer2.Player", "Metadata")
    artist = spotify["xesam:artist"][0]
    track = spotify["xesam:title"]
    return artist, track


def get_info_mac():
    # On MacOS, data has to be fetched with applescript
    spotify = """
    on run {}
        tell application "Spotify"
            set a to artist of current track as string
            set t to name of current track as string
            return a & " - " & t
        end tell
    end run
    """
    p = Popen(['/usr/bin/osascript', '-'], stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    stdout, stderr = p.communicate(spotify)
    artist, track = stdout.strip().split( " - ")
    return artist, track


def get_info_windows():
    windows = []
        
    # Older Spotify versions - simply FindWindow for "SpotifyMainWindow"
    windows.append(win32gui.GetWindowText(win32gui.FindWindow("SpotifyMainWindow", None)))

    # Newer Spotify versions - create an EnumHandler for EnumWindows and flood the list with Chrome_WidgetWin_0s
    def find_spotify_uwp(hwnd, windows):
        text = win32gui.GetWindowText(hwnd)
        if win32gui.GetClassName(hwnd) == "Chrome_WidgetWin_0" and len(text) > 0:
            windows.append(text)
    
    win32gui.EnumWindows(find_spotify_uwp, windows)

    while windows.count != 0:
        try:
            text = windows.pop()
            artist, track = text.split(" - ",1)
            return artist, track
        except:
            pass


def get_info():
    """Returns the currently playing artist and track"""
    if pf == "linux" or pf == "linux2":
        return get_info_linux()
    elif pf == "darwin":
        return get_info_mac()
    elif pf == "win32" or "win64":
        return get_info_windows()


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
    lyrics = bs(requests.get("http://lyrics.wikia.com/wiki/" + artist + ":" + track).content, "lxml")

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


def main():
    """Prints the lyrics"""
    artist, track = get_info()
    artist, track = process_info(artist, track)
    lyrics = get_lyrics(artist, track)

    # Adds a title to the lyrics
    lyrics = [" "] + [artist + " - " + track] + [" "] + lyrics + [" "]

    width = os.get_terminal_size().columns
    longest = len(max(lyrics, key=len))
    start = width - longest

    # Centers and prints the lyrics
    for line in lyrics:
        for i in range(0, int(start / 2) + int((longest - len(line)) / 2 )):
            line = " " + line
        print(line)


if __name__ == "__main__":
    main()
