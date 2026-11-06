const el = document.getElementById("screen-hint");
const word = el.querySelector(".word");

export function show(text, force) {
  if (text) word.textContent = text;
  if (force || !el.classList.contains("live")) el.classList.add("open");
}

export function hide() {
  el.classList.remove("open");
}

export function ready() {}

export function reset() {}
