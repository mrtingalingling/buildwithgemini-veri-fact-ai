// VeriFact AI - Chrome Extension Content Script
// Extracts webpage text and dynamically highlights verified/false claims with WOT-style tooltips.

// Ensure styles are injected once into host page
function injectVeriFactStyles() {
  if (document.getElementById("verifact-injected-styles")) return;
  const styleTag = document.createElement("style");
  styleTag.id = "verifact-injected-styles";
  styleTag.textContent = `
    .verifact-highlight {
      position: relative !important;
      cursor: pointer !important;
      border-radius: 4px !important;
      padding: 1px 4px !important;
      font-weight: 500 !important;
      display: inline !important;
      transition: all 0.2s ease !important;
    }
    
    .verifact-verdict-true {
      background-color: rgba(46, 213, 115, 0.22) !important;
      border-bottom: 2px solid #2ed573 !important;
      color: inherit !important;
    }

    .verifact-verdict-false {
      background-color: rgba(255, 71, 87, 0.22) !important;
      border-bottom: 2px solid #ff4757 !important;
      color: inherit !important;
    }

    .verifact-verdict-misleading {
      background-color: rgba(255, 171, 0, 0.22) !important;
      border-bottom: 2px solid #ffab00 !important;
      color: inherit !important;
    }

    /* WOT (Web of Trust) Style Floating Tooltip */
    .verifact-tooltip {
      position: absolute !important;
      bottom: 125% !important;
      left: 50% !important;
      transform: translateX(-50%) translateY(6px) !important;
      opacity: 0 !important;
      visibility: hidden !important;
      pointer-events: none !important;
      width: 270px !important;
      background: #0b0d17 !important;
      border: 1px solid #00f5d4 !important;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.85), 0 0 15px rgba(0, 245, 212, 0.25) !important;
      border-radius: 10px !important;
      padding: 10px 12px !important;
      color: #f3f4f6 !important;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
      font-size: 12px !important;
      line-height: 1.4 !important;
      text-align: left !important;
      white-space: normal !important;
      z-index: 2147483647 !important;
      transition: opacity 0.2s ease, transform 0.2s ease, visibility 0.2s ease !important;
    }

    .verifact-tooltip::after {
      content: "" !important;
      position: absolute !important;
      top: 100% !important;
      left: 50% !important;
      margin-left: -6px !important;
      border-width: 6px !important;
      border-style: solid !important;
      border-color: #00f5d4 transparent transparent transparent !important;
    }

    .verifact-highlight:hover .verifact-tooltip {
      opacity: 1 !important;
      visibility: visible !important;
      transform: translateX(-50%) translateY(0) !important;
      pointer-events: auto !important;
    }

    .verifact-badge-true { color: #2ed573 !important; font-weight: 700 !important; }
    .verifact-badge-false { color: #ff4757 !important; font-weight: 700 !important; }
    .verifact-badge-misleading { color: #ffab00 !important; font-weight: 700 !important; }
  `;
  document.head.appendChild(styleTag);
}

// Highlight Claims on Active Webpage
function highlightClaimsOnPage(claims) {
  if (!claims || !claims.length) return 0;
  injectVeriFactStyles();

  let count = 0;
  const treeWalker = document.createTreeWalker(
    document.body,
    NodeFilter.SHOW_TEXT,
    {
      acceptNode: (node) => {
        // Skip script, style, input, and existing verifact highlights
        const parent = node.parentElement;
        if (!parent) return NodeFilter.FILTER_REJECT;
        const tag = parent.tagName.toLowerCase();
        if (tag === 'script' || tag === 'style' || tag === 'textarea' || tag === 'input' || tag === 'noscript') {
          return NodeFilter.FILTER_REJECT;
        }
        if (parent.classList.contains('verifact-highlight') || parent.closest('.verifact-tooltip')) {
          return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    }
  );

  const textNodes = [];
  while (treeWalker.nextNode()) {
    textNodes.push(treeWalker.currentNode);
  }

  claims.forEach((item) => {
    const searchStr = (item.claimText || '').trim();
    if (searchStr.length < 5) return;

    const verdict = (item.verdict || 'misleading').toLowerCase();
    const confidence = item.confidence || 90;
    const sources = item.sources ? item.sources.join(', ') : 'VeriFact AI Grounded Database';
    const explanation = item.explanation || 'Analyzed by VeriFact AI Reasoning Engine.';

    let verdictBadge = '🟡 MISLEADING / UNVERIFIED';
    let badgeClass = 'verifact-badge-misleading';

    if (verdict.includes('true')) {
      verdictBadge = `🟢 VERIFIED TRUE (${confidence}%)`;
      badgeClass = 'verifact-badge-true';
    } else if (verdict.includes('false')) {
      verdictBadge = `🔴 FALSE / DEBUNKED (${confidence}%)`;
      badgeClass = 'verifact-badge-false';
    }

    // Search across text nodes
    for (const node of textNodes) {
      if (!node.parentNode || !node.nodeValue) continue;
      const index = node.nodeValue.toLowerCase().indexOf(searchStr.toLowerCase());

      if (index !== -1) {
        const matchingText = node.nodeValue.substr(index, searchStr.length);
        const afterText = node.nodeValue.substr(index + searchStr.length);
        node.nodeValue = node.nodeValue.substr(0, index);

        const highlightSpan = document.createElement('mark');
        highlightSpan.className = `verifact-highlight verifact-verdict-${verdict.includes('true') ? 'true' : verdict.includes('false') ? 'false' : 'misleading'}`;
        highlightSpan.textContent = matchingText;

        // Create WOT Tooltip
        const tooltipDiv = document.createElement('div');
        tooltipDiv.className = 'verifact-tooltip';
        tooltipDiv.innerHTML = `
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:5px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:4px;">
            <span class="${badgeClass}">${verdictBadge}</span>
            <span style="font-size:10px; color:#9ca3af;">VeriFact AI</span>
          </div>
          <div style="margin-bottom:6px; font-weight:400; color:#e5e7eb;">${explanation}</div>
          <div style="font-size:10px; color:#9ca3af; border-top:1px solid rgba(255,255,255,0.06); padding-top:4px;">
            <strong style="color:#00f5d4;">Grounding Sources:</strong> ${sources}
          </div>
        `;

        highlightSpan.appendChild(tooltipDiv);

        const remainderNode = document.createTextNode(afterText);
        node.parentNode.insertBefore(highlightSpan, node.nextSibling);
        node.parentNode.insertBefore(remainderNode, highlightSpan.nextSibling);

        count++;
        break; // Highlight first matching occurrence per claim
      }
    }
  });

  return count;
}

// Chrome Runtime Message Listener
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "GET_PAGE_CONTENT") {
    try {
      const rawText = document.body ? document.body.innerText : "";
      const cleanedText = rawText
        .replace(/\s+/g, ' ')
        .trim()
        .slice(0, 10000);

      sendResponse({
        status: "success",
        url: window.location.href,
        title: document.title,
        text: cleanedText
      });
    } catch (err) {
      sendResponse({
        status: "error",
        message: err.message
      });
    }
  } else if (request.action === "HIGHLIGHT_PAGE_CLAIMS") {
    try {
      const highlightedCount = highlightClaimsOnPage(request.claims || []);
      sendResponse({
        status: "success",
        count: highlightedCount
      });
    } catch (err) {
      sendResponse({
        status: "error",
        message: err.message
      });
    }
  }
  return true;
});
