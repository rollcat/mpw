"use strict";
var $=$?$:{};
var handle_state = null;

function key_main(event) {
    switch (event.key)  {
    case "g":
        handle_state = key_go;
        return;

    case "j":
        $('html, body').animate({scrollTop: $(document).height()}, 0);
        return;
    case "k":
        $('html, body').animate({scrollTop: 0}, 0);
        return;

    case "h":
        $('#controls-prev').click();
        return;
    case "l":
        $('#controls-next').click();
        return;

    case "p":
        $('#controls-play-pause').click();
        return;
    case "s":
        $('#controls-stop').click();
        return;

    case "x":
        $('#playlist-clear-old').click();
        return;

    default:
        console.log(event.key);
    }
}

function key_go(event) {
    switch (event.key)  {
    case "p":
        window.location = "/";
        break;
    case "b":
        window.location = "/browse/";
        break;

    case "a":
        $('#settings-autorefresh').click();
        break;
    case "f":
        $('#settings-fancy').click();
        break;

    default:
        console.log(event.key);
    }
    handle_state = key_main;
}

$(document).ready(function() {
    handle_state = key_main;
    $(document).keydown(function (event) {
        handle_state(event);
    });
});
