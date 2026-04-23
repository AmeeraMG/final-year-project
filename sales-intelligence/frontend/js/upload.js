// upload.js
// Handles Excel file upload, ML results display, and insights rendering
// ──────────────────────────────────────────────────────────────────────

// const API_BASE = "http://127.0.0.1:5000";

// Track selected files
const selectedFiles = {
  sales   : null,
  stock   : null,
  product : null,
};

// ── Set up drag-and-drop and click handlers for each file zone ────────────────
document.addEventListener("DOMContentLoaded", () => {
  // Require login before anything
  const user = getUserSession();
  if (!user) {
    window.location.href = "login.html";
    return;
  }

  // Show user name in greeting
  const greetEl = document.getElementById("upload-greeting");
  if (greetEl) greetEl.textContent = `Hello, ${user.name} 👋`;

  // Set up each file drop zone
  setupDropZone("sales-zone",   "sales-input",   "sales");
  setupDropZone("stock-zone",   "stock-input",   "stock");
  setupDropZone("product-zone", "product-input", "product");

  // Upload button handler
  const uploadBtn = document.getElementById("upload-btn");
  if (uploadBtn) uploadBtn.addEventListener("click", handleUpload);
});

// ── Set up a file drop zone ────────────────────────────────────────────────────
function setupDropZone(zoneId, inputId, fileKey) {
  const zone  = document.getElementById(zoneId);
  const input = document.getElementById(inputId);

  if (!zone || !input) return;

  // File selected via click
  input.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) handleFileSelect(file, fileKey, zone);
  });

  // Drag and drop
  zone.addEventListener("dragover",  (e) => { e.preventDefault(); zone.classList.add("drag-over"); });
  zone.addEventListener("dragleave", ()  => { zone.classList.remove("drag-over"); });
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file, fileKey, zone);
  });
}

// ── Handle a file selection ────────────────────────────────────────────────────
function handleFileSelect(file, fileKey, zone) {
  // Check .xlsx only
  if (!file.name.endsWith(".xlsx")) {
    showAlert("upload-alert", "error", "Please upload Excel files (.xlsx) only");
    return;
  }

  selectedFiles[fileKey] = file;
  zone.classList.add("file-selected");

  const chosenEl = zone.querySelector(".file-chosen");
  if (chosenEl) chosenEl.textContent = `✓ ${file.name}`;

  clearUploadAlert();
}

// ── Handle the upload button click ────────────────────────────────────────────
async function handleUpload() {
  hideAlert("upload-alert");

  // Check all three files are selected
  if (!selectedFiles.sales || !selectedFiles.stock || !selectedFiles.product) {
    showAlert("upload-alert", "error", "All three files are required: sales.xlsx, stock.xlsx, product.xlsx");
    return;
  }

  // Show loading state
  showLoader();

  // Build FormData with the three files
  const user = getUserSession();
  const formData = new FormData();
  formData.append("sales",   selectedFiles.sales);
  formData.append("stock",   selectedFiles.stock);
  formData.append("product", selectedFiles.product);
  formData.append("phone",   user.phone);

  try {
    const response = await fetch(`${API_BASE}/upload`, {
      method      : "POST",
      credentials : "include",
      body        : formData,
    });

    const data = await response.json();

    if (data.success) {
      hideLoader();
      displayResults(data);
      showAlert("upload-alert", "success", "Files processed successfully! Insights generated below.");
    } else {
      hideLoader();
      showAlert("upload-alert", "error", data.message || "Upload failed. Please try again.");
    }
  } catch (err) {
    hideLoader();
    showAlert("upload-alert", "error", "Cannot connect to server. Make sure the backend is running.");
  }
}

// ── Display ML results in the UI ──────────────────────────────────────────────
function displayResults(data) {
  const section = document.getElementById("results-section");
  if (section) section.classList.add("visible");

  const ml = data.ml_results || {};
  const insights = data.insights || {};

  // Summary stats
  const summary = ml.summary || {};
  setVal("res-sales",    "₹" + formatNum(summary.total_sales || 0));
  setVal("res-units",    summary.units_sold || 0);
  setVal("res-forecast", "₹" + formatNum((ml.forecast || {}).predicted_sales || 0));
  setVal("res-change",   ((ml.forecast || {}).change_pct || 0) + "%");

  // English insights
  const engEl = document.getElementById("insight-english");
  if (engEl) engEl.textContent = insights.english || "No insights generated.";

  // Tamil insights
  const taEl = document.getElementById("insight-tamil");
  if (taEl) taEl.textContent = insights.tamil || "";

  // WhatsApp status
  const wa = data.whatsapp || {};
  const waBadge = document.getElementById("whatsapp-badge");
  if (waBadge) {
    if (wa.overall_success) {
      waBadge.className = "whatsapp-badge";
      waBadge.innerHTML = "✅ Insights sent to your WhatsApp";
    } else {
      waBadge.className = "whatsapp-badge";
      waBadge.style.background = "#fff3e0";
      waBadge.style.color      = "#e65100";
      waBadge.style.borderColor = "#ffcc80";
      waBadge.innerHTML = "⚠️ WhatsApp not configured (check backend)";
    }
  }

  // Render stock alerts table
  renderStockAlerts(ml.stock_alerts || {});

  // Render trends
  renderTrends(ml.trends || []);

  // Scroll to results
  section.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ── Render stock alerts ───────────────────────────────────────────────────────
function renderStockAlerts(stockAlerts) {
  const tbody = document.getElementById("stock-tbody");
  if (!tbody) return;

  tbody.innerHTML = "";

  const critical = stockAlerts.critical || [];
  const low      = stockAlerts.low      || [];
  const all      = [...critical, ...low];

  if (all.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;color:var(--sage);padding:1.5rem;">✅ All stock levels are healthy</td></tr>`;
    return;
  }

  all.slice(0, 8).forEach(item => {
    const riskBadge = item.risk.includes("CRITICAL")
      ? `<span style="color:#c62828;font-weight:700;">🔴 CRITICAL</span>`
      : `<span style="color:#e65100;font-weight:700;">🟡 LOW</span>`;

    tbody.innerHTML += `
      <tr>
        <td>${item.product.charAt(0).toUpperCase() + item.product.slice(1)}</td>
        <td>${item.stock}</td>
        <td>${item.days_left} days</td>
        <td>${riskBadge}</td>
      </tr>`;
  });
}

// ── Render trend list ─────────────────────────────────────────────────────────
function renderTrends(trends) {
  const el = document.getElementById("trends-list");
  if (!el) return;

  if (!trends.length) {
    el.innerHTML = `<p style="color:var(--muted);font-size:0.9rem;">No trend data available.</p>`;
    return;
  }

  el.innerHTML = trends.slice(0, 5).map(t => {
    const color = t.direction.includes("Rising")  ? "var(--sage)" :
                  t.direction.includes("Falling") ? "var(--rust)" : "var(--muted)";
    return `<div style="display:flex;justify-content:space-between;align-items:center;
            padding:10px 0;border-bottom:1px solid var(--cream);">
              <span style="font-weight:500;">${t.product}</span>
              <span style="font-weight:600;color:${color};">${t.direction}</span>
            </div>`;
  }).join("");
}

// ── Loader helpers ────────────────────────────────────────────────────────────
function showLoader() {
  const loader = document.getElementById("upload-loader");
  const btn    = document.getElementById("upload-btn");
  if (loader) loader.classList.add("visible");
  if (btn)    btn.disabled = true;
}

function hideLoader() {
  const loader = document.getElementById("upload-loader");
  const btn    = document.getElementById("upload-btn");
  if (loader) loader.classList.remove("visible");
  if (btn)    btn.disabled = false;
}

function clearUploadAlert() {
  hideAlert("upload-alert");
}

// ── Utility helpers ───────────────────────────────────────────────────────────
function setVal(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function formatNum(num) {
  return Number(num).toLocaleString("en-IN", { maximumFractionDigits: 0 });
}

// ── Load upload history ────────────────────────────────────────────────────────
async function loadHistory() {
  const user = getUserSession();
  if (!user) {
    window.location.href = "login.html";
    return;
  }

  const tbody = document.getElementById("history-tbody");
  const emptyEl = document.getElementById("history-empty");

  try {
    const resp = await fetch(`${API_BASE}/upload-history`, {
      credentials: "include",
    });
    const data = await resp.json();

    if (!data.success) {
      if (emptyEl) emptyEl.style.display = "block";
      return;
    }

    const history = data.history || [];

    if (history.length === 0) {
      if (emptyEl) emptyEl.style.display = "block";
      return;
    }

    if (tbody) {
      tbody.innerHTML = "";
      history.forEach(h => {
        const files = h.files || {};
        const sent  = h.whatsapp_sent
          ? `<span class="badge-sent">✅ Sent</span>`
          : `<span class="badge-failed">❌ Not sent</span>`;

        tbody.innerHTML += `
          <tr>
            <td>${h.upload_date || "—"}</td>
            <td>${files.sales || "—"}</td>
            <td>${files.stock || "—"}</td>
            <td>${files.product || "—"}</td>
            <td>${sent}</td>
          </tr>`;
      });
    }

  } catch (err) {
    if (emptyEl) {
      emptyEl.style.display = "block";
      emptyEl.querySelector("h3").textContent = "Could not load history";
    }
  }
}
