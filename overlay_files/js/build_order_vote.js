const clearAllChildren = () => {
    const node = document.getElementById("vote-choices")
    // console.log(node);
    // Remove all children of div
    // https://stackoverflow.com/a/40606838/10811826
    while (node.firstChild) {
        node.firstChild.remove()
    }
}

const hideVote = () => {
    // Hide the whole overlay
    const node = document.getElementsByTagName("body")[0]
    node.style.opacity = "0"
}

const showVote = () => {
    // Show the whole overlay
    const node = document.getElementsByTagName("body")[0]
    node.style.opacity = "1"
}

const changePercentage = (element_number, percentage_value) => {
    // Args example: (0, "75%")
    const object_bo_percentage = document.getElementById(`bo${element_number}-percentage`)
    object_bo_percentage.innerHTML = percentage_value

    const bar = document.getElementById(`bo${element_number}-bar`)
    bar.style.width = percentage_value
}

const changeInfo = (current_matchup, unique_votes, time_active, time_till_vote_ends) => {
    // Args example: ("TvP", 15, 20, 25)
    // console.log(`Changing info: ${current_matchup} ${unique_votes} ${time_active} ${time_till_vote_ends}`)
    if (current_matchup) {
        const vote_title = document.getElementById("vote-title")
        vote_title.innerHTML = `Vote ${current_matchup} Build Order`
    }

    const unique_votes_object = document.getElementById("info1")
    unique_votes_object.innerHTML = `Unique votes: ${unique_votes}`

    const time_active_object = document.getElementById("info2")
    time_active_object.innerHTML = "Time active: " + time_active + " seconds"

    const time_till_vote_ends_object = document.getElementById("info3")
    time_till_vote_ends_object.innerHTML = "Time limit: " + time_till_vote_ends + " seconds"
}

const addVoteChild = (bo_description) => {
    const node = document.getElementById("vote-choices")
    // console.log(node.childElementCount);
    let child_element_count = node.childElementCount

    let div1 = document.createElement("div")
    div1.id = `bo${child_element_count}-name`
    div1.classList.add("text-2xl")
    div1.innerHTML = bo_description

    let div2 = document.createElement("div")
    div2.id = `bo${child_element_count}-percentage`
    div2.classList.add("text-bo-vote-percentage")
    div2.innerHTML = "0%"

    // Inner part 1
    let div_flex_horizontal = document.createElement("div")
    div_flex_horizontal.classList.add("flex")
    div_flex_horizontal.classList.add("justify-between")
    div_flex_horizontal.appendChild(div1)
    div_flex_horizontal.appendChild(div2)

    // Inner part 2
    let bar = document.createElement("div")
    bar.classList.add("bar")
    bar.id = `bo${child_element_count}-bar`
    bar.style.width = "0%"

    let bar_wrapper = document.createElement("div")
    bar_wrapper.classList.add("bar-wrapper")
    bar_wrapper.appendChild(bar)

    // Choice number
    let choice_number = document.createElement("div")
    choice_number.classList.add("m-2")
    choice_number.classList.add("text-2xl")
    choice_number.innerHTML = `${child_element_count + 1})`

    // Choice
    let choice = document.createElement("div")
    choice.classList.add("flex")
    choice.classList.add("flex-col")
    choice.classList.add("m-2")
    choice.classList.add("w-full")
    choice.appendChild(div_flex_horizontal)
    choice.appendChild(bar_wrapper)

    // Outer flex horizontal container
    let outer_flex_horizontal_container = document.createElement("div")
    outer_flex_horizontal_container.classList.add("flex")
    outer_flex_horizontal_container.appendChild(choice_number)
    outer_flex_horizontal_container.appendChild(choice)

    // Append to choices
    node.appendChild(outer_flex_horizontal_container)
}

// Functions used by websocket
// start vote, update vote, end vote
const start_vote = (content_dict) => {
    clearAllChildren()
    for (const bo of content_dict["bos"]) {
        addVoteChild(bo)
    }
    for (const index in content_dict["bos"]) {
        changePercentage(index, "0%")
    }
    const current_matchup = content_dict["current_matchup"]
    console.log(`Received start_vote: ${JSON.stringify(content_dict, null, 2)}`)
    changeInfo(current_matchup, 0, 0, 0)
    showVote()
}

const update_vote = (content_dict) => {
    for (const index in content_dict["percentages"]) {
        changePercentage(index, content_dict["percentages"][index])
    }
    const unique_votes = content_dict["unique_votes"]
    const time_active = content_dict["time_active"]
    const time_till_vote_ends = content_dict["time_till_vote_ends"]
    changeInfo("", unique_votes, time_active, time_till_vote_ends)
}

const end_vote = (content_dict) => {
    hideVote()
}

const connect = () => {
    // New websocket connection
    var ws = new WebSocket("ws://127.0.0.1:5678/")

    ws.onmessage = function (event) {
        content_raw = event.data
        content = JSON.parse(content_raw)
        // All overlay files use the same websocket connection, so need to specify the type of json / payload here if it should be used at all
        /**
         * Example Data:
         * {
         *     "payload_type": "build_order_vote",
         *     "vote_type": one of ["start_vote", "update_vote", "end_vote"],
         *
         *     // If "start_vote"
         *     "current_matchup": "TvP",
         *     "bos": ["my first bo", "my second bo"],
         *
         *     // if "update_vote"
         *     "current_matchup": "",
         *     "percentages": ["25%", "25%", "50%"],
         *     "unique_votes": 12,
         *     "time_active": 15,
         * }
         */
        if (content["payload_type"] === "build_order_vote") {
            if (content["vote_type"] === "start_vote") {
                start_vote(content)
            } else if (content["vote_type"] === "update_vote") {
                update_vote(content)
            } else if (content["vote_type"] === "end_vote") {
                end_vote(content)
            }
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

    // Hide the voting system after delay
    // setTimeout(() => {
    //     hideVote();
    // }, 3000)

    // Show the voting system after delay
    // setTimeout(() => {
    //     showVote();
    // }, 6000)

    // Add new child element to vote choices
    // addVoteChild("big yikes")

    // Modify percentage of a build
    // changePercentage(1, "30%")

    // Modify info at bottom
    // changeInfo(15, 25)

    // Test websocket functions:
    // start_vote({
    //     "bos": ["yikes", "yikers"]
    // });
    // setTimeout(() => {
    //     update_vote({
    //         "percentages": ["30%", "70%"],
    //         "unique_votes": 10,
    //         "time_active": 20,
    //     });
    //
    //     setTimeout(() => {
    //         end_vote({});
    //
    //     }, 2000)
    // }, 1000);
}

const add = (num1, num2) => num1 + num2

module.exports = {
    add: add,
    start_vote: start_vote,
    update_vote: update_vote,
    end_vote: end_vote,
}
