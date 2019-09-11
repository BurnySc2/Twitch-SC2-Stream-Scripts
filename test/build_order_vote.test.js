const functions = require("../overlay_files/js/build_order_vote");

test("Adds 2 + 2 to equal 4", () => {
    expect(functions.add(2, 2)).toBe(4);
});

// Test manipulation of HTML / DOM

// Function "start_vote" should manipulate a div element with id "vote-choices" to have the same amount of children as there are build orders
// Function "update_vote" should change the width and percentage value of the vote bars
// Function "end_vote" should add a class to 'document.getElementsByTagName("body")[0]' with name 'hidden' and change opacity to 0


test("Script executes 'start_vote' and 'update_vote' functions of build_order_vote.js file and changes content of DOM", () => {

    // Set up the required HTML
    document.body.innerHTML =
        '<div id="vote-choices">' +
        '</div>' +
        '<div class="flex-horizontal-container">' +
        '   <div id="info1">Unique votes: 7</div>' +
        '   <div id="info2">Time active: 14 seconds</div>' +
        '</div>';



    // Test 'start_vote' function
    let content_dict = {
        "bos": ["build order 1", "build order 2", "build order 3"]
    };
    functions.start_vote(content_dict);

    // The content should show, thus it should remove the 'hidden' class
    expect(document.getElementsByTagName("body")[0].classList.contains("hidden")).toEqual(false);

    // Test that the build orders have been added correctly
    expect(document.getElementById("vote-choices").childElementCount).toEqual(3);
    expect(document.getElementById("vote-choices").childElementCount).toEqual(3);

    // Test that the info fields of unique votes and active time has changed
    expect(document.getElementById("info1").textContent).toEqual("Unique votes: 0");
    expect(document.getElementById("info2").textContent).toEqual("Time active: 0 seconds");

    // Test that the fields have been properly filled out
    for (let i = 0; i < content_dict["bos"].length; i++) {
        expect(document.getElementById("bo" + i.toString() + "-name").textContent).toEqual("build order " + (i + 1).toString());
        expect(document.getElementById("bo" + i.toString() + "-percentage").textContent).toEqual("0%");
        expect(document.getElementById("bo" + i.toString() + "-bar").style.width).toEqual("0%");
    }



    // Test 'update_vote' function
    content_dict = {
        "percentages": ["25%", "50%", "25%"],
        "unique_votes": "8",
        "time_active": "10",
    };
    functions.update_vote(content_dict);

    for (let i = 0; i < content_dict["percentages"].length; i++) {
        expect(document.getElementById("bo" + i.toString() + "-percentage").textContent).toEqual(content_dict["percentages"][i]);
        expect(document.getElementById("bo" + i.toString() + "-bar").style.width).toEqual(content_dict["percentages"][i]);
    }
    expect(document.getElementById("info1").textContent).toEqual("Unique votes: 8");
    expect(document.getElementById("info2").textContent).toEqual("Time active: 10 seconds");




    // Test "end_vote" function which adds 'hidden' class
    content_dict = {};
    functions.end_vote(content_dict);
    expect(document.getElementsByTagName("body")[0].classList.contains("hidden")).toEqual(true);
    expect(document.getElementsByTagName("body")[0].classList).toContain("hidden");
});
