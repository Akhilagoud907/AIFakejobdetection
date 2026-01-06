const API_BASE = (() => {
  if (typeof window === "undefined") return "";
  if (window.API_BASE) return window.API_BASE;
  if (window.location.host) return `${window.location.protocol}//${window.location.host}`;
  return "http://localhost:8000";
})();

// Firebase config provided by user
const firebaseConfig = {
  apiKey: "AIzaSyAYszdBt4wTZvGFxGFLZcxYmcEaOwCLkRQ",
  authDomain: "fake-job-posting.firebaseapp.com",
  projectId: "fake-job-posting",
  storageBucket: "fake-job-posting.firebasestorage.app",
  messagingSenderId: "716013863430",
  appId: "1:716013863430:web:540f577b64c7c72d6af987",
  measurementId: "G-1PKKDYH7KG",
};

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();

const loginCard = document.getElementById("login-card");
const dashboard = document.getElementById("dashboard");
const loginBtn = document.getElementById("login-btn");
const signupBtn = document.getElementById("signup-btn");
const toggleSignupBtn = document.getElementById("toggle-signup-btn");
const toggleLoginBtn = document.getElementById("toggle-login-btn");
const loginForm = document.getElementById("login-form");
const signupForm = document.getElementById("signup-form");
const formTitle = document.getElementById("form-title");
const formSubtitle = document.getElementById("form-subtitle");
const logoutBtn = document.getElementById("logout-btn");
const loginError = document.getElementById("login-error");
const userChip = document.getElementById("user-chip");
const userEmailEl = document.getElementById("user-email");
const refreshBtn = document.getElementById("refresh-btn");
const retrainBtn = document.getElementById("retrain-btn");
const retrainStatusEl = document.createElement("div");
retrainStatusEl.className = "status";
retrainBtn.parentElement?.appendChild(retrainStatusEl);
const versionsSelect = document.createElement("select");
versionsSelect.id = "versions-select";
versionsSelect.className = "secondary";
versionsSelect.style.minWidth = "180px";
const rollbackBtn = document.createElement("button");
rollbackBtn.textContent = "Rollback";
rollbackBtn.className = "secondary";
retrainBtn.parentElement?.appendChild(versionsSelect);
retrainBtn.parentElement?.appendChild(rollbackBtn);
const exportPredBtn = document.getElementById("export-predictions");
const exportFlagsBtn = document.getElementById("export-flags");
const exportReportBtn = document.getElementById("export-report");
const startInput = document.getElementById("start-date");
const endInput = document.getElementById("end-date");
const flagsTableBody = document.querySelector("#flags-table tbody");
const trendCanvas = document.getElementById("chart-trend");
const activityBody = document.querySelector("#activity-table tbody");
const toast = document.getElementById("toast");

let idToken = null;
let distChart = null;
let trendChart = null;
let retrainPoll = null;

// Debug: Log if buttons are found
console.log("Login btn:", loginBtn);
console.log("Signup btn:", signupBtn);
console.log("Toggle signup btn:", toggleSignupBtn);
console.log("Toggle login btn:", toggleLoginBtn);

function showError(msg) {
  loginError.hidden = !msg;
  loginError.textContent = msg || "";
}

function getFriendlyErrorMessage(error) {
  const code = error.code || "";
  const errorMessages = {
    "auth/user-not-found": "No account found with this email. Please sign up for a new account.",
    "auth/wrong-password": "Incorrect password. Please try again.",
    "auth/invalid-email": "Please enter a valid email address.",
    "auth/email-already-in-use": "This email is already registered. Please login instead.",
    "auth/weak-password": "Password is too weak. Please use at least 6 characters.",
    "auth/too-many-requests": "Too many failed attempts. Please try again later.",
    "auth/network-request-failed": "Network error. Please check your internet connection.",
    "auth/invalid-credential": "Invalid email or password. Please check your credentials.",
    "auth/user-disabled": "This account has been disabled. Please contact support."
  };
  return errorMessages[code] || error.message || "An error occurred. Please try again.";
}

function showToast(msg, variant = "info") {
  toast.textContent = msg;
  toast.className = `toast ${variant}`;
  toast.hidden = false;
  setTimeout(() => { toast.hidden = true; }, 2500);
}

async function apiFetch(path, opts = {}) {
  if (!idToken) throw new Error("Not authenticated");
  const headers = opts.headers ? { ...opts.headers } : {};
  headers["Authorization"] = `Bearer ${idToken}`;
  if (opts.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  return res;
}

function renderStats(data) {
  document.getElementById("stat-total").textContent = data.total_predictions;
  document.getElementById("stat-fake").textContent = data.fake_predictions;
  document.getElementById("stat-real").textContent = data.real_predictions;
  document.getElementById("stat-pending").textContent = data.pending_flags;

  const ctx = document.getElementById("chart-distribution");
  const chartData = {
    labels: ["Fake", "Real"],
    datasets: [{
      data: [data.fake_predictions, data.real_predictions],
      backgroundColor: ["#ef4444", "#22c55e"],
    }],
  };
  if (distChart) {
    distChart.data = chartData;
    distChart.update();
  } else if (ctx) {
    distChart = new Chart(ctx, { type: "doughnut", data: chartData, options: { maintainAspectRatio: false, plugins: { legend: { position: "bottom" }}}});
  }
}

function renderFlags(items) {
  flagsTableBody.innerHTML = "";
  items.forEach(item => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${item.id}</td>
      <td>${item.prediction === 1 ? "Fake" : "Real"}</td>
      <td>${item.reason}</td>
      <td><span class="badge status-${item.status || "pending"}">${item.status || "pending"}</span></td>
      <td>${item.confidence}</td>
      <td>${item.timestamp}</td>
      <td class="actions-inline">
        <button data-id="${item.id}" data-status="validated" data-label="1" class="secondary small">Mark Fake</button>
        <button data-id="${item.id}" data-status="validated" data-label="0" class="secondary small">Mark Real</button>
        <button data-id="${item.id}" data-status="dismissed" class="secondary small">Dismiss</button>
      </td>`;
    flagsTableBody.appendChild(tr);
  });
}

function renderActivity(items) {
  activityBody.innerHTML = "";
  items.forEach(it => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${it.id}</td>
      <td>${it.prediction === 1 ? "Fake" : "Real"}</td>
      <td>${Number(it.confidence).toFixed(3)}</td>
      <td>${it.processing_time_ms} ms</td>
      <td>${it.timestamp}</td>
    `;
    activityBody.appendChild(tr);
  });
}

async function loadDashboard() {
  const [metricsRes, flagsRes, versionsRes, statusRes, trendRes, activityRes] = await Promise.all([
    apiFetch("/admin/metrics/summary"),
    apiFetch("/admin/flags?limit=50"),
    apiFetch("/admin/retrain/versions"),
    apiFetch("/admin/retrain/status"),
    apiFetch("/admin/metrics/trend?days=30"),
    apiFetch("/admin/activity?limit=30"),
  ]);
  const metrics = await metricsRes.json();
  const flags = await flagsRes.json();
  const versions = await versionsRes.json();
  const status = await statusRes.json();
  const trend = await trendRes.json();
  const activity = await activityRes.json();
  renderStats(metrics);
  renderFlags(flags.items || []);
  renderVersions(versions.versions || []);
  renderRetrainStatus(status);
  renderTrend(trend.points || []);
  renderActivity(activity.items || []);
}

function renderTrend(points) {
  if (!trendCanvas) return;
  const labels = points.map(p => p.day);
  const total = points.map(p => p.total);
  const fake = points.map(p => p.fake);
  const datasets = [
    { label: "Total", data: total, borderColor: "#38bdf8", tension: 0.25 },
    { label: "Fake", data: fake, borderColor: "#ef4444", tension: 0.25 },
  ];
  if (trendChart) {
    trendChart.data = { labels, datasets };
    trendChart.update();
  } else {
    trendChart = new Chart(trendCanvas, {
      type: "line",
      data: { labels, datasets },
      options: {
        maintainAspectRatio: false,
        plugins: { legend: { position: "bottom" } },
        scales: { y: { beginAtZero: true } },
      },
    });
  }
}

flagsTableBody?.addEventListener("click", async (e) => {
  const btn = e.target.closest("button[data-id]");
  if (!btn) return;
  const id = btn.getAttribute("data-id");
  const status = btn.getAttribute("data-status");
  const validated_label = btn.getAttribute("data-label");
  try {
    await apiFetch(`/admin/flags/${id}/status`, {
      method: "POST",
      body: JSON.stringify({ status, validated_label: validated_label !== null ? Number(validated_label) : undefined }),
    });
    showToast(`Flag ${id} marked ${status}`);
    await loadDashboard();
  } catch (err) {
    showToast(err.message, "error");
  }
});

// Toggle between login and sign up forms
toggleSignupBtn?.addEventListener("click", (e) => {
  e.preventDefault();
  loginForm.hidden = true;
  signupForm.hidden = false;
  formTitle.textContent = "Create Account";
  formSubtitle.textContent = "Sign up to access the dashboard.";
  showError("");
});

toggleLoginBtn?.addEventListener("click", (e) => {
  e.preventDefault();
  loginForm.hidden = false;
  signupForm.hidden = true;
  formTitle.textContent = "Admin Login";
  formSubtitle.textContent = "Enter your credentials to access the dashboard.";
  showError("");
});

loginBtn?.addEventListener("click", async () => {
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;
  showError("");
  if (!email || !password) { showError("Please enter email and password"); return; }
  try {
    await auth.setPersistence(firebase.auth.Auth.Persistence.LOCAL);
    await auth.signInWithEmailAndPassword(email, password);
    showToast("Logged in successfully");
  } catch (err) {
    showError(getFriendlyErrorMessage(err));
  }
});

signupBtn?.addEventListener("click", async () => {
  const email = document.getElementById("signup-email").value.trim();
  const password = document.getElementById("signup-password").value;
  const confirmPassword = document.getElementById("signup-password-confirm").value;
  showError("");
  if (!email || !password) { showError("Please enter email and password"); return; }
  if (password !== confirmPassword) { showError("Passwords do not match"); return; }
  if (password.length < 6) { showError("Password must be at least 6 characters"); return; }
  try {
    await auth.createUserWithEmailAndPassword(email, password);
    showToast("Account created! Logging in...");
    // After creating account, Firebase automatically logs in
  } catch (err) {
    showError(getFriendlyErrorMessage(err));
  }
});

logoutBtn?.addEventListener("click", async () => {
  await auth.signOut();
});

refreshBtn?.addEventListener("click", async () => {
  try {
    await loadDashboard();
    showToast("Refreshed");
  } catch (err) {
    showToast(err.message, "error");
  }
});

retrainBtn?.addEventListener("click", async () => {
  try {
    await apiFetch("/admin/retrain", { method: "POST" });
    showToast("Retrain queued");
    pollRetrain();
  } catch (err) {
    showToast(err.message, "error");
  }
});

rollbackBtn?.addEventListener("click", async () => {
  const version = versionsSelect.value;
  if (!version) { showToast("Select a version", "error"); return; }
  try {
    await apiFetch(`/admin/retrain/rollback?version=${encodeURIComponent(version)}`, { method: "POST" });
    showToast(`Rolled back to ${version}`);
    await loadDashboard();
  } catch (err) {
    showToast(err.message, "error");
  }
});

function renderVersions(list) {
  versionsSelect.innerHTML = "";
  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = "Select version";
  versionsSelect.appendChild(placeholder);
  list.slice().reverse().forEach(v => {
    const opt = document.createElement("option");
    opt.value = v.version;
    opt.textContent = `${v.version} (f1=${(v.metrics?.f1 ?? 0).toFixed(3)})`;
    versionsSelect.appendChild(opt);
  });
}

function renderRetrainStatus(status) {
  if (!status || !status.status) { retrainStatusEl.textContent = ""; return; }
  const text = status.status === "running" ? "Retraining..." : status.status;
  retrainStatusEl.textContent = text;
  retrainStatusEl.className = `status pill ${status.status}`;
}

async function pollRetrain() {
  if (retrainPoll) clearInterval(retrainPoll);
  retrainPoll = setInterval(async () => {
    try {
      const res = await apiFetch("/admin/retrain/status");
      const st = await res.json();
      renderRetrainStatus(st);
      if (st.status && st.status !== "running") {
        clearInterval(retrainPoll);
        await loadDashboard();
      }
    } catch (err) {
      clearInterval(retrainPoll);
    }
  }, 3000);
}

async function downloadCsv(path, filename) {
  try {
    const res = await apiFetch(path);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    showToast(err.message, "error");
  }
}

function buildRangeQuery() {
  const params = [];
  const start = startInput?.value;
  const end = endInput?.value;
  if (start) params.push(`start=${encodeURIComponent(start)}`);
  if (end) params.push(`end=${encodeURIComponent(end)}`);
  return params.length ? `?${params.join("&")}` : "";
}

exportPredBtn?.addEventListener("click", () => downloadCsv(`/admin/export/predictions${buildRangeQuery()}`, "predictions.csv"));
exportFlagsBtn?.addEventListener("click", () => downloadCsv(`/admin/export/flags${buildRangeQuery()}`, "flagged_posts.csv"));
exportReportBtn?.addEventListener("click", () => downloadCsv(`/admin/export/report.pdf`, "admin_report.pdf"));

auth.onAuthStateChanged(async (user) => {
  if (user) {
    idToken = await user.getIdToken();
    userEmailEl.textContent = user.email || "admin";
    userChip.hidden = false;
    loginCard.hidden = true;
    dashboard.hidden = false;
    await loadDashboard();
  } else {
    idToken = null;
    userChip.hidden = true;
    dashboard.hidden = true;
    loginCard.hidden = false;
  }
});
