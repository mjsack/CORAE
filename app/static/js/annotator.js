const videoElement = document.getElementById("videoElement");
const progressBar = document.getElementById("videoProgressBar");
const annotationSlider = document.getElementById("annotationSlider");
const videosDataElement = document.getElementById("videosData");
const videos_data = JSON.parse(videosDataElement.textContent);
let annotations = {};
let currentVideoIndex = 0;
let intervalAnnotation = null;
let isPlaying = false;
let intervalAnnotationModeEnabled = false;
let intervalTime = 1000;

// Update currentVideoId and currentVideoURL
let currentVideoId = videos_data[currentVideoIndex].id;
let currentVideoURL = videos_data[currentVideoIndex].url;

// Event listeners
videoElement.addEventListener("keydown", reemitKeydown);
annotationSlider.addEventListener("keydown", reemitKeydown);
videoElement.addEventListener("timeupdate", updateProgressBar);
document.addEventListener("keydown", handleKey);
document.addEventListener("reemittedKeydown", handleKey);
videoElement.addEventListener("ended", handleVideoEnd);
annotationSlider.addEventListener("input", function () {
  if (isPlaying) {
    recordAnnotation();
  }
});

videoElement.addEventListener("play", function () {
  if (!annotations[currentVideoId]) {
    annotations[currentVideoId] = [];
    const startingAnnotation = {
      timestamp: 0,
      video_frame: 0,
      slider_position: 0,
      video_id: currentVideoId,
    };
    annotations[currentVideoId].push(startingAnnotation);
  }

  isPlaying = true;

  updateSliderAppearance();
  if (intervalAnnotationModeEnabled) {
    intervalAnnotation = setInterval(recordAnnotation, intervalTime);
  }
});

videoElement.addEventListener("pause", function () {
  isPlaying = false;
  updateSliderAppearance();
  if (intervalAnnotation) {
    clearInterval(intervalAnnotation);
    intervalAnnotation = null;
  }
});

function recordAnnotation() {
  const currentTimestamp = videoElement.currentTime;
  const currentValue = annotationSlider.value;

  // Fetch the frame rate for the current video
  const frameRateElement = document.getElementById(
    `videoFrameRate_${currentVideoId}`
  );
  const FRAME_RATE = JSON.parse(frameRateElement.textContent);

  const currentFrameNumber = Math.round(currentTimestamp * FRAME_RATE);

  // Avoid recording annotations with zeroed-out values unless it's the start
  if (
    currentTimestamp === 0 &&
    currentFrameNumber === 0 &&
    annotations[currentVideoId] &&
    annotations[currentVideoId].length > 0
  ) {
    return;
  }

  if (!annotations[currentVideoId]) {
    annotations[currentVideoId] = [];
  }

  const annotation = {
    timestamp: currentTimestamp,
    video_frame: currentFrameNumber,
    slider_position: currentValue,
    video_id: currentVideoId,
  };

  console.log("Recording annotation:", annotation);

  const lastAnnotation = annotations[currentVideoId].length
    ? annotations[currentVideoId][annotations[currentVideoId].length - 1]
    : null;

  if (
    lastAnnotation &&
    lastAnnotation.timestamp === currentTimestamp &&
    lastAnnotation.slider_position === currentValue
  ) {
    return; // Skip adding duplicate annotation
  }

  annotations[currentVideoId].push(annotation);

  const annotationsInput = document.getElementById("annotations");
  annotationsInput.value = JSON.stringify(annotations);
}

function reemitKeydown(event) {
  event.stopPropagation();
  const newEvent = new KeyboardEvent("reemittedKeydown", event);
  document.dispatchEvent(newEvent);
}

function handleKey(event) {
  const focusedElement = document.activeElement;

  if (["INPUT", "TEXTAREA", "SELECT"].includes(focusedElement.tagName)) {
    return;
  }

  switch (event.code) {
    case "Space":
      event.preventDefault();
      togglePlayPause();
      break;
    case "ArrowRight":
    case "ArrowLeft":
      if (!videoElement.paused) {
        event.preventDefault();
        const delta = event.code === "ArrowRight" ? 1 : -1;
        adjustSliderValue(delta);
      }
      break;
  }
}

function adjustSliderValue(delta) {
  let newValue = Number(annotationSlider.value) + delta;
  newValue = Math.max(
    annotationSlider.min,
    Math.min(newValue, annotationSlider.max)
  );
  annotationSlider.value = newValue;
  recordAnnotation();
}

function togglePlayPause() {
  if (videoElement.paused) {
    videoElement.play();
  } else {
    videoElement.pause();
  }
}

function captureCurrentFrame() {
  const canvas = document.createElement("canvas");
  canvas.width = videoElement.videoWidth;
  canvas.height = videoElement.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL("image/jpeg", 0.95); // Convert to JPEG format with 95% quality
}

function updateProgressBar() {
  let percentage = (videoElement.currentTime / videoElement.duration) * 100;
  progressBar.style.width = percentage + "%";
}

function updateSliderAppearance() {
  if (videoElement.paused) {
    videoElement.classList.add("grayscale");
    annotationSlider.classList.add("grayscale");
    annotationSlider.disabled = true;
  } else {
    videoElement.classList.remove("grayscale");
    annotationSlider.classList.remove("grayscale");
    annotationSlider.disabled = false;
  }
}

function handleVideoEnd() {
  console.log("Current Video Index:", currentVideoIndex);
  console.log("Annotations:", annotations);
  currentVideoIndex++;

  const participantTokenElement = document.getElementById("participantToken");
  const participant_token = JSON.parse(participantTokenElement.textContent);
  const videoUrlsElement = document.getElementById("videosData");
  const video_urls = JSON.parse(videoUrlsElement.textContent);
  const csrf_token = document
    .querySelector('meta[name="csrf-token"]')
    .getAttribute("content");
  const videoIds = videos_data.map((video) => video.id);

  if (
    !annotations[videoIds[currentVideoIndex - 1]] ||
    annotations[videoIds[currentVideoIndex - 1]].length === 0
  ) {
    console.error("No annotations found for the current video.");
    alert("Please annotate the video before proceeding.");
    return;
  }

  if (currentVideoIndex < videos_data.length) {
    // Update the currentVideoId and currentVideoURL after checking the valid index
    currentVideoId = videos_data[currentVideoIndex].id;
    currentVideoURL = videos_data[currentVideoIndex].url;

    // Reset annotations for the new video
    if (!annotations[currentVideoId]) {
      annotations[currentVideoId] = [];
    }

    videoElement.querySelector("source").src = currentVideoURL;
    videoElement.load();
    videoElement.play();
  } else {
    console.log("Sending annotations to server:", annotations);
    fetch(`/annotator/${participant_token}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf_token,
      },
      body: JSON.stringify({
        annotations: annotations,
        participant_token: participant_token,
      }),
    })
      .then((response) => {
        if (!response.ok) {
          if (
            response.headers.get("Content-Type").includes("application/json")
          ) {
            return response.json().then((data) => {
              throw new Error(
                `Server responded with status ${response.status}: ${
                  data.error || response.statusText
                }`
              );
            });
          } else {
            return response.text().then((text) => {
              throw new Error(
                `Server responded with status ${response.status}: ${text}`
              );
            });
          }
        }
        return response.json();
      })
      .then((data) => {
        if (data.message) {
          alert(data.message);
          window.location.href = "/";
        } else if (data.error) {
          alert(data.error);
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        alert(`An error occurred: ${error.message}`);
      });
  }
}
