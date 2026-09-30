
// ==UserScript==
// @name         Naukri Candidates Details Extraction
// @match        https://resdex.naukri.com/*
// @grant        GM_xmlhttpRequest
// @connect      localhost
// @connect      *
// ==/UserScript==

(function () {
'use strict';

console.log("[TM] Script started");

let LOCATION = "";
let GENDER = "";
let CAND_NUM = 10;
let ACTIVE_IN = "6 months";
let REJECTED_IDS = new Set();
let STAR_TAGS = "";

/* =========================
   UTILS
========================= */

function wait(ms) {
  return new Promise(r => setTimeout(r, ms));
}

/* =========================
   UNIQUE ID EXTRACTOR
========================= */

function extractUniqueId(url) {
  try {
    const u = new URL(url);
    const uniqId = u.searchParams.get("uniqId");
    if (!uniqId || uniqId.length < 68) return null;

    return uniqId.substring(32, 68);
  } catch {
    return null;
  }
}

/* =========================
   ASK N8N FOR NEXT CANDIDATE
========================= */

function getNextCandidate() {

  console.log("[TM] Asking n8n for next candidate");

  GM_xmlhttpRequest({
    method: "POST",
    url: "http://localhost:5678/webhook/start-processing",

    onload: function(res) {

      const data = JSON.parse(res.responseText || "{}");

      if (!data.profileUrl) {
        console.log("[TM] No more candidates. Closing tab...");

          setTimeout(() => {
              window.close();
          }, 2000);
        return;
      }

      console.log("[TM] Opening candidate:", data.profileUrl);

      window.location.href = data.profileUrl;
    }
  });
}

/* =========================
   FETCH FILTERS FROM N8N
========================= */

function getFilters() {

  GM_xmlhttpRequest({
    method: "GET",
    url: "http://localhost:5678/webhook/get-filters",

    onload: function (res) {

      const data = JSON.parse(res.responseText);

      LOCATION = data.location || "";
      GENDER = data.gender || "";
      CAND_NUM = data.cand_num || 10;
      ACTIVE_IN = data.active_in || "6 months";
      STAR_TAGS = data.star || "";

      const rejectedProfiles = data.rejected_profiles || [];

      REJECTED_IDS = new Set(
        rejectedProfiles.map(url => extractUniqueId(url)).filter(Boolean)
      );

      handleStarFlow();
    }
  });
}

/* =========================
   WAIT FOR ELEMENT
========================= */

function waitForElement(selector, timeout = 10000) {

  return new Promise((resolve, reject) => {

    const start = Date.now();

    const interval = setInterval(() => {

      const el = document.querySelector(selector);

      if (el) {
        clearInterval(interval);
        resolve(el);
      }

      if (Date.now() - start > timeout) {
        clearInterval(interval);
        reject();
      }

    }, 400);

  });

}

async function handleStarFlow() {

  try {
    await wait(2000);
    // If no star tags → skip everything
    if (!STAR_TAGS || !STAR_TAGS.trim()) {
      console.log("[TM] No star tags → skipping modify flow");
      await applyActiveInFilter();
      applyFilters();
      return;
    }

    console.log("[TM] Star tags found:", STAR_TAGS);

    const tags = STAR_TAGS.split(",").map(t => t.trim().toLowerCase());

    /* =========================
       STEP 1: CLICK MODIFY
    ========================= */

    console.log("[TM] Looking for Modify button...");

      // Get all possible matches
      const modifyButtons = document.querySelectorAll('a.modify-btn');

      console.log("[TM] Found modify buttons:", modifyButtons.length);

      modifyButtons.forEach((btn, i) => {
          console.log(`[TM] Button ${i}:`, btn.innerText, btn);
      });

      // Try to find correct one
      let modifyBtn = null;

      for (const btn of modifyButtons) {
          if (btn.innerText.trim().toLowerCase() === "modify") {
              modifyBtn = btn;
              break;
          }
      }

      if (modifyBtn) {
          console.log("[TM] Clicking Modify button:", modifyBtn);
          modifyBtn.click();
      } else {
          console.log("[TM] Modify button NOT found");
      }

    await wait(2000);

    /* =========================
       STEP 2: TURN OFF BOOLEAN
    ========================= */

    const toggle = document.querySelector('input[name="toggleSwitch"]');

    if (toggle && toggle.checked) {
      toggle.click();
      console.log("[TM] Boolean turned OFF");
    }

    await wait(1500);

    /* =========================
       STEP 3: CLICK STAR TAGS
    ========================= */

    const allTagButtons = document.querySelectorAll('button.star-tag-wrapper');

    tags.forEach(tag => {

      allTagButtons.forEach(btn => {

        const label = btn.innerText.trim().toLowerCase();

        if (label === tag) {
          btn.click();
          console.log("[TM] Starred:", tag);
        }

      });

    });

    await wait(1500);

    /* =========================
       STEP 4: CLICK SEARCH
    ========================= */

    const searchBtn = document.querySelector('#adv-search-btn');

    if (searchBtn) {
      searchBtn.click();
      console.log("[TM] Clicked Search Candidates");
    }

    await wait(5000);

    /* =========================
       CONTINUE EXISTING FLOW
    ========================= */

    await applyActiveInFilter();
    applyFilters();

  }
  catch (err) {
    console.log("[TM] Star flow failed", err);
    await applyActiveInFilter();
    applyFilters(); // fallback
  }

}

async function applyActiveInFilter() {
  try {
    console.log("[TM] Applying Active In filter:", ACTIVE_IN);

    // STEP 1: Click dropdown
    const input = await waitForElement('#active-in');

    input.click();
    console.log("[TM] Clicked Active In dropdown");

    await wait(1000);

    // STEP 2: Get all options
    const options = document.querySelectorAll('#sa-dd-scrollactive-in li');

    let target = ACTIVE_IN.toLowerCase().trim();

    let matched = false;

    for (const li of options) {
      const text = li.innerText.toLowerCase().trim();

      // NORMAL MATCH
      if (text === target) {
        li.click();
        matched = true;
        console.log("[TM] Selected:", text);
        break;
      }

      // SPECIAL CASE: 1 year+
      if (target === "1 year+" && text.includes("1 year")) {
        li.click();
        matched = true;
        console.log("[TM] Selected special case:", text);
        break;
      }
    };

    if (!matched) {
      console.log("[TM] No matching Active In option found");
    }

    await wait(1500);

  } catch (err) {
    console.log("[TM] Active In filter failed", err);
  }
}

/* =========================
   APPLY FILTERS
========================= */

async function applyFilters() {

try {

  let filterApplied = false;

  if (GENDER) {

    const headers = document.querySelectorAll(".collapser-title-text");

    let diversityHeader;

    headers.forEach(h => {
      if (h.innerText.trim() === "Diversity hiring") diversityHeader = h;
    });

    if (diversityHeader) {

      const diversityExpand = diversityHeader.parentElement.querySelector("i.ico-expand");

      diversityExpand.click();

      await wait(3000);

      const genderCheckboxes = document.querySelectorAll('a[role="checkbox"]');

      genderCheckboxes.forEach(box => {

        const label = box.parentElement.innerText.toLowerCase();

        if (GENDER === "male" && label.includes("male")) {
          box.click();
          filterApplied = true;
        }

        if (GENDER === "female" && label.includes("female")) {
          box.click();
          filterApplied = true;
        }

      });

    }

  }

  await wait(500);

  if (filterApplied) {

    console.log("[TM] Applying filters → clicking refine");

    const refineButton = await waitForElement(".refine-search button");

    refineButton.click();

    setTimeout(extractCandidates, 7000);

  } else {

    console.log("[TM] No filters → skipping refine");

    extractCandidates();

  }

}
catch (err) {
  console.log("Filter failed");
}

}

/* =========================
   EXTRACT CANDIDATES
========================= */

function extractCandidates() {

  const links = document.querySelectorAll(".candidate-headline a");

  const candidates = [];

  for (const a of links) {

    const url = a.href;
    const id = extractUniqueId(url);

    // skip rejected
    if (id && REJECTED_IDS.has(id)) {
      continue;
    }

    candidates.push({
      name: a.innerText.trim(),
      profileUrl: url
    });

    if (candidates.length >= CAND_NUM) break;
  }

  GM_xmlhttpRequest({

    method: "POST",
    url: "http://localhost:5678/webhook/naukri-results",
    headers: { "Content-Type": "application/json" },

    data: JSON.stringify({
      runId: Date.now().toString(),
      candidates
    }),

    onload: async res => {

      const data = JSON.parse(res.responseText || "{}");

      if (data.profileUrl) {
        window.location.href = data.profileUrl;
        return;
      }

      getNextCandidate();
    }

  });

}

async function getPhoneNumber() {
    try {
        console.log("[TM] Triggering PyAutoGUI for phone click...");

        // STEP 1: Call Python to click button
        await new Promise((resolve) => {
            GM_xmlhttpRequest({
                method: "POST",
                url: "http://127.0.0.1:5001/view-phone",
                onload: () => {
                    console.log("[TM] PyAutoGUI click done");
                    resolve();
                }
            });
        });

        // STEP 2: Wait for number to appear
        await wait(2000);

        // STEP 3: Extract number
        const elements = document.querySelectorAll('div, span');

        for (let el of elements) {
            const text = el.innerText?.trim();

            if (/^\d{10}\s*\(M\)$/.test(text)) {
                console.log("[TM] Phone extracted:", text);
                return text;
            }
        }

    } catch (err) {
        console.log("[TM] Phone extraction failed", err);
        return "";
    }
}

/* =========================
   PROFILE PAGE LOGIC
========================= */

async function detectButtonAndProcess() {

    const btn = document.querySelector('button[aria-label="Download Resume"]');

    const profileSection = document.querySelector('.profile-summary');
    const nameElement = document.querySelector('.hlite-inherit');

    let email = "";

    const allSpans = document.querySelectorAll("span.hlite-inherit");

    for (let span of allSpans) {
        const text = span.innerText.trim();
        const title = span.getAttribute("title") || "";

        if (text.includes("@")) {
            email = text;
            break;
        }

        if (title.includes("@")) {
            email = title;
            break;
        }
    }

    let activeIn = "";

    const activeEl = Array.from(document.querySelectorAll("span"))
    .find(el => el.innerText.toLowerCase().includes("active in"));

    if (activeEl) {
        activeIn = activeEl.innerText.trim();
    }

    let experience = "";

    const expElement = document.querySelector('i[title="Experience"]');

    if (expElement) {
        const parent = expElement.parentElement;
        const span = parent ? parent.querySelector("span") : null;

        if (span) {
            experience = span.getAttribute("title") || span.innerText.trim();
        }
    }

    let location = "";

    const locationLabel = Array.from(document.querySelectorAll("span.lbl"))
        .find(el => el.innerText.toLowerCase().includes("pref. location"));

    if (locationLabel) {
        const parent = locationLabel.parentElement;
        const locSpan = parent ? parent.querySelector(".ellipsis") : null;

        if (locSpan) {
            location = locSpan.getAttribute("title") || locSpan.innerText.trim();
        }
    }

    let gender = "";

    const genderCell = Array.from(document.querySelectorAll(".table-cell"))
        .find(el => {
            const txt = el.innerText.toLowerCase();
            return txt.includes("male") || txt.includes("female");
        });

    if (genderCell) {
        gender = genderCell.innerText.trim();
    }

    const resumeText = profileSection ? profileSection.innerText.trim() : "";
    const candidateName = nameElement ? nameElement.innerText.trim() : "";
    const profileUrl = window.location.href;
    const phone = await getPhoneNumber();

    if (btn) {

        btn.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });
    }

    GM_xmlhttpRequest({
        method: "POST",
        url: "http://localhost:5678/webhook/send-profile",
        headers: { "Content-Type": "application/json" },
        data: JSON.stringify({
            candidateName,
            profileUrl,
            resumeText,
            email,
            activeIn,
            phone,
            experience,
            location,
            gender
        })
    });

    if (btn) {
        setTimeout(getNextCandidate, 10000);
    } else {
        getNextCandidate();
    }

}

/* =========================
   PAGE DETECTION
========================= */

function detectPage() {

  const url = window.location.href;

  if (url.includes("/v3/preview")) {
    setTimeout(detectButtonAndProcess, 2500);
    return;
  }

  if (url.includes("/v3/search")) {
    getFilters();
    return;
  }

}

/* =========================
   START
========================= */

setTimeout(detectPage, 3000);

})();

