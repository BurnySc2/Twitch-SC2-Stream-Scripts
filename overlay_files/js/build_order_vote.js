
const clearAllChildren = () => {
    const node = document.getElementById("vote-choices");
    // console.log(node);
    // Remove all children of div
    // https://stackoverflow.com/a/40606838/10811826
    while (node.firstChild) {
        node.firstChild.remove();
    }
};

const hideVote = () => {
    const node = document.getElementsByTagName("body")[0];
    node.classList.add("hidden");
};

const showVote = () => {
    const node = document.getElementsByTagName("body")[0];
    node.classList.remove("hidden");
};

const changePercentage = (element_number, percentage_value) => {
    // Args example: (0, "75%")
    const object_bo_percentage = document.getElementById("bo" + element_number.toString());
    object_bo_percentage.innerHTML = percentage_value;

    const bar = document.getElementById("bar" + element_number.toString());
    bar.style.width = percentage_value;
};

const changeInfo = (unique_votes, time_active) => {
    // Args example: (15, 25)
    const unique_votes_object = document.getElementById("info1");
    unique_votes_object.innerHTML = "Unique votes: " + unique_votes;

    const time_active_object = document.getElementById("info2");
    time_active_object.innerHTML = "Time active: " + time_active + " seconds";
};

const addVoteChild = (bo_description) => {
    const node = document.getElementById("vote-choices");
    // console.log(node.childElementCount);
    let child_element_count = node.childElementCount;

    let div1 = document.createElement("div");
    div1.classList.add("text-bo-description");
    div1.innerHTML = bo_description;

    let div2 = document.createElement("div");
    div2.id = "bo" + child_element_count;
    div2.classList.add("text-bo-vote-percentage");
    div2.innerHTML = "0%";

    // Inner part 1
    let div_flex_horizontal = document.createElement("div");
    div_flex_horizontal.classList.add("flex-horizontal-bo-percentage");
    div_flex_horizontal.appendChild(div1);
    div_flex_horizontal.appendChild(div2);

    // Inner part 2
    let bar = document.createElement("div");
    bar.classList.add("bar");
    bar.id = "bar" + child_element_count;
    bar.style.width = "0%";

    let bar_wrapper = document.createElement("div");
    bar_wrapper.classList.add("bar-wrapper");
    bar_wrapper.appendChild(bar);

    // Choice number
    let choice_number = document.createElement("div");
    choice_number.classList.add("choice-number");
    choice_number.innerHTML = (child_element_count + 1).toString() + ")";

    // Choice
    let choice = document.createElement("div");
    choice.classList.add("choice");
    choice.appendChild(div_flex_horizontal);
    choice.appendChild(bar_wrapper);

    // Outer flex horizontal container
    let outer_flex_horizontal_container = document.createElement("div");
    outer_flex_horizontal_container.classList.add("flex-horizontal-container");
    outer_flex_horizontal_container.appendChild(choice_number);
    outer_flex_horizontal_container.appendChild(choice);

    // Append to choices
    node.appendChild(outer_flex_horizontal_container);
};

// Websocket functions
var ws = new WebSocket("ws://127.0.0.1:5678/");

ws.onmessage = function (event) {
    content_raw = event.data;
    content = JSON.parse(content_raw);
    // All overlay files use the same websocket connection, so need to specify the type of json / payload here if it should be used at all
    /**
     * Example Data:
     * {
     *     "payload_type": "build_order_vote",
     *     "vote_type": one of ["hide", "show", "clear", "change_percentage", "change_info", "add_children"],
     *     // If "add_children"
     *     "data": ["my first bo", "my second bo"],
     *     // if "change_percentage", submit new percentage values and unique votes and time active
     *     "data": ["25%", "25%", "50%", 15, 15],
     * }
    */
    if (content["payload_type"] === "build_order_vote") {
        console.log(content);
        apply_changes(content);
        // TODO: run functions accordingly to json data type
        // document.getElementById("p1name").innerHTML = content["p1name"];
    }
};

window.onload = function(){
    // Animate width of first bar
    // https://developer.mozilla.org/en-US/docs/Web/CSS/transition
    // const test = document.getElementById("bar1");
    // test.style.width = "75%";

    // Clear all children
    // clearAllChildren();

    // Hide the voting system
    // hideVote();

    // Show the voting system
    // showVote();

    // Add new child element to vote choices
    // addVoteChild("big yikes")

    // Modify percentage of a build
    // changePercentage(1, "30%")

    // Modify info at bottom
    // changeInfo(15, 25)
};
