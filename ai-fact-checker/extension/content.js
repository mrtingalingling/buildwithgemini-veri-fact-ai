// VeriFact AI - Chrome Extension Content Script
// Extracts text and metadata from active webpage when requested by the extension popup.

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "GET_PAGE_CONTENT") {
    try {
      // Extract page body text up to 10,000 characters to keep payload responsive
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
  }
  return true; // Keep message channel open for async response
});
