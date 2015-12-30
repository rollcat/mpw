# mpw - MPD on the Web

[![Build status](https://travis-ci.org/rollcat/mpw.svg)](https://travis-ci.org/rollcat/mpw)

Small [MPD](http://www.musicpd.org/) web client.

Recommended to only ever use on a trusted LAN and/or local machine.

Since it doesn't use any fancy advanced HTML features, it will
probably work on every single web browser in the world. Tested on
[Firefox](https://www.mozilla.org/en-US/firefox/),
[elinks](http://elinks.or.cz/), [dillo](http://www.dillo.org/),
[surf](http://surf.suckless.org/).

It uses some simple JS to enable keyboard shortcuts, and a tiny bit of
CSS to make things like playlists more readable.

Tech stack:

- [Python 3.4](https://www.python.org/)
- [`flask`](http://flask.pocoo.org/)
- [`python-mpd2`](https://pypi.python.org/pypi/python-mpd2)
