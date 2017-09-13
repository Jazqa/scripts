#!/bin/sh

# Uses wget to download the album art of the current Spotify song and displays it with neofetch

art="$(dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify /org/mpris/MediaPlayer2 org.freedesktop.DBus.Properties.Get string:'org.mpris.MediaPlayer2.Player' string:'Metadata' |grep /image/ |cut -d '"' -f2 |cut -d '/' -f 5-)"

if [ -z ${art} ]
then
    echo "Album art not found"
else
    wget https://i.scdn.co/image/${art} -O /tmp/${art}
    neofetch --w3m /tmp/${art}
    rm /tmp/${art}
fi
