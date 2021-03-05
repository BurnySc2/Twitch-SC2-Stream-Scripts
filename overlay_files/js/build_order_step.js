// Store the timeout id, cancel timeout if "changeBuildOrderInfo" is called multiple times
let timeoutId = 0

const hideBoSteps = () => {
    const node = document.getElementsByTagName("body")[0]
    node.style.opacity = "0"
}

const showBoSteps = () => {
    const node = document.getElementsByTagName("body")[0]
    node.style.opacity = "1"
}

const changeBuildOrderInfo = (
    title_name,
    step0_time,
    step0_info,
    step1_time,
    step1_info,
    animation_time_ms
) => {
    // Args example: ("4 Hellion into Bio (Fantasy Build Order)", "0:40", "Barracks", "0:45", "Refinery", 500)

    const bo_title = document.getElementById("build-order-title")
    const timer0 = document.getElementById("bo-timer0")
    const instruction0 = document.getElementById("bo-instruction0")
    const timer1 = document.getElementById("bo-timer1")
    const instruction1 = document.getElementById("bo-instruction1")

    // Same content was broadcasted, return early without doing animation
    if (timer0.textContent === step0_time) {
        return
    }

    const elements = [timer0, instruction0, timer1, instruction1]

    for (const element of elements) {
        element.style.transition = "opacity " + animation_time_ms.toString() + "ms ease-in-out"
        element.style.opacity = "0"
    }

    if (timeoutId !== 0) {
        clearTimeout(timeoutId)
    }
    timeoutId = setTimeout(() => {
        bo_title.textContent = title_name
        timer0.textContent = step0_time
        instruction0.textContent = step0_info
        timer1.textContent = step1_time
        instruction1.textContent = step1_info

        for (const element of elements) {
            element.style.opacity = "1"
        }
        timeoutId = 0
    }, animation_time_ms)
}

// Functions used by websocket
// start vote, update vote, end vote
const show_step = (content_dict) => {
    showBoSteps()
    const title = content_dict["title"]
    const step0_time = content_dict["step0_time"]
    const step0_info = content_dict["step0_info"]
    const step1_time = content_dict["step1_time"]
    const step1_info = content_dict["step1_info"]
    changeBuildOrderInfo(
        title,
        step0_time,
        step0_info,
        step1_time,
        step1_info,
        content_dict["animation_time"]
    )
    // changeBuildOrderInfo("4 Hellion into Bio (Fantasy Build Order)", "0:40", "Barracks", "0:45", "Refinery", 1000);
}

const hide_step = (content_dict) => {
    hideBoSteps()
}

const connect = () => {
    // New websocket connection
    let ws = new WebSocket("ws://127.0.0.1:5678/")

    ws.onmessage = function (event) {
        content_raw = event.data
        content = JSON.parse(content_raw)
        // All overlay files use the same websocket connection, so need to specify the type of json / payload here if it should be used at all
        /**
         * Example Data:
         * {
         *     "payload_type": "build_order_step",
         *     "step_type": one of ["show_step", "hide_step"],
         *
         *     // If "show_step"
         *     "title": "4 Hellion into Bio (Fantasy Build Order)",
         *     "step0_time": "0:40",
         *     "step0_info": "Barracks",
         *     "step1_time": "0:45",
         *     "step1_info": "Refinery",
         *     "animation_time": 1000,
         * }
         */
        if (content["payload_type"] === "build_order_step") {
            if (content["step_type"] === "show_step") {
                show_step(content)
            } else if (content["step_type"] === "hide_step") {
                hide_step(content)
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

    // Hide build order steps
    // hideBoSteps();

    // show build order steps
    // showBoSteps();

    // Modify build order display
    // changeBuildOrderInfo("4 Hellion into Bio (Fantasy Build Order)", "0:40", "Barracks", "0:45", "Refinery", 1000);

    // Try to trigger another animation while the animation is still going
    // setTimeout(() => {
    //     changeBuildOrderInfo("4 Hellion into Bio (Fantasy Build Order)", "0:45", "Refinery", "1:30", "Reaper", 1000);
    // }, 2500);
}

module.exports = {
    show_step: show_step,
    hide_step: hide_step,
}
