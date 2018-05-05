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
        spotify = stdout.strip().split( " - ")
        artist = spotify[0]
        track = spotify[1]

    elif pf == "win32" or "win64":
        # On Windows, data is available through win32gui
        text = win32gui.GetWindowText(win32gui.FindWindow("SpotifyMainWindow", None))

        # New Window 10 Spotify is not found with "SpotifyMainWindow" anymore, but "Chrome_WidgetWin_0" instead
        if len(text) == 0:
            # EnumHandler callback for win32gui.EnumWindows
            def find_spotify_uwp(hwnd, hwnds):
                text = win32gui.GetWindowText(hwnd)
                if win32gui.GetClassName(hwnd) == "Chrome_WidgetWin_0" and len(text) > 0:
                    hwnds.append(text)
            # Use win32gui.EnumWindows to flood the array with potential Spotify Windows
            # Note: Never seen other "Chrome_WidgetWin_0" instances with text
            hwnds = []
            win32gui.EnumWindows(find_spotify_uwp, hwnds)
            text = hwnds[0]

    return text.split(" - ",1)

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
