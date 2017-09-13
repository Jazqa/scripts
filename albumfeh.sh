#!/bin/sh

# Uses feh to display the album art of the current song

art="$(dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify /org/mpris/MediaPlayer2 org.freedesktop.DBus.Properties.Get string:'org.mpris.MediaPlayer2.Player' string:'Metadata' |grep /image/ |cut -d '"' -f2 |cut -d '/' -f 5-)"

feh https://i.scdn.co/image/${art} &
