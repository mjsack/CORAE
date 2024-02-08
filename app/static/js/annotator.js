const videoElement = document.getElementById("videoElement");
const progressBar = document.getElementById("videoProgressBar");
const annotationSlider = document.getElementById("annotationSlider");
const videosDataElement = document.getElementById("videosData");
const videos_data = JSON.parse(videosDataElement.textContent);
let annotations = {};

videos_data.forEach((video) => {
  annotations[video.id] = [];
});

let currentVideoIndex = 0;
let intervalAnnotation = null;
let isPlaying = false;
let intervalAnnotationModeEnabled = false;
let intervalTime = 1000;

let currentVideoId = videos_data[currentVideoIndex].id;
let currentVideoURL = videos_data[currentVideoIndex].url;

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
  annotationSlider.value = 0;
  if (
    !annotations[currentVideoId] ||
    annotations[currentVideoId].length === 0
  ) {
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
  const FRAME_RATE = JSON.parse(
    document.getElementById(`videoFrameRate_${currentVideoId}`).textContent
  );
  const currentFrameNumber = Math.round(currentTimestamp * FRAME_RATE);

  if (!annotations[currentVideoId]) {
    annotations[currentVideoId] = [];
  }

  const annotation = {
    timestamp: currentTimestamp,
    video_frame: currentFrameNumber,
    slider_position: currentValue,
    video_id: currentVideoId,
  };

  // Enhanced duplicate check logic
  const isDuplicate = annotations[currentVideoId].some(
    (ann) => Math.abs(ann.timestamp - annotation.timestamp) < 0.05 // Adjust the threshold as needed
  );

  if (!isDuplicate) {
    annotations[currentVideoId].push(annotation);
  }
}

function updateAnnotationsInput() {
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
  if (currentVideoIndex < videos_data.length - 1) {
    const nextVideoId = videos_data[currentVideoIndex + 1].id;
    annotations[nextVideoId] = annotations[nextVideoId] || [];
    annotations[nextVideoId].push({
      timestamp: 0,
      video_frame: 0,
      slider_position: 0,
      video_id: nextVideoId,
    });
  }
  console.log("Current Video Index:", currentVideoIndex);
  console.log("Annotations:", annotations);
  currentVideoIndex++;

  if (currentVideoIndex < videos_data.length) {
    currentVideoId = videos_data[currentVideoIndex].id;
    currentVideoURL = videos_data[currentVideoIndex].url;
    videoElement.querySelector("source").src = currentVideoURL;
    videoElement.load();
    videoElement.play();
  } else {
    console.log(
      "All videos completed. Sending annotations to server:",
      annotations
    );

    if (currentVideoIndex >= videos_data.length) {
      const csrfToken = document
        .querySelector('meta[name="csrf-token"]')
        .getAttribute("content");
      submitAnnotations(annotations, csrfToken);
    } else {
      console.log(
        "Current video index:",
        currentVideoIndex,
        "is invalid for comparison to video data length:",
        videos_data.length
      );
    }
  }
}

const participantTokenElement = document.getElementById("participantToken");
const participantToken = JSON.parse(participantTokenElement.textContent);

function submitAnnotations(annotationsData, csrfToken) {
  fetch(`/annotator/${participantToken}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify({
      annotations: annotationsData,
      participant_token: participantToken,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        return response.json().then((data) => {
          throw new Error(
            `Server responded with status ${response.status}: ${
              data.error || response.statusText
            }`
          );
        });
      }
      return response.json();
    })
    .then((data) => {
      if (data.message) {
        annotations[currentVideoId].submitted = true;
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

  function periodicSync() {
    if (currentVideoIndex < videos_data.length) {
      submitAnnotations();
    }
  }

  // Call periodicSync function at desired intervals
  setInterval(periodicSync, 300000); // Sync every 5 minutes
}
