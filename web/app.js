// Small, dependency-free front end. Talks to the FastAPI backend.

const $ = (sel) => document.querySelector(sel);

const state = {
  mode: "text", // "text" | "audio"
  recorder: null,
  chunks: [],
  audioBlob: null, // the recorded or uploaded audio
};

// --- Setup ------------------------------------------------------------------

async function loadLanguages() {
  const res = await fetch("/api/languages");
  const { languages } = await res.json();

  const target = $("#target-lang");
  const source = $("#source-lang");
  source.innerHTML = '<option value="">Auto-detect</option>';
  for (const lang of languages) {
    target.append(new Option(lang.name, lang.code));
    source.append(new Option(lang.name, lang.code));
  }
  // Sensible defaults for this user: Hindi <-> English.
  target.value = "en";
  source.value = "hi";
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
  });
});

// --- Recording --------------------------------------------------------------

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
  const sourceLang = $("#source-lang").value;
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
