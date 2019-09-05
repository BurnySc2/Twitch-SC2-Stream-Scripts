
var ws = new WebSocket("ws://127.0.0.1:5678/");

function apply_changes(content) {
    document.getElementById("p1name").innerHTML = content["p1name"];
    document.getElementById("p2name").innerHTML = content["p2name"];
    document.getElementById("p1race").innerHTML = content["p1race"];
    document.getElementById("p2race").innerHTML = content["p2race"];
    document.getElementById("p1mmr").innerHTML = content["p1mmr"];
    document.getElementById("p2mmr").innerHTML = content["p2mmr"];
    document.getElementById("p2stream").innerHTML = content["p2stream"];
    document.getElementById("server").innerHTML = content["server"];
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