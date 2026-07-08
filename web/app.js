// Small, dependency-free front end. Talks to the FastAPI backend.

const $ = (sel) => document.querySelector(sel);

const state = {
  mode: "text", // "text" | "audio"
  recorder: null,
  chunks: [],
  audioBlob: null, // the recorded or uploaded audio
  userSetSource: false, // did the user pick a "From" language by hand?
  recognition: null, // live speech preview while recording
};

// --- Setup ------------------------------------------------------------------

async function loadLanguages() {
  const res = await fetch("/api/languages");
  const { languages, targets } = await res.json();

  const target = $("#target-lang");
  const source = $("#source-lang");
  source.innerHTML = '<option value="">Auto-detect</option>';
  for (const lang of languages) source.append(new Option(lang.name, lang.code));
  for (const t of targets || languages) target.append(new Option(t.name, t.code));

  // Default: auto-detect what you say/type, translate to English.
  target.value = "en";
  source.value = ""; // Auto-detect
}

// --- Tabs -------------------------------------------------------------------

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    state.mode = tab.dataset.mode;
    document.querySelectorAll(".pane").forEach((p) => {
      p.classList.toggle("hidden", p.dataset.pane !== state.mode);
    });
    applyModeUI();
  });
});

// In audio mode the language is auto-detected, so hide "From" and show only "To".
function applyModeUI() {
  const audioMode = state.mode === "audio";
  $("#from-control").classList.toggle("hidden", audioMode);
  $("#lang-arrow").classList.toggle("hidden", audioMode);
}

// Track manual "From" picks, so auto-detect stays on until you override it.
$("#source-lang").addEventListener("change", () => {
  state.userSetSource = $("#source-lang").value !== "";
});

// --- Recording --------------------------------------------------------------

// Live words while recording, using the browser's built-in speech recognition
// (instant). The authoritative transcript still comes from the on-device
// Whisper model when you press Translate.
const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;

function startLivePreview() {
  const live = $("#live-transcript");
  if (!SpeechRec) {
    live.classList.add("hidden");
    return;
  }
  try {
    const rec = new SpeechRec();
    rec.lang = navigator.language || "en-US";
    rec.continuous = true;
    rec.interimResults = true;
    rec.onresult = (e) => {
      let text = "";
      for (const r of e.results) text += r[0].transcript;
      live.textContent = text.trim() || "Listening…";
    };
    rec.onerror = () => {};
    state.recognition = rec;
    live.textContent = "Listening…";
    live.classList.remove("hidden");
    rec.start();
  } catch {
    live.classList.add("hidden");
  }
}

function stopLivePreview() {
  if (state.recognition) {
    try {
      state.recognition.stop();
    } catch {}
    state.recognition = null;
  }
}

$("#record-btn").addEventListener("click", async () => {
  const btn = $("#record-btn");
  if (state.recorder && state.recorder.state === "recording") {
    state.recorder.stop();
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    state.chunks = [];
    state.recorder = new MediaRecorder(stream);
    state.recorder.ondataavailable = (e) => state.chunks.push(e.data);
    state.recorder.onstop = () => {
      stream.getTracks().forEach((t) => t.stop());
      stopLivePreview();
      state.audioBlob = new Blob(state.chunks, { type: "audio/webm" });
      const url = URL.createObjectURL(state.audioBlob);
      const preview = $("#input-preview");
      preview.src = url;
      preview.classList.remove("hidden");
      btn.classList.remove("recording");
      btn.textContent = "● Record";
      $("#rec-status").textContent = "Recorded ✓";
    };
    state.recorder.start();
    startLivePreview();
    btn.classList.add("recording");
    btn.textContent = "■ Stop";
    $("#rec-status").textContent = "Recording…";
  } catch (err) {
    showError("Microphone access denied or unavailable.");
  }
});

$("#file-input").addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (!file) return;
  state.audioBlob = file;
  const preview = $("#input-preview");
  preview.src = URL.createObjectURL(file);
  preview.classList.remove("hidden");
  $("#rec-status").textContent = file.name;
});

// --- Translate --------------------------------------------------------------

$("#go-btn").addEventListener("click", translate);

async function translate() {
  hideError();
  const targetLang = $("#target-lang").value;
  // Text mode respects a manual "From"; audio always auto-detects.
  const sourceLang =
    state.mode === "text" && state.userSetSource ? $("#source-lang").value : "";
  const speak = $("#speak-toggle").checked;
  const btn = $("#go-btn");

  let request;
  if (state.mode === "text") {
    const text = $("#text-input").value.trim();
    if (!text) return showError("Type some text first.");
    request = fetch("/api/translate/text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        target_lang: targetLang,
        source_lang: sourceLang || null,
        speak,
      }),
    });
  } else {
    if (!state.audioBlob) return showError("Record or upload audio first.");
    const form = new FormData();
    form.append("file", state.audioBlob, "audio.webm");
    form.append("target_lang", targetLang);
    if (sourceLang) form.append("source_lang", sourceLang);
    const hints = $("#hints-input").value.trim();
    if (hints) form.append("hints", hints);
    form.append("speak", speak);
    request = fetch("/api/translate/audio", { method: "POST", body: form });
  }

  btn.disabled = true;
  btn.textContent = "Working…";
  try {
    const res = await request;
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Request failed (${res.status})`);
    }
    showResult(await res.json());
  } catch (err) {
    showError(err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Translate";
  }
}

// --- Rendering --------------------------------------------------------------

function langName(code) {
  const opt = $("#target-lang").querySelector(`option[value="${code}"]`);
  return opt ? opt.textContent : code;
}

function showResult(data) {
  $("#source-text").textContent = data.source_text || "—";

  const detected = $("#detected");
  if (data.source_lang) {
    let label = `Detected: ${langName(data.source_lang)}`;
    if (data.source_lang_confidence != null) {
      label += ` (${Math.round(data.source_lang_confidence * 100)}%)`;
    }
    detected.textContent = label;
    detected.classList.remove("hidden");
  } else {
    detected.classList.add("hidden");
  }

  // Reflect the detected language in the "From" selector. A programmatic value
  // change does not fire "change", so auto-detect stays on for the next run.
  if (data.source_lang) {
    $("#source-lang").value = data.source_lang;
  }

  $("#target-title").textContent = `Translation — ${langName(data.target_lang)}`;
  $("#target-text").textContent = data.target_text || "—";

  const audio = $("#result-audio");
  if (data.audio) {
    audio.src = data.audio;
    audio.classList.remove("hidden");
    audio.play().catch(() => {});
  } else {
    audio.classList.add("hidden");
  }

  const notes = $("#notes");
  if (data.notes && data.notes.length) {
    notes.textContent = data.notes.join(" ");
    notes.classList.remove("hidden");
  } else {
    notes.classList.add("hidden");
  }

  $("#result").classList.remove("hidden");
}

function showError(msg) {
  const el = $("#error");
  el.textContent = msg;
  el.classList.remove("hidden");
}

function hideError() {
  $("#error").classList.add("hidden");
}

loadLanguages().catch(() => showError("Could not reach the server."));
applyModeUI();

// --- Model warmup status ----------------------------------------------------

// Poll until the models finish loading; keep Translate disabled until then, so
// the first click is fast instead of waiting ~30s for models to load.
async function pollReady() {
  const banner = $("#warmup");
  const go = $("#go-btn");
  try {
    const h = await (await fetch("/api/health")).json();
    if (h.error) {
      banner.textContent = "⚠ Model load failed: " + h.error;
      banner.classList.remove("hidden");
      banner.classList.add("error");
      return;
    }
    if (h.ready) {
      banner.classList.add("hidden");
      go.disabled = false;
      return;
    }
    banner.textContent = "⏳ Warming up models — " + (h.progress || "loading") +
      " (first start only)";
    banner.classList.remove("hidden");
    go.disabled = true;
    setTimeout(pollReady, 1500);
  } catch {
    setTimeout(pollReady, 2000);
  }
}
pollReady();
