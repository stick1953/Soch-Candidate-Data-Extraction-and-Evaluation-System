// ==UserScript==
// @name         Naukri Homepage
// @namespace    http://tampermonkey.net/
// @match        https://recruit.naukri.com/*
// @grant        GM_xmlhttpRequest
// @connect      localhost
// @run-at       document-idle
// ==/UserScript==

(function () {
    'use strict';

    if (window.naukriAutoSearchExecuted) return;
    window.naukriAutoSearchExecuted = true;

    const N8N_URL = "http://localhost:5678/webhook/get-field";

    function waitForElement(selector, timeout = 5000) {
        return new Promise((resolve, reject) => {
            const interval = 300;
            let elapsed = 0;

            const timer = setInterval(() => {
                const element = document.querySelector(selector);
                if (element) {
                    clearInterval(timer);
                    resolve(element);
                }
                elapsed += interval;
                if (elapsed >= timeout) {
                    clearInterval(timer);
                    reject("Element not found: " + selector);
                }
            }, interval);
        });
    }

    function fetchField() {
        return new Promise((resolve, reject) => {
            GM_xmlhttpRequest({
                method: "GET",
                url: N8N_URL,
                onload: function (response) {
                    try {
                        const data = JSON.parse(response.responseText);
                        resolve(data.fields);
                    } catch {
                        reject("Invalid JSON");
                    }
                },
                onerror: function () {
                    reject("Failed to connect to n8n");
                }
            });
        });
    }

    function setReactInputValue(input, value) {
        const nativeSetter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype,
            "value"
        ).set;

        nativeSetter.call(input, value);

        const event = new Event("input", { bubbles: true });
        input.dispatchEvent(event);
    }

    // Universal click helper
    function clickElement(el) {
        if (!el) return false;

        const clickable = el.closest("a, button");
        if (clickable) {
            clickable.click();
        } else {
            el.click();
        }
        return true;
    }

    async function handleStartupPopup() {
        try {
            let handled = false;

            // FIRST POPUP
            const closeBtn1 = document.querySelector(".mmr-icon-close");
            if (closeBtn1) {
                console.log("First popup → closing");
                clickElement(closeBtn1);
                handled = true;

                // small delay for chained popup
                await new Promise(r => setTimeout(r, 800));
            }

            // SECOND POPUP (robust fix)
            const closeBtn2 = document.querySelector('a[href="javascript:void(0)"]');

            if (closeBtn2) {
                console.log("Second popup → closing");
                closeBtn2.click();
                handled = true;
            }

            // FALLBACK BUTTON
            const buttons = document.querySelectorAll("button");
            for (let btn of buttons) {
                if (btn.innerText.includes("This is my account")) {
                    console.log("Fallback → clicking 'This is my account'");
                    btn.click();
                    handled = true;
                    break;
                }
            }

            return handled;

        } catch (err) {
            console.log("Popup handling error:", err);
            return false;
        }
    }

    async function run() {
        try {
            const popupHandled = await handleStartupPopup();

            if (popupHandled) {
                console.log("Popup handled, waiting for UI to stabilize...");
                await new Promise(r => setTimeout(r, 1500));
            }

            const fields = await fetchField();
            console.log("Fields:", fields);

            const wrapper = await waitForElement(".yluSq");
            wrapper.click();

            const realInput = await waitForElement(".yluSq.dKmYz input");

            realInput.focus();
            setReactInputValue(realInput, fields);

            console.log("Text entered");

            const searchBtn = await waitForElement(".jJK7z");
            searchBtn.click();

            console.log("Search clicked");

        } catch (err) {
            console.error("Automation failed:", err);
        }
    }

    setTimeout(run, 500);

})();