const functions = require("../overlay_files/js/match_info")

test("Script executes 'apply_changes' function of match_info.js file and changes content of DOM", () => {
    // Create example HTML content
    document.body.innerHTML =
        "<table>" +
        "<tr>" +
        '<td class="left">My MMR:</td>' +
        '<td id="p1mmr" class="left">9876?</td>' +
        "</tr>" +
        "<tr>" +
        '<td class="left">Opponent:</td>' +
        '<td id="p2name" class="left">TestTestTest</td>' +
        "</tr>" +
        "<tr>" +
        '<td class="left">Opp. Race:</td>' +
        '<td id="p2race" class="left">Terran</td>' +
        "</tr>" +
        "<tr>" +
        '<td class="left">Opp. MMR:</td>' +
        '<td id="p2mmr" class="left">8765?</td>' +
        "</tr>" +
        "<tr>" +
        '<td class="left">Opp. Stream:</td>' +
        '<td id="p2stream" class="left"></td>' +
        "</tr>" +
        "<tr>" +
        '<td class="left">Server:</td>' +
        '<td id="server" class="left">Europe</td>' +
        "</tr>" +
        "</table>"

    const payload = {
        payload_type: "match_info",
        p2name: "Idontknow",
        p2race: "P",
        p1mmr: "4444",
        p2mmr: "4555",
        p2stream: "rotterdam08",
        server: "Europe",
    }

    functions.apply_changes(payload)

    // Confirm / Check that the function 'apply_changes' changed content of the DOM
    expect(document.getElementById("p2name").textContent).toEqual("Idontknow")
    expect(document.getElementById("p2race").textContent).toEqual("P")
    expect(document.getElementById("p1mmr").textContent).toEqual("4444")
    expect(document.getElementById("p2mmr").textContent).toEqual("4555")
    expect(document.getElementById("p2stream").textContent).toEqual("rotterdam08")
    expect(document.getElementById("server").textContent).toEqual("Europe")
})
