let current = null;
let locked = false;

const img = document.getElementById("champImg");
const finishBtn = document.getElementById("finishBtn");
const progressBadge = document.getElementById("progressBadge");

const finishPopup = document.getElementById("finishPopup");
const closeFinish = document.getElementById("closeFinish");

const confirmFinish = document.getElementById("confirmFinish");
const stepConfirm = document.getElementById("finishStepConfirm");
const stepResult = document.getElementById("finishStepResult");
const resultText = document.getElementById("resultText");

const buttons = [
  document.getElementById("a1"),
  document.getElementById("a2"),
  document.getElementById("a3"),
];

function getLabel(btn) {
  const t = btn.querySelector(".text");
  return (t ? t.textContent : btn.textContent).trim();
}

function setLabel(btn, value) {
  const t = btn.querySelector(".text");
  if (t) t.textContent = value;
  else btn.textContent = value;
}

function resetUI() {
  buttons.forEach(b => {
    b.classList.remove("correct", "wrong");
    b.disabled = false;
  });
  locked = false;
}

function setProgress(data) {
  if (!progressBadge) return;
  progressBadge.textContent = `${data.i}/${data.total}`;
}

async function showResultInPopup() {
  const res = await fetch("/api/result");
  const data = await res.json();

  if (resultText) resultText.textContent = `${data.score} / ${data.total}`;

  if (stepConfirm) stepConfirm.hidden = true;
  if (stepResult) stepResult.hidden = false;
}

function openFinish() {
  if (!finishPopup) return;
  finishPopup.hidden = false;

  if (stepConfirm) stepConfirm.hidden = false;
  if (stepResult) stepResult.hidden = true;
}

function closeFinishPopup() {
  if (finishPopup) finishPopup.hidden = true;
}

async function loadNext() {
  resetUI();

  const res = await fetch("/api/next");
  const data = await res.json();

  // Wenn fertig: bei Competition Popup-Result anzeigen
  if (data.done) {
    if (finishPopup) {
      openFinish();
      await showResultInPopup();
      return;
    }
    window.location.href = "/result";
    return;
  }

  current = data;

  if (data.mode === "competition") setProgress(data);

  // Loading-Overlay AN (auf die champbox)
img.classList.add("loading");

// onload muss VOR src gesetzt werden
img.onload = () => {
  img.classList.remove("loading");
};

// Bild setzen
img.src = data.question.image;

  data.question.options.forEach((opt, idx) => {
    setLabel(buttons[idx], opt);
    buttons[idx].onclick = () => pick(opt);
  });
}

async function pick(picked) {
  if (locked) return;
  locked = true;

  buttons.forEach(b => (b.disabled = true));

  const correct = current.correct;

  // richtig immer grün markieren
  buttons.forEach(b => {
    if (getLabel(b) === correct) b.classList.add("correct");
  });

  // falscher Klick rot markieren
  if (picked !== correct) {
    const clicked = buttons.find(b => getLabel(b) === picked);
    if (clicked) clicked.classList.add("wrong");
  }

  await fetch("/api/answer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ picked, correct })
  });

  setTimeout(loadNext, 650);
}

/* Zoom */
if (img) {
  img.addEventListener("click", (e) => {
    e.stopPropagation();
    img.classList.toggle("zoomed");
  });
  document.addEventListener("click", () => img.classList.remove("zoomed"));
}

/* Finish popup events */
if (finishBtn) finishBtn.addEventListener("click", openFinish);
if (closeFinish) closeFinish.addEventListener("click", closeFinishPopup);

if (finishPopup) {
  finishPopup.addEventListener("click", (e) => {
    if (e.target === finishPopup) closeFinishPopup();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !finishPopup.hidden) closeFinishPopup();
  });
}

if (confirmFinish) {
  confirmFinish.addEventListener("click", async () => {
    await fetch("/api/finish", { method: "POST" });
    await showResultInPopup();
  });
}

loadNext();


