
const hideBoSteps = () => {
    const node = document.getElementsByTagName("body")[0];
    node.classList.add("hidden");
};

const showBoSteps = () => {
    const node = document.getElementsByTagName("body")[0];
    node.classList.remove("hidden");
};

const changeBuildOrderInfo = (title_name, step0_time, step0_info, step1_time, step1_info, animation_time_ms) => {
    // Args example: ("4 Hellion into Bio (Fantasy Build Order)", "0:40", "Barracks", "0:45", "Refinery")

        const bo_title = document.getElementById("build-order-title");
        const timer0 = document.getElementById("bo-timer0");
        const instruction0 = document.getElementById("bo-instruction0");
        const timer1 = document.getElementById("bo-timer1");
        const instruction1 = document.getElementById("bo-instruction1");

        bo_title.style.transition = "opacity " + animation_time_ms.toString() + "ms ease-in-out";
        timer0.style.transition = "opacity " + animation_time_ms.toString() + "ms ease-in-out";
        instruction0.style.transition = "opacity " + animation_time_ms.toString() + "ms ease-in-out";
        timer1.style.transition = "opacity " + animation_time_ms.toString() + "ms ease-in-out";
        instruction1.style.transition = "opacity " + animation_time_ms.toString() + "ms ease-in-out";

        bo_title.style.opacity = "0";
        timer0.style.opacity = "0";
        instruction0.style.opacity = "0";
        timer1.style.opacity = "0";
        instruction1.style.opacity = "0";

    setTimeout(function(){
        bo_title.innerHTML = title_name;
        timer0.innerHTML = step0_time;
        instruction0.innerHTML = step0_info;
        timer1.innerHTML = step1_time;
        instruction1.innerHTML = step1_info;

        setTimeout(function(){
            bo_title.style.opacity = "1";
            timer0.style.opacity = "1";
            instruction0.style.opacity = "1";
            timer1.style.opacity = "1";
            instruction1.style.opacity = "1";
        }, animation_time_ms);
    }, animation_time_ms);
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
     *     "payload_type": "build_order_step",
     *     "vote_type": one of ["hide", "show", "change_info"],
     *     // If "change_info"
     *     "data": ["my bo name", "0:40", "Barracks", "0:45", "Refinery"],
     * }
    */
    if (content["payload_type"] === "build_order_step") {
        console.log(content);
        apply_changes(content);
        // TODO: run functions accordingly to json data type
        // document.getElementById("p1name").innerHTML = content["p1name"];
    }
};

window.onload = function(){
    // Hide build order steps
    // hideBoSteps();

    // show build order steps
    // showBoSteps();

    // Modify build order display
    changeBuildOrderInfo("4 Hellion into Bio (Fantasy Build Order)", "0:40", "Barracks", "0:45", "Refinery", 500)
};
