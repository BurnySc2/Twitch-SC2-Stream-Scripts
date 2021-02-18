const functions = require("../overlay_files/js/build_order_step")

test("Script executes 'show_step' and 'hide_step' functions of build_order_step.js file and changes content of DOM", () => {
    // Create example HTML content
    document.body.innerHTML =
        '<div id="build-order-title" class="title">4 Hellion into Bio (Fantasy Build Order)</div>' +
        '<div id="bo-step0">Current step:</div>' +
        '<div class="flex-horizontal-container-bo">' +
        '<div id="bo-timer0" class="bo-animation-text">0:14</div>' +
        '<div id="bo-instruction0" class="bo-animation-text">Depot</div>' +
        "</div>" +
        '<div id="bo-step1">Next step:</div>' +
        '<div class="flex-horizontal-container-bo">' +
        '<div id="bo-timer1" class="bo-animation-text">0:40</div>' +
        '<div id="bo-instruction1" class="bo-animation-text">Barracks</div>' +
        "</div>"

    const payload = {
        payload_type: "build_order_step",
        step_type: "show_step",
        title: "3 CC Mech BO",
        step0_time: "0:45",
        step0_info: "Refinery",
        step1_time: "1:30",
        step1_info: "Factory",
        animation_time: 1000,
    }

    // Apply changes
    functions.show_step(payload)

    let timeoutId = setTimeout(() => {
        // Confirm / Check that the function 'show_step' changed content of the DOM
        expect(document.getElementById("build-order-title").textContent).toEqual("3 CC Mech BO")
        expect(document.getElementById("bo-timer0").textContent).toEqual("0:45")
        expect(document.getElementById("bo-instruction0").textContent).toEqual("Refinery")
        expect(document.getElementById("bo-timer1").textContent).toEqual("1:30")
        expect(document.getElementById("bo-instruction1").textContent).toEqual("Factory")

        expect(document.getElementsByTagName("body")[0].classList.contains("hidden")).toEqual(false)

        // Hide overlay
        const content_dict = {}
        functions.hide_step(content_dict)

        expect(document.getElementsByTagName("body")[0].classList.contains("hidden")).toEqual(true)
        expect(document.getElementsByTagName("body")[0].classList).toContain("hidden")
    }, payload["animation_time"])
})
