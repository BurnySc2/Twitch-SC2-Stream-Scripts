function apply_changes(content) {
    // document.getElementById("p1name").textContent = content["p1name"];
    document.getElementById("p2name").textContent = content["p2name"]
    // document.getElementById("p1race").textContent = content["p1race"];
    document.getElementById("p2race").textContent = content["p2race"]
    document.getElementById("p1mmr").textContent = content["p1mmr"]
    document.getElementById("p2mmr").textContent = content["p2mmr"]
    document.getElementById("p2stream").textContent = content["p2stream"]
    document.getElementById("server").textContent = content["server"]
}

const connect = () => {
    // New websocket connection
    var ws = new WebSocket("ws://127.0.0.1:5678/")

    ws.onmessage = function (event) {
        content_raw = event.data
        content = JSON.parse(content_raw)
        // All overlay files use the same websocket connection, so need to specify the type of json / payload here if it should be used at all
        /*
        Example payload:
        {
            "payload_type": "match_info",
            "p2name": "Idontknow",
            "p2race": "Z",
            "p1mmr": "4444",
            "p2mmr": "4555",
            "p2stream": "BurnySc2",
            "server": "Europe"
        }
         */
        if (content["payload_type"] === "match_info") {
            // console.log(content);
            apply_changes(content)
        }
    }

    ws.onclose = (e) => {
        // console.log("Lost connection")
        setTimeout(() => {
            // console.log("Trying to reconnect")
            connect()
        }, 5000)
    }

    ws.onerror = (err) => {
        ws.close()
    }
}

window.onload = function () {
    connect()
}

module.exports = {
    apply_changes: apply_changes,
}
