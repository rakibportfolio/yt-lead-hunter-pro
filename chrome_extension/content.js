// ============================================================
// ZENTIC MEDIA — YOUTUBE IN-PAGE EMAIL EXTRACTOR CONTENT SCRIPT
// Injects a 1-click email extractor directly into YouTube About dialogs
// ============================================================

(function () {
  const BACKEND_URL = "http://localhost:8000/api/extract-single-email";

  function injectEmailExtractor() {
    // Look for YouTube Channel About Dialog or Links section
    const dialog = document.querySelector('tp-yt-paper-dialog, ytd-engagement-panel-section-list-renderer[target-id="engagement-panel-about"], #about-container, ytd-about-channel-renderer');
    
    // Also channel header action area
    const channelHeader = document.querySelector('#header-container, #channel-header, ytd-c4-tabbed-header-renderer #buttons');

    const targetContainer = dialog || channelHeader;
    if (!targetContainer) return;

    if (document.getElementById("zentic-email-extractor-container")) return;

    // Create Extractor Widget
    const widget = document.createElement("div");
    widget.id = "zentic-email-extractor-container";
    widget.style.cssText = `
      margin: 12px 0;
      padding: 12px 14px;
      background: #111827;
      border: 1.5px solid #dc2626;
      border-radius: 8px;
      color: #fff;
      font-family: Roboto, Arial, sans-serif;
      box-shadow: 0 4px 16px rgba(0,0,0,0.5);
      z-index: 9999;
    `;

    widget.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;">
        <button id="zentic-run-extract-btn" style="background:linear-gradient(135deg, #dc2626, #991b1b);color:#fff;border:none;padding:8px 16px;border-radius:6px;font-weight:700;font-size:13px;cursor:pointer;display:flex;align-items:center;gap:6px;box-shadow:0 2px 8px rgba(220,38,38,0.4);transition:all 0.2s;">
          <span>⚡</span> Extract Real Email (Zentic)
        </button>
        <span style="font-size:11px;color:#94a3b8;font-weight:500;">Direct Website & Bio Deep Crawl</span>
      </div>
      <div id="zentic-extract-status" style="display:none;margin-top:10px;font-size:12.5px;color:#cbd5e1;"></div>
      <div id="zentic-extract-results" style="display:none;margin-top:10px;padding-top:10px;border-top:1px solid #334155;"></div>
    `;

    // Insert into modal or channel page
    if (dialog) {
      const moreInfo = dialog.querySelector('#additional-info-container, #links-section, #more-info, #description-container') || dialog;
      moreInfo.prepend(widget);
    } else if (channelHeader) {
      channelHeader.appendChild(widget);
    }

    const btn = widget.querySelector("#zentic-run-extract-btn");
    const statusEl = widget.querySelector("#zentic-extract-status");
    const resultsEl = widget.querySelector("#zentic-extract-results");

    btn.addEventListener("click", async () => {
      btn.disabled = true;
      btn.innerHTML = "⏳ Crawling Websites & Bio...";
      statusEl.style.display = "block";
      statusEl.innerHTML = "🔍 Scanning channel links and crawling official websites...";
      resultsEl.style.display = "none";

      try {
        // Collect links from the open page/dialog
        const links = [];
        document.querySelectorAll('a[href*="q="], a[href^="http"]').forEach(a => {
          let h = a.href || "";
          if (h.includes("q=")) {
            const m = h.match(/q=(https?(?:%3A%2F%2F|:\/\/)[^&]+)/i);
            if (m) h = decodeURIComponent(m[1]);
          }
          if (
            h.startsWith("http") &&
            !h.includes("youtube.com") &&
            !h.includes("google.com") &&
            !h.includes("accounts.") &&
            !h.includes("support.")
          ) {
            if (!links.includes(h)) links.push(h);
          }
        });

        // Current handle
        const handleMatch = window.location.pathname.match(/(@[a-zA-Z0-9_.-]+)/);
        const handle = handleMatch ? handleMatch[1] : "";

        // Description text
        const descEl = document.querySelector("#description-container, #description, ytd-channel-about-metadata-renderer");
        const description = descEl ? descEl.innerText : "";

        const payload = {
          target: handle || window.location.href,
          links: links,
          description: description
        };

        const resp = await fetch(BACKEND_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        const data = await resp.json();
        btn.disabled = false;
        btn.innerHTML = "⚡ Extract Real Email (Zentic)";

        if (data.success && data.all_emails && data.all_emails.length > 0) {
          statusEl.style.display = "none";
          resultsEl.style.display = "block";
          resultsEl.innerHTML = `
            <div style="background:rgba(16,185,129,0.12);border:1px solid #059669;padding:10px;border-radius:6px;">
              <div style="font-size:12px;color:#34d399;font-weight:700;margin-bottom:6px;">
                🎉 ${data.all_emails.length} Verified Email${data.all_emails.length > 1 ? 's' : ''} Found:
              </div>
              <div style="display:flex;flex-direction:column;gap:6px;">
                ${data.all_emails.map(em => `
                  <div style="display:flex;align-items:center;justify-content:space-between;background:#1e293b;padding:6px 10px;border-radius:4px;gap:8px;">
                    <span style="font-family:monospace;font-size:13px;color:#38bdf8;font-weight:700;">✉️ ${em}</span>
                    <button class="zentic-copy-email-btn" data-email="${em}" style="background:#059669;color:#fff;border:none;padding:4px 10px;border-radius:4px;font-size:11px;font-weight:700;cursor:pointer;">
                      Copy
                    </button>
                  </div>
                `).join('')}
              </div>
            </div>
          `;

          resultsEl.querySelectorAll(".zentic-copy-email-btn").forEach(cBtn => {
            cBtn.addEventListener("click", () => {
              const em = cBtn.dataset.email;
              navigator.clipboard.writeText(em);
              cBtn.textContent = "Copied! ✓";
              cBtn.style.background = "#2563eb";
              setTimeout(() => { cBtn.textContent = "Copy"; cBtn.style.background = "#059669"; }, 2000);
            });
          });
        } else {
          statusEl.style.display = "block";
          statusEl.innerHTML = `⚠️ No public email found in channel description or linked websites (${links.length} websites checked).`;
        }
      } catch (err) {
        btn.disabled = false;
        btn.innerHTML = "⚡ Extract Real Email (Zentic)";
        statusEl.style.display = "block";
        statusEl.innerHTML = `❌ Error connecting to Zentic Backend (Ensure http://localhost:8000 is running).`;
      }
    });
  }

  // Auto-capture revealed email from YouTube's native "View email address" button
  function setupNativeViewEmailAutoCapture() {
    const emailEls = document.querySelectorAll('#email, ytd-channel-about-metadata-renderer #email, a[href^="mailto:"], tp-yt-paper-dialog #email');
    emailEls.forEach(el => {
      const text = el.innerText || el.textContent || (el.href || '').replace('mailto:', '');
      const match = text.match(/[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+/);
      if (match && !el.dataset.zenticCaptured) {
        el.dataset.zenticCaptured = "true";
        const email = match[0].toLowerCase();
        
        // Show auto-captured badge right next to the revealed email
        const badge = document.createElement("span");
        badge.style.cssText = "display:inline-block;margin-left:8px;padding:3px 8px;background:#059669;color:#fff;border-radius:4px;font-size:11px;font-weight:700;";
        badge.textContent = "✓ Auto-Captured & Copied (Zentic)";
        if (el.parentElement) el.parentElement.appendChild(badge);

        // Auto-copy to clipboard
        try {
          navigator.clipboard.writeText(email);
        } catch (e) {}

        // Send to Zentic Backend
        const handleMatch = window.location.pathname.match(/(@[a-zA-Z0-9_.-]+)/);
        fetch(BACKEND_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ target: handleMatch ? handleMatch[1] : window.location.href, description: email })
        }).catch(() => {});
      }
    });
  }

  // Observe DOM changes to catch dialogs dynamically
  const observer = new MutationObserver(() => {
    injectEmailExtractor();
    setupNativeViewEmailAutoCapture();
  });

  observer.observe(document.body, { childList: true, subtree: true });

  // Initial attempt
  setTimeout(() => {
    injectEmailExtractor();
    setupNativeViewEmailAutoCapture();
  }, 1000);
})();
