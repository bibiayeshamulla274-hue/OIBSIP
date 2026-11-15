/* ==========================================================================
   BMI Studio — Vanilla JavaScript (Works via file:// without a server)
   Includes Live BMI Simulator + Presets, Category Explorer, m/cm Toggle,
   Healthy Weight Corridor, Goal BMI Line, Multi-User LocalStorage & CSV Export.
   ========================================================================== */

(function () {
  "use strict";

  var STORAGE_KEY = "oibsip_bmi_calculator_records_v1";
  var SEEDED_KEY = "oibsip_bmi_calculator_seeded_v1";
  var MIN_WEIGHT_KG = 10;
  var MAX_WEIGHT_KG = 300;
  var MIN_HEIGHT_M = 0.5;
  var MAX_HEIGHT_M = 2.5;

  var SAMPLE_RECORDS = [
    { id: 1001, username: "Ayesha", weight: 73.5, height: 1.66, bmi: 26.67, category: "Overweight", date_time: "2026-09-02 09:15:00" },
    { id: 1002, username: "Ayesha", weight: 71.2, height: 1.66, bmi: 25.84, category: "Overweight", date_time: "2026-09-18 09:20:00" },
    { id: 1003, username: "Ayesha", weight: 68.4, height: 1.66, bmi: 24.82, category: "Normal", date_time: "2026-10-05 08:50:00" },
    { id: 1004, username: "Ayesha", weight: 65.8, height: 1.66, bmi: 23.88, category: "Normal", date_time: "2026-10-22 09:05:00" },
    { id: 1005, username: "Ayesha", weight: 63.2, height: 1.66, bmi: 22.93, category: "Normal", date_time: "2026-11-10 09:10:00" },
    { id: 1006, username: "Rahul", weight: 51.0, height: 1.72, bmi: 17.24, category: "Underweight", date_time: "2026-09-10 18:30:00" },
    { id: 1007, username: "Rahul", weight: 53.5, height: 1.72, bmi: 18.08, category: "Underweight", date_time: "2026-10-01 18:45:00" },
    { id: 1008, username: "Rahul", weight: 56.4, height: 1.72, bmi: 19.06, category: "Normal", date_time: "2026-10-20 19:00:00" },
    { id: 1009, username: "Rahul", weight: 58.8, height: 1.72, bmi: 19.88, category: "Normal", date_time: "2026-11-08 18:40:00" },
    { id: 1010, username: "Priya", weight: 88.0, height: 1.64, bmi: 32.72, category: "Obese", date_time: "2026-09-14 07:30:00" },
    { id: 1011, username: "Priya", weight: 84.5, height: 1.64, bmi: 31.42, category: "Obese", date_time: "2026-10-04 07:45:00" },
    { id: 1012, username: "Priya", weight: 79.8, height: 1.64, bmi: 29.67, category: "Overweight", date_time: "2026-10-28 07:40:00" },
    { id: 1013, username: "Priya", weight: 76.5, height: 1.64, bmi: 28.44, category: "Overweight", date_time: "2026-11-12 07:50:00" }
  ];

  var CATEGORY_INFO = {
    Underweight: {
      cardClass: "result-underweight",
      textClass: "cat-blue",
      colorHex: "#2563eb",
      range: "< 18.5",
      sampleW: 48.0,
      sampleH: 1.70,
      tip: "Underweight (<18.5): Focus on nutrient-dense meals and strength training to enter the 18.5–24.9 corridor.",
    },
    Normal: {
      cardClass: "result-normal",
      textClass: "cat-green",
      colorHex: "#16a34a",
      range: "18.5 – 24.9",
      sampleW: 63.7,
      sampleH: 1.70,
      tip: "Normal (18.5–24.9): Balanced weight for height. Maintain steady nutrition, hydration, and regular activity.",
    },
    Overweight: {
      cardClass: "result-overweight",
      textClass: "cat-orange",
      colorHex: "#ea580c",
      range: "25.0 – 29.9",
      sampleW: 79.0,
      sampleH: 1.70,
      tip: "Overweight (25.0–29.9): Moderate cardio and a gentle calorie deficit can guide weight back toward the Normal corridor.",
    },
    Obese: {
      cardClass: "result-obese",
      textClass: "cat-red",
      colorHex: "#dc2626",
      range: ">= 30.0",
      sampleW: 96.0,
      sampleH: 1.70,
      tip: "Obese (>=30.0): Consider consulting a healthcare professional for a sustainable, gradual wellness plan.",
    },
  };

  // Simulator DOM References
  var simWeightSlider = document.getElementById("simWeightSlider");
  var simHeightSlider = document.getElementById("simHeightSlider");
  var simWeightVal = document.getElementById("simWeightVal");
  var simHeightVal = document.getElementById("simHeightVal");
  var simBmiValue = document.getElementById("simBmiValue");
  var simReadoutTag = document.getElementById("simReadoutTag");
  var simCategoryLabel = document.getElementById("simCategoryLabel");
  var simCorridorLabel = document.getElementById("simCorridorLabel");
  var simDisplayCard = document.getElementById("simDisplayCard");
  var simGaugeMarker = document.getElementById("simGaugeMarker");
  var applySimulatorBtn = document.getElementById("applySimulatorBtn");
  var presetButtons = document.querySelectorAll(".preset-btn");

  // Tracker DOM References
  var bmiForm = document.getElementById("bmiForm");
  var usernameInput = document.getElementById("usernameInput");
  var weightInput = document.getElementById("weightInput");
  var heightInput = document.getElementById("heightInput");
  var heightInputLabel = document.getElementById("heightInputLabel");
  var unitLabelTag = document.getElementById("unitLabelTag");
  var unitMeterBtn = document.getElementById("unitMeterBtn");
  var unitCmBtn = document.getElementById("unitCmBtn");
  var goalBmiInput = document.getElementById("goalBmiInput");
  var clearBtn = document.getElementById("clearBtn");
  var focusInputBtn = document.getElementById("focusInputBtn");

  var formErrorEl = document.getElementById("formError");
  var storageErrorBanner = document.getElementById("storageErrorBanner");

  var resultCard = document.getElementById("resultCard");
  var resultMeta = document.getElementById("resultMeta");
  var resultBmi = document.getElementById("resultBmi");
  var resultCategory = document.getElementById("resultCategory");
  var resultGuidance = document.getElementById("resultGuidance");

  var categoryCards = document.querySelectorAll(".cat-card");
  var categoryTipBox = document.getElementById("categoryTipBox");

  var userSelect = document.getElementById("userSelect");
  var selectedUserSummary = document.getElementById("selectedUserSummary");
  var loadSampleBtn = document.getElementById("loadSampleBtn");
  var exportCsvBtn = document.getElementById("exportCsvBtn");
  var deleteRecordsBtn = document.getElementById("deleteRecordsBtn");

  var statLatestBmi = document.getElementById("statLatestBmi");
  var statDeltaBmi = document.getElementById("statDeltaBmi");
  var statAvgBmi = document.getElementById("statAvgBmi");

  var historyCountEl = document.getElementById("historyCount");
  var historyTableBody = document.getElementById("historyTableBody");

  var chartCanvas = document.getElementById("bmiChart");
  var chartFallback = document.getElementById("chartFallback");

  var bmiChartInstance = null;
  var selectedUsername = "";
  var heightUnit = "m";

  /* ------------------------------------------------------------------------
     Safe localStorage Read / Write Helpers (wrapped in try/catch)
     ------------------------------------------------------------------------ */
  function readAllRecords() {
    try {
      var raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return [];
      }
      var parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (err) {
      showStorageError("Unable to read saved BMI records from localStorage: " + err.message);
      return [];
    }
  }

  function writeAllRecords(records) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
      hideStorageError();
      return true;
    } catch (err) {
      showStorageError("Unable to save BMI record to localStorage: " + err.message);
      return false;
    }
  }

  function showStorageError(message) {
    storageErrorBanner.textContent = message;
    storageErrorBanner.classList.remove("hidden");
  }

  function hideStorageError() {
    storageErrorBanner.textContent = "";
    storageErrorBanner.classList.add("hidden");
  }

  /* ------------------------------------------------------------------------
     BMI Calculation, Category Classification & Healthy Weight Guidance
     ------------------------------------------------------------------------ */
  function classifyBmi(bmi) {
    var catName = "Obese";
    if (bmi < 18.5) {
      catName = "Underweight";
    } else if (bmi < 25.0) {
      catName = "Normal";
    } else if (bmi < 30.0) {
      catName = "Overweight";
    }
    var meta = CATEGORY_INFO[catName];
    return {
      category: catName,
      cardClass: meta.cardClass,
      textClass: meta.textClass,
      colorHex: meta.colorHex,
      range: meta.range,
    };
  }

  function getHealthyWeightGuidance(weight, height) {
    var minKg = Math.round(18.5 * height * height * 10) / 10;
    var maxKg = Math.round(24.9 * height * height * 10) / 10;
    var rangeText =
      "Healthy range for " +
      height.toFixed(2) +
      " m: " +
      minKg.toFixed(1) +
      " – " +
      maxKg.toFixed(1) +
      " kg";

    if (weight < minKg) {
      var gain = (minKg - weight).toFixed(1);
      return rangeText + " · Gain ~" + gain + " kg to enter Normal";
    }
    if (weight > maxKg) {
      var lose = (weight - maxKg).toFixed(1);
      return rangeText + " · Lose ~" + lose + " kg to enter Normal";
    }
    return rangeText + " · Within Normal target";
  }

  function validateInputs(usernameRaw, weightRaw, heightRaw) {
    var username = usernameRaw.trim();
    if (!username) {
      return { error: "Please enter a username before calculating." };
    }

    if (weightRaw.trim() === "" || heightRaw.trim() === "") {
      return { error: "Weight and Height fields cannot be empty." };
    }

    var weight = Number(weightRaw);
    var heightInputVal = Number(heightRaw);

    if (!Number.isFinite(weight) || !Number.isFinite(heightInputVal)) {
      return { error: "Weight and Height must be valid numeric values." };
    }

    if (weight <= 0 || heightInputVal <= 0) {
      return { error: "Weight and Height must be greater than zero." };
    }

    var height = heightUnit === "cm" ? heightInputVal / 100 : heightInputVal;

    if (weight < MIN_WEIGHT_KG || weight > MAX_WEIGHT_KG) {
      return {
        error:
          "Please enter a realistic weight between " +
          MIN_WEIGHT_KG +
          " kg and " +
          MAX_WEIGHT_KG +
          " kg.",
      };
    }

    if (height < MIN_HEIGHT_M || height > MAX_HEIGHT_M) {
      if (heightUnit === "cm") {
        return {
          error:
            "Please enter a realistic height between " +
            MIN_HEIGHT_M * 100 +
            " cm and " +
            MAX_HEIGHT_M * 100 +
            " cm.",
        };
      }
      return {
        error:
          "Please enter a realistic height between " +
          MIN_HEIGHT_M +
          " m and " +
          MAX_HEIGHT_M +
          " m.",
      };
    }

    return {
      username: username,
      weight: weight,
      height: Math.round(height * 10000) / 10000,
      error: null,
    };
  }

  function formatDateTime(dateObj) {
    var pad = function (n) {
      return n < 10 ? "0" + n : String(n);
    };
    return (
      dateObj.getFullYear() +
      "-" +
      pad(dateObj.getMonth() + 1) +
      "-" +
      pad(dateObj.getDate()) +
      " " +
      pad(dateObj.getHours()) +
      ":" +
      pad(dateObj.getMinutes()) +
      ":" +
      pad(dateObj.getSeconds())
    );
  }

  /* ------------------------------------------------------------------------
     Height Unit Toggle (m <-> cm)
     ------------------------------------------------------------------------ */
  function setHeightUnit(nextUnit) {
    if (nextUnit === heightUnit) {
      return;
    }
    var currentVal = Number(heightInput.value);
    heightUnit = nextUnit;

    if (nextUnit === "cm") {
      unitCmBtn.classList.add("active");
      unitMeterBtn.classList.remove("active");
      heightInputLabel.textContent = "Height (cm)";
      unitLabelTag.textContent = "cm";
      heightInput.placeholder = "50 – 250";
      heightInput.step = "1";
      heightInput.min = "50";
      heightInput.max = "250";
      if (heightInput.value.trim() !== "" && Number.isFinite(currentVal) && currentVal <= 3.0) {
        heightInput.value = String(Math.round(currentVal * 100));
      }
    } else {
      unitMeterBtn.classList.add("active");
      unitCmBtn.classList.remove("active");
      heightInputLabel.textContent = "Height (m)";
      unitLabelTag.textContent = "m";
      heightInput.placeholder = "0.5 – 2.5";
      heightInput.step = "0.01";
      heightInput.min = "0.5";
      heightInput.max = "2.5";
      if (heightInput.value.trim() !== "" && Number.isFinite(currentVal) && currentVal > 10) {
        heightInput.value = (currentVal / 100).toFixed(2);
      }
    }
  }

  unitMeterBtn.addEventListener("click", function () {
    setHeightUnit("m");
  });

  unitCmBtn.addEventListener("click", function () {
    setHeightUnit("cm");
  });

  /* ------------------------------------------------------------------------
     Live BMI Spectrum Simulator + Presets
     ------------------------------------------------------------------------ */
  function updateSimulator() {
    var w = Number(simWeightSlider.value);
    var h = Number(simHeightSlider.value);
    var bmi = Math.round((w / (h * h)) * 100) / 100;
    var info = classifyBmi(bmi);

    simWeightVal.textContent = w.toFixed(1) + " kg";
    simHeightVal.textContent = h.toFixed(2) + " m";
    simBmiValue.textContent = bmi.toFixed(2);
    simReadoutTag.textContent = bmi.toFixed(2) + " BMI";
    simCategoryLabel.textContent = info.category + " (" + info.range + ")";
    simDisplayCard.className = "sim-display " + info.cardClass;
    simCorridorLabel.textContent = getHealthyWeightGuidance(w, h);

    var clamped = Math.max(12, Math.min(42, bmi));
    var pct = ((clamped - 12) / (42 - 12)) * 100;
    simGaugeMarker.style.left = pct.toFixed(1) + "%";
  }

  function clearActivePreset() {
    presetButtons.forEach(function (btn) {
      btn.classList.remove("active");
    });
  }

  simWeightSlider.addEventListener("input", function () {
    clearActivePreset();
    updateSimulator();
  });

  simHeightSlider.addEventListener("input", function () {
    clearActivePreset();
    updateSimulator();
  });

  presetButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      clearActivePreset();
      btn.classList.add("active");
      simWeightSlider.value = btn.getAttribute("data-w");
      simHeightSlider.value = btn.getAttribute("data-h");
      updateSimulator();
    });
  });

  applySimulatorBtn.addEventListener("click", function () {
    var w = Number(simWeightSlider.value);
    var h = Number(simHeightSlider.value);
    weightInput.value = w.toFixed(1);
    heightInput.value = heightUnit === "cm" ? String(Math.round(h * 100)) : h.toFixed(2);
    usernameInput.focus();
    document.getElementById("tracker-section").scrollIntoView({ behavior: "smooth" });
  });

  /* ------------------------------------------------------------------------
     Interactive Clickable Category Reference Cards
     ------------------------------------------------------------------------ */
  categoryCards.forEach(function (card) {
    card.addEventListener("click", function () {
      var cat = card.getAttribute("data-cat");
      var meta = CATEGORY_INFO[cat];
      if (!meta) {
        return;
      }
      categoryTipBox.textContent = meta.tip;
      clearActivePreset();
      simWeightSlider.value = String(meta.sampleW);
      simHeightSlider.value = String(meta.sampleH);
      updateSimulator();
    });
  });

  /* ------------------------------------------------------------------------
     UI Rendering: Result Card, Stats Strip, Dropdown, History & Chart
     ------------------------------------------------------------------------ */
  function showFormError(msg) {
    formErrorEl.textContent = msg;
    formErrorEl.classList.remove("hidden");
  }

  function clearFormError() {
    formErrorEl.textContent = "";
    formErrorEl.classList.add("hidden");
  }

  function updateResultCard(username, bmi, info, guidance) {
    resultCard.className = "result-card " + info.cardClass;
    resultMeta.textContent = "Result for " + username;
    resultBmi.textContent = bmi.toFixed(2);
    resultCategory.textContent = "Category: " + info.category + " (" + info.range + ")";
    resultGuidance.textContent = guidance;
  }

  function resetResultCard() {
    resultCard.className = "result-card result-neutral";
    resultMeta.textContent = "Ready for calculation";
    resultBmi.textContent = "--";
    resultCategory.textContent = "Enter username, weight, and height to view your category.";
    resultGuidance.textContent = "Healthy weight corridor and target delta will appear here.";
  }

  function getDistinctUsers(records) {
    var seen = {};
    var users = [];
    records.forEach(function (rec) {
      var key = rec.username.toLowerCase();
      if (!seen[key]) {
        seen[key] = true;
        users.push(rec.username);
      }
    });
    users.sort(function (a, b) {
      return a.toLowerCase().localeCompare(b.toLowerCase());
    });
    return users;
  }

  function getUserRecords(records, username) {
    if (!username) {
      return [];
    }
    var target = username.toLowerCase();
    return records.filter(function (rec) {
      return rec.username.toLowerCase() === target;
    });
  }

  function syncUserDropdown(records) {
    var users = getDistinctUsers(records);
    userSelect.innerHTML = "";

    if (users.length === 0) {
      var emptyOption = document.createElement("option");
      emptyOption.value = "";
      emptyOption.textContent = "No saved users";
      userSelect.appendChild(emptyOption);
      selectedUsername = "";
      deleteRecordsBtn.disabled = true;
      exportCsvBtn.disabled = true;
      return;
    }

    users.forEach(function (user) {
      var opt = document.createElement("option");
      opt.value = user;
      opt.textContent = user;
      userSelect.appendChild(opt);
    });

    var match = users.find(function (u) {
      return u.toLowerCase() === selectedUsername.toLowerCase();
    });
    selectedUsername = match || users[0];
    userSelect.value = selectedUsername;
    deleteRecordsBtn.disabled = false;
    exportCsvBtn.disabled = false;
  }

  function renderUserStats(userRecords) {
    if (userRecords.length === 0) {
      statLatestBmi.textContent = "--";
      statDeltaBmi.textContent = "--";
      statAvgBmi.textContent = "--";
      return;
    }

    var latest = userRecords[userRecords.length - 1].bmi;
    var first = userRecords[0].bmi;
    var delta = Math.round((latest - first) * 100) / 100;
    var sum = userRecords.reduce(function (acc, rec) {
      return acc + Number(rec.bmi);
    }, 0);
    var avg = sum / userRecords.length;

    statLatestBmi.textContent = Number(latest).toFixed(2);
    if (userRecords.length === 1) {
      statDeltaBmi.textContent = "0.00";
    } else {
      statDeltaBmi.textContent = (delta > 0 ? "+" : "") + delta.toFixed(2);
    }
    statAvgBmi.textContent = avg.toFixed(2);
  }

  function renderHistoryTable(userRecords) {
    historyTableBody.innerHTML = "";
    historyCountEl.textContent =
      userRecords.length + (userRecords.length === 1 ? " record" : " records");

    if (userRecords.length === 0) {
      var emptyRow = document.createElement("tr");
      var emptyCell = document.createElement("td");
      emptyCell.colSpan = 5;
      emptyCell.className = "empty-cell";
      emptyCell.textContent = selectedUsername
        ? "No records found for " + selectedUsername + "."
        : "No records yet. Calculate a BMI entry to start tracking.";
      emptyRow.appendChild(emptyCell);
      historyTableBody.appendChild(emptyRow);
      return;
    }

    var reversed = userRecords.slice().reverse();
    reversed.forEach(function (rec) {
      var row = document.createElement("tr");
      var info = classifyBmi(rec.bmi);

      var dtCell = document.createElement("td");
      dtCell.className = "tabular-nums";
      dtCell.textContent = rec.date_time;

      var weightCell = document.createElement("td");
      weightCell.className = "num-col tabular-nums";
      weightCell.textContent = Number(rec.weight).toFixed(1);

      var heightCell = document.createElement("td");
      heightCell.className = "num-col tabular-nums";
      heightCell.textContent = Number(rec.height).toFixed(2);

      var bmiCell = document.createElement("td");
      bmiCell.className = "num-col tabular-nums " + info.textClass;
      bmiCell.style.fontWeight = "700";
      bmiCell.textContent = Number(rec.bmi).toFixed(2);

      var catCell = document.createElement("td");
      catCell.className = info.textClass;
      catCell.style.fontWeight = "700";
      catCell.textContent = rec.category;

      row.appendChild(dtCell);
      row.appendChild(weightCell);
      row.appendChild(heightCell);
      row.appendChild(bmiCell);
      row.appendChild(catCell);
      historyTableBody.appendChild(row);
    });
  }

  function showChartFallback(message) {
    chartCanvas.classList.add("hidden");
    chartFallback.textContent = message;
    chartFallback.classList.remove("hidden");
  }

  function hideChartFallback() {
    chartFallback.classList.add("hidden");
    chartCanvas.classList.remove("hidden");
  }

  function renderChart(userRecords) {
    if (bmiChartInstance) {
      bmiChartInstance.destroy();
      bmiChartInstance = null;
    }

    if (typeof window.Chart === "undefined") {
      showChartFallback(
        "Chart library could not load (you appear to be offline or CDN is unreachable). Your BMI calculations, healthy weight guidance, and CSV export still work normally."
      );
      return;
    }

    if (userRecords.length === 0) {
      showChartFallback(
        "Calculate and save at least one BMI entry to view the trend line chart."
      );
      return;
    }

    hideChartFallback();

    var labels = userRecords.map(function (rec) {
      return rec.date_time;
    });
    var dataPoints = userRecords.map(function (rec) {
      return rec.bmi;
    });
    var pointColors = userRecords.map(function (rec) {
      return classifyBmi(rec.bmi).colorHex;
    });

    var datasets = [
      {
        label: "BMI (" + selectedUsername + ")",
        data: dataPoints,
        borderColor: "#0f766e",
        backgroundColor: "rgba(15, 118, 110, 0.12)",
        borderWidth: 2.5,
        pointRadius: 6,
        pointHoverRadius: 8,
        pointBackgroundColor: pointColors,
        pointBorderColor: "#ffffff",
        pointBorderWidth: 2,
        tension: 0.25,
        fill: true,
      },
    ];

    var goalVal = Number(goalBmiInput.value);
    if (Number.isFinite(goalVal) && goalVal >= 15 && goalVal <= 35) {
      datasets.push({
        label: "Goal BMI (" + goalVal.toFixed(1) + ")",
        data: labels.map(function () {
          return goalVal;
        }),
        borderColor: "#16a34a",
        borderDash: [6, 6],
        borderWidth: 1.75,
        pointRadius: 0,
        fill: false,
      });
    }

    var ctx = chartCanvas.getContext("2d");
    bmiChartInstance = new window.Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: datasets,
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: "top",
          },
          title: {
            display: true,
            text: "BMI Progression — " + selectedUsername,
            font: {
              size: 14,
              weight: "bold",
            },
          },
        },
        scales: {
          x: {
            title: {
              display: true,
              text: "Date & Time",
            },
            ticks: {
              maxRotation: 30,
              minRotation: 0,
            },
          },
          y: {
            title: {
              display: true,
              text: "BMI (kg/m²)",
            },
            suggestedMin: 15,
            suggestedMax: 35,
          },
        },
      },
    });
  }

  function refreshDashboard() {
    var allRecords = readAllRecords();
    syncUserDropdown(allRecords);

    if (!selectedUsername) {
      selectedUserSummary.textContent = "No saved users yet";
      renderUserStats([]);
      renderHistoryTable([]);
      renderChart([]);
      return;
    }

    var userRecords = getUserRecords(allRecords, selectedUsername);
    selectedUserSummary.textContent =
      "Viewing " + userRecords.length + " entry(s) for " + selectedUsername;

    renderUserStats(userRecords);
    renderHistoryTable(userRecords);
    renderChart(userRecords);
  }

  /* ------------------------------------------------------------------------
     Event Handlers
     ------------------------------------------------------------------------ */
  bmiForm.addEventListener("submit", function (event) {
    event.preventDefault();
    clearFormError();

    var validation = validateInputs(
      usernameInput.value,
      weightInput.value,
      heightInput.value
    );
    if (validation.error) {
      showFormError(validation.error);
      return;
    }

    var rawBmi = validation.weight / (validation.height * validation.height);
    var bmi = Math.round(rawBmi * 100) / 100;
    var info = classifyBmi(bmi);
    var guidance = getHealthyWeightGuidance(validation.weight, validation.height);

    updateResultCard(validation.username, bmi, info, guidance);

    var allRecords = readAllRecords();
    allRecords.push({
      id: Date.now(),
      username: validation.username,
      weight: validation.weight,
      height: validation.height,
      bmi: bmi,
      category: info.category,
      date_time: formatDateTime(new Date()),
    });

    if (writeAllRecords(allRecords)) {
      selectedUsername = validation.username;
      refreshDashboard();
    }
  });

  clearBtn.addEventListener("click", function () {
    clearFormError();
    usernameInput.value = "";
    weightInput.value = "";
    heightInput.value = "";
    resetResultCard();
    usernameInput.focus();
  });

  focusInputBtn.addEventListener("click", function () {
    usernameInput.focus();
    document.getElementById("tracker-section").scrollIntoView({ behavior: "smooth" });
  });

  goalBmiInput.addEventListener("change", function () {
    refreshDashboard();
  });

  userSelect.addEventListener("change", function () {
    selectedUsername = userSelect.value;
    refreshDashboard();
  });

  exportCsvBtn.addEventListener("click", function () {
    if (!selectedUsername) {
      return;
    }
    var allRecords = readAllRecords();
    var userRecords = getUserRecords(allRecords, selectedUsername);
    if (userRecords.length === 0) {
      return;
    }

    var lines = ["Date & Time,Username,Weight (kg),Height (m),BMI,Category"];
    userRecords.forEach(function (rec) {
      lines.push(
        [
          '"' + rec.date_time + '"',
          '"' + String(rec.username).replace(/"/g, '""') + '"',
          Number(rec.weight).toFixed(1),
          Number(rec.height).toFixed(2),
          Number(rec.bmi).toFixed(2),
          '"' + rec.category + '"',
        ].join(",")
      );
    });

    var blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
    var url = URL.createObjectURL(blob);
    var link = document.createElement("a");
    link.href = url;
    link.download = selectedUsername.toLowerCase().replace(/\s+/g, "_") + "_bmi_history.csv";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  });

  deleteRecordsBtn.addEventListener("click", function () {
    if (!selectedUsername) {
      return;
    }
    var confirmed = window.confirm(
      "Are you sure you want to delete all BMI records for '" + selectedUsername + "'?"
    );
    if (!confirmed) {
      return;
    }

    var allRecords = readAllRecords();
    var targetLower = selectedUsername.toLowerCase();
    var remaining = allRecords.filter(function (rec) {
      return rec.username.toLowerCase() !== targetLower;
    });

    if (writeAllRecords(remaining)) {
      selectedUsername = "";
      refreshDashboard();
    }
  });

  function seedSampleDataIfFirstRun(force) {
    try {
      var existing = readAllRecords();
      var alreadySeeded = window.localStorage.getItem(SEEDED_KEY);
      if (!force && (alreadySeeded || existing.length > 0)) {
        return;
      }
      var cloned = SAMPLE_RECORDS.map(function (rec, idx) {
        return {
          id: force ? Date.now() + idx : rec.id,
          username: rec.username,
          weight: rec.weight,
          height: rec.height,
          bmi: rec.bmi,
          category: rec.category,
          date_time: rec.date_time,
        };
      });
      var merged = force ? existing.concat(cloned) : cloned;
      if (writeAllRecords(merged)) {
        window.localStorage.setItem(SEEDED_KEY, "1");
        if (!selectedUsername) {
          selectedUsername = "Ayesha";
        }
      }
    } catch (err) {
      showStorageError("Unable to initialize sample BMI records: " + err.message);
    }
  }

  loadSampleBtn.addEventListener("click", function () {
    seedSampleDataIfFirstRun(true);
    refreshDashboard();
  });

  // Seed dummy multi-user records on first run, then initialize simulator & dashboard
  seedSampleDataIfFirstRun(false);
  updateSimulator();
  refreshDashboard();
})();
