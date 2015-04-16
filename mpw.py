import flask
import mpd


SYMBOLS = {
    "volume": {
        0: "🔇", 1: "🔈", 2: "🔉", 3: "🔊",
    },
    "controls": {
        "stop": "◼",
        "play-pause": "⏯",
        "play": "⏵",
        "pause": "⏸",
        "prev": "⏮",
        "next": "⏭",
        "fbackward": "⏪",
        "fforward": "⏩",
    },
}

app = flask.Flask(__name__)
app.mpd = mpd.MPDClient()


@app.before_request
def mpd_connect():
    try:
        app.mpd.connect("localhost", 6600, timeout=1)
    except mpd.ConnectionError as e:
        if e.args[0] == "Already connected":
            pass


@app.after_request
def mpd_disconnect(response):
    app.mpd.close()
    app.mpd.disconnect()
    return response


@app.route("/")
def index():
    playlist = app.mpd.playlistinfo()
    song = app.mpd.currentsong()
    status = app.mpd.status()
    icon = SYMBOLS["controls"][status["state"]]
    status_line = (
        "{icon} {artist} - {title}".format(icon=icon, **song)
        if song else
        "{icon} Not playing".format(icon=icon)
    )
    context = {
        "playlist": playlist,
        "song": song,
        "status": status,
        "status_line": status_line,
        "symbols": SYMBOLS,
    }
    return flask.render_template("base.html", **context)


@app.route("/controls/<action>", methods=["POST"])
def controls(action):
    state = app.mpd.status()["state"]
    if action == "play-pause" and state == "stop":
        app.mpd.play()
    elif action == "play-pause" and state in {"play", "pause"}:
        app.mpd.pause()
    elif action == "play-pause":
        pass  # ???
    elif action == "stop":
        app.mpd.stop()
    elif action == "prev":
        app.mpd.previous()
    elif action == "next":
        app.mpd.next()
    else:
        pass  # ???
    return flask.redirect(flask.url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
