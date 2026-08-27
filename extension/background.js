// VeriFact AI - Background Service Worker (Manifest V3)

chrome.runtime.onInstalled.addListener(() => {
  console.log("VeriFact AI Extension installed successfully.");
  
  // Set default storage settings if not present
  chrome.storage.local.get(["backendUrl", "permissionDuration"], (res) => {
    if (!res.backendUrl) {
      chrome.storage.local.set({ backendUrl: "http://localhost:8080/chat" });
    }
    if (!res.permissionDuration) {
      chrome.storage.local.set({ permissionDuration: "15m" });
    }
  });
});
