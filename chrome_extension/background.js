/**
 * Background Service Worker
 * Handles opening full app tab and inter-script messaging
 */

chrome.runtime.onInstalled.addListener(() => {
  console.log('[YT Lead Hunter PRO] Extension installed successfully.');
});

// Listen for action click or message
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'open_full_dashboard') {
    chrome.tabs.create({ url: chrome.runtime.getURL('app.html#dashboard') });
    sendResponse({ status: 'ok' });
  }
  return true;
});

