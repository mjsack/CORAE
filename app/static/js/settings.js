const capacityElement = document.getElementById("settings-capacity");
const couplingElement = document.getElementById("settings-coupling");
const orderingElement = document.getElementById("settings-ordering");
const boundingElement = document.getElementById("settings-bounding");
const granularityElement = document.getElementById("settings-granularity");
const ceilingElement = document.getElementById("settings-ceiling");
const floorElement = document.getElementById("settings-floor");

function toggleBoundingFields(isBounded, overwrite = true) {
  const displayValue = isBounded ? "block" : "none";
  granularityElement.parentElement.style.display = displayValue;
  ceilingElement.parentElement.style.display = displayValue;
  floorElement.parentElement.style.display = displayValue;

  if (overwrite) {
    if (!isBounded) {
      granularityElement.value = 2;
      ceilingElement.value = "+";
      floorElement.value = "-";
    } else {
      granularityElement.value = "";
      ceilingElement.value = "";
      floorElement.value = "";
    }
  }
}

boundingElement.addEventListener("change", function () {
  toggleBoundingFields(this.value === "bounded", true);
});

function toggleCapacityFields(isMultiple) {
  const displayValue = isMultiple ? "block" : "none";
  couplingElement.parentElement.style.display = displayValue;
}

function toggleCouplingFields(isCoupled) {
  const displayValue = !isCoupled ? "block" : "none";
  orderingElement.parentElement.style.display = displayValue;
}

couplingElement.addEventListener("change", function () {
  toggleCouplingFields(this.value === "coupled");
});

capacityElement.addEventListener("change", function () {
  toggleCapacityFields(this.value >= 2);
});

const presetDropdown = document.getElementById("preset");
const settingsSection = document.getElementById("section-settings");

toggleBoundingFields(boundingElement.value === "bounded", false);
toggleCapacityFields(capacityElement.value >= 2);
toggleCouplingFields(couplingElement.value === "coupled");

function populatePresetSettings(presetId) {
  fetch(`/api/presets/${presetId}/settings`)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      for (const [key, value] of Object.entries(data)) {
        const inputField = document.getElementById(`settings-${key}`);
        if (inputField) {
          inputField.value = value;
        }
      }
    })
    .catch((error) => {
      console.error("Error fetching preset settings:", error);
    });
}

if (presetDropdown) {
  presetDropdown.addEventListener("change", function () {
    if (this.value !== "new" && settingsSection) {
      populatePresetSettings(this.value);
      settingsSection.style.display = "none";
    } else if (settingsSection) {
      settingsSection.style.display = "block";
    }
  });
}

if (settingsSection && !presetDropdown) {
  settingsSection.style.display = "block";
  const presetId = settingsSection.dataset.presetId;
  if (presetId) {
    populatePresetSettings(presetId);
  }
}
