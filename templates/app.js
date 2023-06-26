/* TODO:
1. Refactor all keypress events to "event.key" and integrate "handleKeyDown()" function
2. Integrate config.ini switch for event-based and interval-based data logging
3. Find database solution for data logging
*/

var log = {};

var idInput = document.getElementById("idInput");
var container = document.querySelector(".container");
var platformContainer = document.querySelector(".platform-container");

var submitButton = document.getElementById("submitButton");

var slider = document.getElementById("slider");
var video = document.getElementById("video");
var main = document.getElementById("main");
var progressBar = document.getElementById("progress-bar");
var progress = document.getElementById("progress");

var startLogging;

// Reveal Dashboard on ID Submit
function showContent() {
  if (idInput.value.trim() != null && idInput.value.trim() != "") {
    logID();
    logTime();
    container.classList.add("hide");
    platformContainer.classList.remove("hide");
  } else {
    showContent();
  }
}

// Submit Toggle for ID Logging
function handleInputChange() {
  if (idInput.value.trim() === "") {
    submitButton.disabled = true;
    submitButton.style.filter = "grayscale(1)";
  } else {
    submitButton.disabled = false;
    submitButton.style.filter = "grayscale(0)";
  }
}

function logID() {
  log["ID"] = idInput.value;
  idInput.value = "";
}

function resetID() {
  idInput.value = "";
}

// Download Data Locally (TODO: 3)
function downloadData() {
  let data = new Blob([JSON.stringify(log)], { type: "application/json" });
  let a = window.document.createElement("a");
  a.href = window.URL.createObjectURL(data);
  a.download = "results.json";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

video.addEventListener("play", logTime);
video.addEventListener("pause", (event) => {
  clearInterval(startLogging);
});
video.addEventListener("pause", (event) => {
  slider.disabled = true;
});
video.addEventListener("pause", (event) => {
  video.focus();
});
video.addEventListener("play", (event) => {
  slider.disabled = false;
});
video.addEventListener("play", (event) => {
  slider.focus();
});
video.addEventListener("ended", downloadData);

// Data Logging, Interval-Based (TODO: 2)
/*
function logTime() {
    if (!(video.currentTime.toString() in log)) {
        let hours = Math.floor(video.currentTime / 3600);
        let minutes = Math.floor((video.currentTime - hours) / 60);
        let seconds = Math.floor(((video.currentTime - (hours * 3600)) - (minutes * 60)))
        let frame = Math.floor(video.currentTime * 25);
        log[hours + ":" + minutes + ":" + seconds + ";" + frame] = slider.value;
    }
}
*/

// Data Logging, Event-Based (TODO: 2)
function logTime() {
  let hours = Math.floor(video.currentTime / 3600);
  let minutes = Math.floor((video.currentTime - hours) / 60);
  let seconds = Math.floor(video.currentTime - hours * 3600 - minutes * 60);
  let frame = Math.floor(video.currentTime * 25);
  log[hours + ":" + minutes + ":" + seconds + ";" + frame] = slider.value;
}

// Input Handling
function handleKeyDown(event) {
  if (event.key === "Enter" && !submitButton.disabled) {
    showContent();
  }
}

// Pause Toggle (TODOL: 1)
document.onkeydown = function (e) {
  if (
    (e || window.event).keyCode === 32 &&
    container.classList.contains("hide")
  ) {
    video.paused ? video.play() : video.pause();
    video.paused
      ? (slider.style.filter = "grayscale(1)")
      : (slider.style.filter = "grayscale(0)");
    console.log(slider.value);
  }
};

// Video Progress Bar
video.addEventListener("timeupdate", function () {
  var percentage = (video.currentTime / video.duration) * 100;
  progress.style.width = percentage + "%";
});
