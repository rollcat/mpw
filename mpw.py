import flask
import mpd
import os
import uuid


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
    "other": {
        "refresh": "🔃",
        "delete": "❌",
        "add": "➕",
        "song": "🎶",
        "folder": "📂",
    },
}

app = flask.Flask(__name__)
app.mpd = mpd.MPDClient()
app.secret_key = hex(uuid.getnode())  # WARNING: **VERY INSECURE**


@app.before_request
def mpd_connect():
    flask.session.setdefault("autorefresh", 0)
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


def rehydrate(item):
    if "file" in item:
        item.setdefault("title", os.path.basename(item["file"]))
        item.setdefault("artist", "?")
        item.setdefault("type", "file")
        item.setdefault("path", item["file"])
        item.setdefault("label", item["title"])
        item.setdefault("icon", SYMBOLS["other"]["song"])
    elif "directory" in item:
        item.setdefault("type", "directory")
        item.setdefault("path", item["directory"])
        item.setdefault("label", os.path.basename(item["path"]))
        item.setdefault("icon", SYMBOLS["other"]["folder"])
    return item


def get_current_context():
    playlist = list(map(rehydrate, app.mpd.playlistinfo()))
    song = rehydrate(app.mpd.currentsong())
    status = app.mpd.status()
    state = SYMBOLS["controls"][status["state"]]
    status_line = (
        "{state} {artist} - {title}".format(state=state, **song)
        if status["state"] in {"play", "pause"} else
        "{state} Not playing".format(state=state)
    )
    return {
        "playlist": playlist,
        "song": song,
        "status": status,
        "status_line": status_line,
        "symbols": SYMBOLS,
    }


def make_breadcrumbs(path):
    breadcrumbs = [{"label": "/", "path": "/"}]
    path_elems = filter(None, path.strip("/").split("/"))
    for elem in path_elems:
        breadcrumbs.append({
            "label": elem,
            "path": os.path.join(breadcrumbs[-1]["path"], elem)
        })
    breadcrumbs.pop(0)
    return breadcrumbs


@app.route("/")
def index():
    context = get_current_context()
    context["autorefresh"] = flask.session["autorefresh"]
    return flask.render_template("base.html", **context)


@app.route("/browse/")
@app.route("/browse/<path:path>")
def browse(path=""):
    listing = list(map(rehydrate, app.mpd.lsinfo(path)))
    context = get_current_context()
    context["listing"] = listing
    context["path"] = path
    context["breadcrumbs"] = make_breadcrumbs(path)
    context["autorefresh"] = flask.session["autorefresh"]
    return flask.render_template("browse.html", **context)


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


@app.route("/playlist/<action>", methods=["POST"])
def playlist_action(action):
    if action == "clear-old":
        status = app.mpd.status()
        if "song" in status:
            song = int(status["song"])
            for i in range(song):
                app.mpd.delete(0)
        else:
            app.mpd.clear()
    elif action == "shuffle":
        app.mpd.shuffle()
    else:
        pass  # ???
    return flask.redirect(flask.url_for("index"))


@app.route("/playlist/<action>/<int:song>", methods=["POST"])
def playlist_action_song(action, song):
    if action == "play":
        app.mpd.play(song)
    elif action == "delete":
        app.mpd.delete(song)
    else:
        pass  # ???
    return flask.redirect(flask.url_for("index"))


@app.route("/library/<action>/<path:path>", methods=["POST"])
def library(action, path):
    if action == "add":
        app.mpd.add(path)
    elif action == "replace-play":
        app.mpd.clear()
        app.mpd.add(path)
        app.mpd.play()
    else:
        pass  # ???
    return flask.redirect(flask.url_for("index"))


@app.route("/settings/autorefresh/<int:value>", methods=["POST"])
def settings_autorefresh(value):
    flask.session["autorefresh"] = int(value)
    return flask.redirect(flask.url_for("index"))


if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--debug", action="store_const",
                           const=True, default=False)
    args = argparser.parse_args()
    app.run(debug=args.debug)
