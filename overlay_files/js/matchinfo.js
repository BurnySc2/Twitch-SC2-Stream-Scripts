
var ws = new WebSocket("ws://127.0.0.1:5678/");

function apply_changes(content) {
    $("#p1name").html(content["p1name"]);
    $("#p2name").html(content["p2name"]);
    $("#p1race").html(content["p1race"]);
    $("#p2race").html(content["p2race"]);
    $("#p1mmr").html(content["p1mmr"]);
    $("#p2mmr").html(content["p2mmr"]);
    $("#p2stream").html(content["p2stream"]);
    $("#server").html(content["server"]);
}

ws.onmessage = function (event) {
    content_raw = event.data;
    content = JSON.parse(content_raw);
    // All overlay files use the same websocket connection, so need to specify the type of json / payload here if it should be used at all
    if (content["payload_type"] === "match_info") {
        console.log(content);
        apply_changes(content);
    }
};