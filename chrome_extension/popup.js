document.getElementById('openAppBtn').addEventListener('click', () => {
  chrome.tabs.create({ url: chrome.runtime.getURL('app.html#dashboard') });
});

