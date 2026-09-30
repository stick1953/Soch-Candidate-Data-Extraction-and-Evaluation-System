// ==UserScript==
// @name         Naukri Auto Reset Login
// @namespace    http://tampermonkey.net/
// @version      3.0
// @description  Auto click Reset Subuser and Reset & Login
// @match        https://resdex.naukri.com/v2/ChangeLogin/*
// @match        https://resdex.naukri.com/v2/ResetLogin/*
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    const url = window.location.href;

    // -------- PAGE 1: ChangeLogin --------
    if (url.includes("ChangeLogin")) {
        console.log("On ChangeLogin page");

        function clickResetTab() {
            let tabs = document.querySelectorAll('a');

            for (let tab of tabs) {
                if (tab.innerText.includes("Reset Subuser")) {
                    console.log("Clicking Reset Subuser tab...");
                    tab.click();
                    return;
                }
            }

            console.log("Waiting for Reset Subuser tab...");
            setTimeout(clickResetTab, 1000);
        }

        setTimeout(clickResetTab, 2000);
    }

    // -------- PAGE 2: ResetLogin --------
    if (url.includes("ResetLogin")) {
        console.log("On ResetLogin page");

        function clickResetButton() {
            let btn = document.querySelector('#resetLoginRadioBtn');

            if (btn) {
                console.log("Clicking Reset & Login button...");
                btn.click();
            } else {
                console.log("Waiting for Reset & Login button...");
                setTimeout(clickResetButton, 1000);
            }
        }

        setTimeout(clickResetButton, 2000);
    }

})();