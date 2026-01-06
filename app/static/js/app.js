// Prefer same-origin API; allow override via window.API_BASE; fall back to localhost during file:// opens.
const API_BASE = (() => {
  if (typeof window === "undefined") return "";
  if (window.API_BASE) return window.API_BASE;
  if (window.location.host) return `${window.location.protocol}//${window.location.host}`;
  // file:// case or no host — fall back to common dev port
  return "http://localhost:8000";
})();

const descriptionEl = document.getElementById("description");
const companyEl = document.getElementById("company");
const locationEl = document.getElementById("location");
const salaryEl = document.getElementById("salary");
const charCounter = document.getElementById("char-counter");
const resultCard = document.getElementById("result-card");
const resultLabel = document.getElementById("result-label");
const confidenceEl = document.getElementById("confidence");
const processingEl = document.getElementById("processing");
const timestampEl = document.getElementById("timestamp");
const warningEl = document.getElementById("warning");
const loadingEl = document.getElementById("loading");
const errorEl = document.getElementById("error");
const flagForm = document.getElementById("flag-form");
const flagStatus = document.getElementById("flag-status");

function setLoading(on) { loadingEl.hidden = !on; }
function setError(msg) {
  if (!msg) { errorEl.hidden = true; errorEl.textContent = ""; return; }
  errorEl.hidden = false; errorEl.textContent = msg;
}

function updateCounter() {
  const len = (descriptionEl.value || "").length;
  charCounter.textContent = `${len} characters`;
}

document.getElementById("clear-btn").addEventListener("click", () => {
  descriptionEl.value = "";
  companyEl.value = ""; locationEl.value = ""; salaryEl.value = "";
  resultCard.hidden = true; setError(""); updateCounter();
});

document.getElementById("example-btn").addEventListener("click", () => {
  descriptionEl.value = "We are seeking a data analyst to interpret complex datasets, build dashboards, and collaborate with stakeholders. Competitive salary, benefits, and growth opportunities.";
  updateCounter();
});

descriptionEl.addEventListener("input", updateCounter);
updateCounter();

async function predict() {
  const description = descriptionEl.value.trim();
  if (description.length < 10) { setError("Please enter at least 10 characters."); return; }
  setError(""); setLoading(true);
  try {
    const res = await fetch(`${API_BASE}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description, company: companyEl.value, location: locationEl.value, salary: salaryEl.value })
    });
    if (!res.ok) { throw new Error(`Request failed: ${res.status}`); }
    const data = await res.json();
    resultCard.hidden = false;
    const isFake = data.result.toLowerCase() === "fake";
    resultLabel.textContent = data.result;
    resultLabel.classList.remove("real","fake");
    resultLabel.classList.add(isFake ? "fake" : "real");
    confidenceEl.textContent = `Confidence: ${data.confidence_percent}%`;
    processingEl.textContent = `Processing time: ${data.processing_time_ms} ms`;
    timestampEl.textContent = `Timestamp: ${data.timestamp}`;
    warningEl.hidden = !(data.confidence_percent < 60);
  } catch (e) {
    setError(e.message);
  } finally { setLoading(false); }
}

document.getElementById("predict-form").addEventListener("submit", (ev) => { ev.preventDefault(); predict(); });

flagForm.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const description = descriptionEl.value.trim();
  const reason = document.getElementById("reason").value;
  const comments = document.getElementById("comments").value;
  const user_email = document.getElementById("email").value;
  if (description.length < 10) { setError("Please enter at least 10 characters."); return; }
  setError(""); setLoading(true); flagStatus.hidden = true;
  try {
    const res = await fetch(`${API_BASE}/feedback/flag`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description, reason, comments, user_email })
    });
    if (!res.ok) { throw new Error(`Flag failed: ${res.status}`); }
    const data = await res.json();
    flagStatus.hidden = false;
    flagStatus.textContent = `Flag saved (id=${data.id}) at ${data.timestamp}`;
  } catch (e) {
    setError(e.message);
  } finally { setLoading(false); }
});
