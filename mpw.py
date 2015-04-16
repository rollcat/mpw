import flask
import mpd
import os
import uuid


SYMBOLS = {
    "fancy": {
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
            "shuffle": "🔃",
            "delete": "❌",
            "add": "➕",
            "song": "🎶",
            "folder": "📂",
            "logo": "𝄞",
        },
    },
    "simple": {
        "volume": {
            0: "[muted]", 1: "[quiet]", 2: "[normal]", 3: "[loud]",
        },
        "controls": {
            "stop": "[stop]",
            "play-pause": "[play/pause]",
            "play": "[play]",
            "pause": "[pause]",
            "prev": "[prev]",
            "next": "[next]",
            "fbackward": "[fast forward]",
            "fforward": "[fast backward]",
        },
        "other": {
            "refresh": "[refresh]",
            "shuffle": "[shuffle]",
            "delete": "[del]",
            "add": "[add]",
            "song": "[song]",
            "folder": "[folder]",
            "logo": "[music]",
        },
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


def get_symbols(default="simple"):
    return SYMBOLS[flask.session.setdefault("symbols", default)]


def rehydrate(item):
    symbols = get_symbols()
    if "file" in item:
        item.setdefault("title", os.path.basename(item["file"]))
        item.setdefault("artist", "?")
        item.setdefault("type", "file")
        item.setdefault("path", item["file"])
        item.setdefault("label", item["title"])
        item.setdefault("icon", symbols["other"]["song"])
    elif "directory" in item:
        item.setdefault("type", "directory")
        item.setdefault("path", item["directory"])
        item.setdefault("label", os.path.basename(item["path"]))
        item.setdefault("icon", symbols["other"]["folder"])
    return item


def get_current_context():
    playlist = list(map(rehydrate, app.mpd.playlistinfo()))
    song = rehydrate(app.mpd.currentsong())
    status = app.mpd.status()
    symbols = get_symbols()
    state = symbols["controls"][status["state"]]
    logo = symbols["other"]["logo"]
    status_line = (
        "{logo} {state} {artist} - {title}".format(
            logo=logo, state=state, **song
        )
        if status["state"] in {"play", "pause"} else
        "{logo} {state} Not playing".format(logo=logo, state=state)
    )
    return {
        "playlist": playlist,
        "song": song,
        "status": status,
        "status_line": status_line,
        "symbols": symbols,
        "autorefresh": flask.session["autorefresh"],
        "symbols_mode": flask.session["symbols"],
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
    return flask.render_template("base.html", **context)


@app.route("/browse/")
@app.route("/browse/<path:path>")
def browse(path=""):
    listing = list(map(rehydrate, app.mpd.lsinfo(path)))
    context = get_current_context()
    context["listing"] = listing
    context["path"] = path
    context["breadcrumbs"] = make_breadcrumbs(path)
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


@app.route("/settings/<string:key>/<string:value>", methods=["POST"])
def settings(key, value):
    schema = {
        "autorefresh": int,
        "symbols": str,
    }
    if key not in schema:
        flask.abort(404)
    flask.session[key] = schema[key](value)
    return flask.redirect(flask.url_for("index"))


if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--debug", action="store_const",
                           const=True, default=False)
    argparser.add_argument("--host", default="localhost")
    argparser.add_argument("--port", default=5000, type=int)
    args = argparser.parse_args()
    app.run(debug=args.debug, host=args.host, port=args.port)
