/*
 * CipherForge — Interactive Random Password Generator (Vanilla JS)
 * Double-click index.html directly via file:// with zero build tools or servers.
 * Uses crypto.getRandomValues() exclusively (never Math.random()).
 * Stores all passwords & session history strictly in volatile memory (RAM).
 */

(function () {
  "use strict";

  var UPPERCASE_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  var LOWERCASE_CHARS = "abcdefghijklmnopqrstuvwxyz";
  var NUMBER_CHARS = "0123456789";
  var SYMBOL_CHARS = "!@#$%^&*()-_=+[]{};:,.<>?/\\|~";
  var AMBIGUOUS_PATTERN = /[0Oo1lI]/g;

  // Curated diceware-style word pool for Memorable Passphrase mode
  var WORD_POOL = [
    "amber", "anchor", "atlas", "aurora", "beacon", "birch", "boulder", "breeze",
    "canyon", "cedar", "cipher", "citadel", "cobalt", "compass", "copper", "coral",
    "crescent", "crimson", "crystal", "cypress", "delta", "drift", "eclipse", "ember",
    "emerald", "falcon", "fjord", "flint", "forest", "forge", "frost", "galaxy",
    "glacier", "granite", "harbor", "horizon", "indigo", "island", "jasper", "juniper",
    "kestrel", "lagoon", "lantern", "laurel", "lunar", "magnet", "maple", "marble",
    "meadow", "mercury", "meteor", "mirage", "monarch", "mosaic", "nebula", "nectar",
    "north", "obsidian", "ocean", "olive", "onyx", "orbit", "orchid", "osprey",
    "pebble", "phoenix", "pioneer", "planet", "prism", "quartz", "quiver", "radium",
    "raven", "redwood", "ripple", "river", "saffron", "sapphire", "sequoia", "shadow",
    "sierra", "silver", "solstice", "sparrow", "spruce", "starlight", "summit", "timber",
    "topaz", "torrent", "tundra", "valley", "velvet", "vertex", "voyager", "zephyr"
  ];

  var MIN_LENGTH = 8;
  var MAX_LENGTH = 64;
  var MAX_HISTORY = 5;

  // Volatile in-memory state only (never written to localStorage or disk)
  // Seeded with 3 illustrative dummy entries for immediate interactive preview
  var sessionHistory = [
    "Tr9@xW4#nZ1$pQ6!",
    "Cobalt-Beacon-7",
    "K9#mP2$vL8!q"
  ];
  var isPasswordVisible = true;
  var activeMode = "random"; // "random" | "passphrase"
  var statusTimerId = null;

  var SAMPLE_BENCHMARKS = [
    { scenario: "Legacy 6-Digit PIN", value: "482910" },
    { scenario: "Seasonal Pattern", value: "Summer2024" },
    { scenario: "Standard Web Account", value: "mR7#kP2!vX9q" },
    { scenario: "Memorable Passphrase", value: "Amber-Cobalt-Prism4" },
    { scenario: "High-Entropy API Token", value: "V9$kL2#mP8!xQ4@nR7^w" }
  ];

  // Navigation & Hero elements
  var headerGenerateCta = document.getElementById("header-generate-cta");
  var heroModeLabel = document.getElementById("hero-mode-label");
  var heroPreviewChars = document.getElementById("hero-preview-chars");
  var heroEntropyBits = document.getElementById("hero-entropy-bits");
  var heroCrackTime = document.getElementById("hero-crack-time");

  // Mode tabs & containers
  var tabRandom = document.getElementById("tab-random");
  var tabPassphrase = document.getElementById("tab-passphrase");
  var randomControls = document.getElementById("random-controls");
  var passphraseControls = document.getElementById("passphrase-controls");

  // Random controls
  var lengthSlider = document.getElementById("length-slider");
  var lengthNumber = document.getElementById("length-number");
  var optUpper = document.getElementById("opt-upper");
  var optLower = document.getElementById("opt-lower");
  var optNumbers = document.getElementById("opt-numbers");
  var optSymbols = document.getElementById("opt-symbols");
  var optExcludeAmbiguous = document.getElementById("opt-exclude-ambiguous");
  var customExcludeInput = document.getElementById("custom-exclude-input");
  var presetButtons = document.querySelectorAll(".preset-btn");

  // Passphrase controls
  var wordCountSlider = document.getElementById("word-count-slider");
  var wordCountReadout = document.getElementById("word-count-readout");
  var separatorSelect = document.getElementById("separator-select");
  var optCapitalizeWords = document.getElementById("opt-capitalize-words");
  var optAppendNumber = document.getElementById("opt-append-number");

  // Output & Feedback
  var errorBanner = document.getElementById("error-banner");
  var generateBtn = document.getElementById("generate-btn");
  var passwordOutput = document.getElementById("password-output");
  var toggleVisibilityBtn = document.getElementById("toggle-visibility-btn");
  var copyBtn = document.getElementById("copy-btn");
  var copyStatus = document.getElementById("copy-status");

  // Anatomy & Strength
  var anatomyCounts = document.getElementById("anatomy-counts");
  var anatomyTokens = document.getElementById("anatomy-tokens");
  var entropyReadout = document.getElementById("entropy-readout");
  var strengthLabel = document.getElementById("strength-label");
  var strengthBar = document.getElementById("strength-bar");
  var crackTimeText = document.getElementById("crack-time-text");

  // History
  var historyList = document.getElementById("history-list");
  var clearHistoryBtn = document.getElementById("clear-history-btn");

  // Strength Lab elements
  var auditInput = document.getElementById("audit-input");
  var auditToggleBtn = document.getElementById("audit-toggle-btn");
  var auditBar = document.getElementById("audit-bar");
  var auditStrengthLabel = document.getElementById("audit-strength-label");
  var auditEntropy = document.getElementById("audit-entropy");
  var auditCrackTime = document.getElementById("audit-crack-time");
  var chkLen = document.getElementById("chk-len");
  var chkUpper = document.getElementById("chk-upper");
  var chkLower = document.getElementById("chk-lower");
  var chkDigit = document.getElementById("chk-digit");
  var chkSymbol = document.getElementById("chk-symbol");
  var sampleBenchmarksBody = document.getElementById("sample-benchmarks-body");
  var entropyLabSection = document.getElementById("entropy-lab");

  /**
   * Cryptographically secure uniform random integer in [0, max).
   * Uses rejection sampling with crypto.getRandomValues() to eliminate modulo bias.
   */
  function getSecureRandomInt(max) {
    if (max <= 0) {
      throw new Error("Upper bound must be positive.");
    }
    if (!window.crypto || typeof window.crypto.getRandomValues !== "function") {
      throw new Error("Cryptographically secure random generator is unavailable in this browser.");
    }

    var maxUint32 = 0xffffffff;
    var limit = maxUint32 - ((maxUint32 + 1) % max);
    var buffer = new Uint32Array(1);

    while (true) {
      window.crypto.getRandomValues(buffer);
      if (buffer[0] <= limit) {
        return buffer[0] % max;
      }
    }
  }

  function pickSecureChar(pool) {
    return pool.charAt(getSecureRandomInt(pool.length));
  }

  /**
   * Fisher-Yates shuffle powered by crypto.getRandomValues().
   */
  function secureShuffle(chars) {
    for (var i = chars.length - 1; i > 0; i--) {
      var j = getSecureRandomInt(i + 1);
      var temp = chars[i];
      chars[i] = chars[j];
      chars[j] = temp;
    }
    return chars;
  }

  /**
   * Evaluate password strength based on length and character diversity.
   */
  function evaluatePasswordStrength(password) {
    if (!password) {
      return { label: "None", color: "#cbd5e1", percent: 0 };
    }

    var len = password.length;
    var lengthScore = 0;
    if (len >= 16) {
      lengthScore = 3;
    } else if (len >= 12) {
      lengthScore = 2;
    } else if (len >= 8) {
      lengthScore = 1;
    }

    var hasUpper = /[A-Z]/.test(password);
    var hasLower = /[a-z]/.test(password);
    var hasDigit = /[0-9]/.test(password);
    var hasSymbol = /[^A-Za-z0-9]/.test(password);

    var diversityScore =
      (hasUpper ? 1 : 0) +
      (hasLower ? 1 : 0) +
      (hasDigit ? 1 : 0) +
      (hasSymbol ? 1 : 0);

    var totalScore = lengthScore + diversityScore;

    if (len < 10 || diversityScore < 2 || totalScore <= 3) {
      return { label: "Weak", color: "#dc2626", percent: 33 };
    }
    if (totalScore <= 5) {
      return { label: "Medium", color: "#d97706", percent: 66 };
    }
    return { label: "Strong", color: "#16a34a", percent: 100 };
  }

  /**
   * Compute Shannon-pool bit entropy and estimate crack resistance at 10B guesses/sec.
   */
  function calculateEntropyBits(password, customPoolSize) {
    if (!password) return 0;

    if (typeof customPoolSize === "number" && customPoolSize > 0) {
      return customPoolSize;
    }

    var poolSize = 0;
    if (/[A-Z]/.test(password)) poolSize += 26;
    if (/[a-z]/.test(password)) poolSize += 26;
    if (/[0-9]/.test(password)) poolSize += 10;
    if (/[^A-Za-z0-9]/.test(password)) poolSize += 30;
    if (poolSize === 0) return 0;

    return password.length * (Math.log(poolSize) / Math.LN2);
  }

  function formatCrackTime(bits) {
    if (bits <= 0) return "—";
    if (bits < 25) return "Instant (< 1 sec)";
    // Offline fast-hash rate: 10^10 guesses/sec (~2^33.2 guesses/sec)
    var guesses = Math.pow(2, bits) * 0.5;
    var seconds = guesses / 1e10;

    if (seconds < 1) return "Instant (< 1 sec)";
    if (seconds < 60) return Math.round(seconds) + " seconds";
    var minutes = seconds / 60;
    if (minutes < 60) return Math.round(minutes) + " minutes";
    var hours = minutes / 60;
    if (hours < 24) return Math.round(hours) + " hours";
    var days = hours / 24;
    if (days < 365) return Math.round(days) + " days";
    var years = days / 365.25;
    if (years < 1000) return Math.round(years) + " years";
    if (years < 1e6) return (years / 1000).toFixed(1) + "K years";
    if (years < 1e9) return (years / 1e6).toFixed(1) + "M years";
    return "Centuries (1B+ yrs)";
  }

  function showError(message) {
    errorBanner.textContent = message;
    errorBanner.hidden = false;
  }

  function clearError() {
    errorBanner.textContent = "";
    errorBanner.hidden = true;
  }

  function showStatus(message, isError) {
    if (statusTimerId) {
      clearTimeout(statusTimerId);
    }
    copyStatus.textContent = message;
    if (isError) {
      copyStatus.classList.add("is-error");
    } else {
      copyStatus.classList.remove("is-error");
    }

    statusTimerId = setTimeout(function () {
      copyStatus.textContent = "";
      copyStatus.classList.remove("is-error");
    }, 3000);
  }

  function execCommandCopyFallback(text) {
    var textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    textarea.style.top = "0";
    document.body.appendChild(textarea);

    try {
      textarea.focus();
      textarea.select();
      var ok = document.execCommand("copy");
      document.body.removeChild(textarea);
      if (!ok) {
        throw new Error("execCommand copy returned false");
      }
      return true;
    } catch (err) {
      document.body.removeChild(textarea);
      throw err;
    }
  }

  function copyWithFallback(text) {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
      return navigator.clipboard.writeText(text).catch(function () {
        return execCommandCopyFallback(text);
      });
    }
    return Promise.resolve(execCommandCopyFallback(text));
  }

  function handleCopy(text) {
    try {
      copyWithFallback(text)
        .then(function () {
          showStatus("Copied!", false);
        })
        .catch(function () {
          showStatus("Copy blocked by browser", true);
        });
    } catch (_err) {
      showStatus("Copy blocked by browser", true);
    }
  }

  function renderAnatomy(password) {
    anatomyTokens.innerHTML = "";
    if (!password) {
      anatomyCounts.textContent = "Ready";
      var placeholder = document.createElement("span");
      placeholder.className = "anatomy-placeholder";
      placeholder.textContent = "Characters will appear color-coded by type after generation.";
      anatomyTokens.appendChild(placeholder);
      return;
    }

    if (!isPasswordVisible) {
      anatomyCounts.textContent = password.length + " chars (hidden)";
      var hiddenMsg = document.createElement("span");
      hiddenMsg.className = "anatomy-placeholder";
      hiddenMsg.textContent = "•".repeat(password.length);
      anatomyTokens.appendChild(hiddenMsg);
      return;
    }

    var upper = 0;
    var lower = 0;
    var digit = 0;
    var symbol = 0;

    for (var i = 0; i < password.length; i++) {
      var ch = password.charAt(i);
      var span = document.createElement("span");
      span.className = "tok ";

      if (/[A-Z]/.test(ch)) {
        span.className += "tok-upper";
        upper++;
      } else if (/[a-z]/.test(ch)) {
        span.className += "tok-lower";
        lower++;
      } else if (/[0-9]/.test(ch)) {
        span.className += "tok-digit";
        digit++;
      } else {
        span.className += "tok-symbol";
        symbol++;
      }
      span.textContent = ch === " " ? "␣" : ch;
      anatomyTokens.appendChild(span);
    }

    anatomyCounts.textContent =
      upper + "U · " + lower + "L · " + digit + "N · " + symbol + "S";
  }

  function updateStrengthAndTelemetry(password, overrideEntropyBits) {
    var result = evaluatePasswordStrength(password);
    var bits = calculateEntropyBits(password, overrideEntropyBits);
    var crackText = formatCrackTime(bits);

    strengthLabel.textContent = result.label;
    strengthLabel.style.color = result.percent === 0 ? "#64748b" : result.color;
    strengthBar.style.width = result.percent + "%";
    strengthBar.style.backgroundColor = result.color;

    entropyReadout.textContent = bits.toFixed(1) + " bits";
    crackTimeText.textContent = crackText;

    // Mirror into Hero live telemetry card
    heroEntropyBits.textContent = bits.toFixed(1) + " bits";
    heroCrackTime.textContent = crackText;
    if (!password) {
      heroPreviewChars.textContent = "Click Generate to forge";
    } else {
      heroPreviewChars.textContent = isPasswordVisible ? password : "•".repeat(password.length);
    }
  }

  function renderHistory() {
    historyList.innerHTML = "";

    if (sessionHistory.length === 0) {
      var emptyItem = document.createElement("li");
      emptyItem.className = "history-empty";
      emptyItem.textContent = "No passwords generated yet in this session.";
      historyList.appendChild(emptyItem);
      return;
    }

    sessionHistory.forEach(function (pwd, idx) {
      var li = document.createElement("li");
      li.className = "history-item";

      var indexSpan = document.createElement("span");
      indexSpan.className = "history-index";
      indexSpan.textContent = "#" + (idx + 1);

      var pwdSpan = document.createElement("span");
      pwdSpan.className = "history-password";
      pwdSpan.textContent = isPasswordVisible ? pwd : "•".repeat(pwd.length);

      var itemCopyBtn = document.createElement("button");
      itemCopyBtn.type = "button";
      itemCopyBtn.className = "history-copy-btn";
      itemCopyBtn.textContent = "Copy";
      itemCopyBtn.addEventListener("click", function () {
        handleCopy(pwd);
      });

      li.appendChild(indexSpan);
      li.appendChild(pwdSpan);
      li.appendChild(itemCopyBtn);
      historyList.appendChild(li);
    });
  }

  function buildPools() {
    var rawPools = [];
    if (optUpper.checked) rawPools.push(UPPERCASE_CHARS);
    if (optLower.checked) rawPools.push(LOWERCASE_CHARS);
    if (optNumbers.checked) rawPools.push(NUMBER_CHARS);
    if (optSymbols.checked) rawPools.push(SYMBOL_CHARS);

    var customExcluded = customExcludeInput.value || "";

    return rawPools
      .map(function (pool) {
        var filtered = pool;
        if (optExcludeAmbiguous.checked) {
          filtered = filtered.replace(AMBIGUOUS_PATTERN, "");
        }
        if (customExcluded.length > 0) {
          var nextPool = "";
          for (var i = 0; i < filtered.length; i++) {
            if (customExcluded.indexOf(filtered.charAt(i)) === -1) {
              nextPool += filtered.charAt(i);
            }
          }
          filtered = nextPool;
        }
        return filtered;
      })
      .filter(function (pool) {
        return pool.length > 0;
      });
  }

  function generateRandomPassword() {
    var parsedLength = Number(lengthNumber.value);
    if (!Number.isInteger(parsedLength) || parsedLength < MIN_LENGTH || parsedLength > MAX_LENGTH) {
      showError("Password length must be a whole number between 8 and 64.");
      return null;
    }

    lengthSlider.value = String(parsedLength);

    var selectedCount =
      (optUpper.checked ? 1 : 0) +
      (optLower.checked ? 1 : 0) +
      (optNumbers.checked ? 1 : 0) +
      (optSymbols.checked ? 1 : 0);

    if (selectedCount < 2) {
      showError("Please select at least 2 character types.");
      return null;
    }

    var pools = buildPools();
    if (pools.length < 2) {
      showError("At least 2 non-empty character pools remain after exclusions.");
      return null;
    }

    var chars = pools.map(function (pool) {
      return pickSecureChar(pool);
    });

    var combinedPool = pools.join("");
    while (chars.length < parsedLength) {
      chars.push(pickSecureChar(combinedPool));
    }

    secureShuffle(chars);
    var password = chars.join("");
    var exactEntropy = parsedLength * (Math.log(combinedPool.length) / Math.LN2);

    return { password: password, entropyBits: exactEntropy };
  }

  function generateMemorablePassphrase() {
    var count = Number(wordCountSlider.value);
    var separator = separatorSelect.value;
    var capitalize = optCapitalizeWords.checked;
    var appendDigit = optAppendNumber.checked;

    var chosen = [];
    for (var i = 0; i < count; i++) {
      var word = WORD_POOL[getSecureRandomInt(WORD_POOL.length)];
      if (capitalize) {
        word = word.charAt(0).toUpperCase() + word.slice(1);
      }
      chosen.push(word);
    }

    var phrase = chosen.join(separator);
    var entropyBits = count * (Math.log(WORD_POOL.length) / Math.LN2);

    if (appendDigit) {
      phrase += pickSecureChar(NUMBER_CHARS);
      entropyBits += Math.log(10) / Math.LN2;
    }

    return { password: phrase, entropyBits: entropyBits };
  }

  function handleGenerate(shouldCopy) {
    if (shouldCopy === undefined) {
      shouldCopy = true;
    }
    clearError();

    try {
      var generated =
        activeMode === "random" ? generateRandomPassword() : generateMemorablePassphrase();
      if (!generated) return;

      passwordOutput.value = generated.password;
      renderAnatomy(generated.password);
      updateStrengthAndTelemetry(generated.password, generated.entropyBits);

      sessionHistory.unshift(generated.password);
      if (sessionHistory.length > MAX_HISTORY) {
        sessionHistory = sessionHistory.slice(0, MAX_HISTORY);
      }
      renderHistory();

      if (shouldCopy) {
        handleCopy(generated.password);
      }
    } catch (err) {
      showError(err.message || "Failed to generate password.");
    }
  }

  function setMode(mode) {
    activeMode = mode;
    clearError();

    if (mode === "random") {
      tabRandom.classList.add("is-active");
      tabRandom.setAttribute("aria-selected", "true");
      tabPassphrase.classList.remove("is-active");
      tabPassphrase.setAttribute("aria-selected", "false");
      randomControls.hidden = false;
      passphraseControls.hidden = true;
      generateBtn.textContent = "Generate Password";
      heroModeLabel.textContent = "Random Mode";
    } else {
      tabPassphrase.classList.add("is-active");
      tabPassphrase.setAttribute("aria-selected", "true");
      tabRandom.classList.remove("is-active");
      tabRandom.setAttribute("aria-selected", "false");
      passphraseControls.hidden = false;
      randomControls.hidden = true;
      generateBtn.textContent = "Generate Passphrase";
      heroModeLabel.textContent = "Passphrase Mode";
    }
  }

  function applyPreset(presetName) {
    setMode("random");
    if (presetName === "standard") {
      lengthNumber.value = "12";
      lengthSlider.value = "12";
      optUpper.checked = true;
      optLower.checked = true;
      optNumbers.checked = true;
      optSymbols.checked = true;
      optExcludeAmbiguous.checked = false;
    } else if (presetName === "strong") {
      lengthNumber.value = "20";
      lengthSlider.value = "20";
      optUpper.checked = true;
      optLower.checked = true;
      optNumbers.checked = true;
      optSymbols.checked = true;
      optExcludeAmbiguous.checked = false;
    } else if (presetName === "readable") {
      lengthNumber.value = "16";
      lengthSlider.value = "16";
      optUpper.checked = true;
      optLower.checked = true;
      optNumbers.checked = true;
      optSymbols.checked = false;
      optExcludeAmbiguous.checked = true;
    } else if (presetName === "max") {
      lengthNumber.value = "32";
      lengthSlider.value = "32";
      optUpper.checked = true;
      optLower.checked = true;
      optNumbers.checked = true;
      optSymbols.checked = true;
      optExcludeAmbiguous.checked = false;
    }
    handleGenerate();
  }

  function updateStrengthLab() {
    var val = auditInput.value;
    var res = evaluatePasswordStrength(val);
    var bits = calculateEntropyBits(val);

    auditBar.style.width = res.percent + "%";
    auditBar.style.backgroundColor = res.color;
    auditStrengthLabel.textContent = res.label;
    auditStrengthLabel.style.color = res.percent === 0 ? "#64748b" : res.color;
    auditEntropy.textContent = bits.toFixed(1) + " bits";
    auditCrackTime.textContent = formatCrackTime(bits);

    chkLen.classList.toggle("is-met", val.length >= 12);
    chkUpper.classList.toggle("is-met", /[A-Z]/.test(val));
    chkLower.classList.toggle("is-met", /[a-z]/.test(val));
    chkDigit.classList.toggle("is-met", /[0-9]/.test(val));
    chkSymbol.classList.toggle("is-met", /[^A-Za-z0-9]/.test(val));
  }

  // Wire listeners
  tabRandom.addEventListener("click", function () {
    setMode("random");
  });
  tabPassphrase.addEventListener("click", function () {
    setMode("passphrase");
  });

  for (var i = 0; i < presetButtons.length; i++) {
    presetButtons[i].addEventListener("click", function () {
      applyPreset(this.getAttribute("data-preset"));
    });
  }

  lengthSlider.addEventListener("input", function () {
    lengthNumber.value = lengthSlider.value;
    clearError();
  });

  lengthNumber.addEventListener("input", function () {
    var val = Number(lengthNumber.value);
    if (Number.isInteger(val) && val >= MIN_LENGTH && val <= MAX_LENGTH) {
      lengthSlider.value = String(val);
      clearError();
    }
  });

  wordCountSlider.addEventListener("input", function () {
    wordCountReadout.textContent = wordCountSlider.value;
  });

  toggleVisibilityBtn.addEventListener("click", function () {
    isPasswordVisible = !isPasswordVisible;
    passwordOutput.type = isPasswordVisible ? "text" : "password";
    toggleVisibilityBtn.textContent = isPasswordVisible ? "Hide" : "Show";
    renderAnatomy(passwordOutput.value);
    renderHistory();
    if (passwordOutput.value) {
      heroPreviewChars.textContent = isPasswordVisible
        ? passwordOutput.value
        : "•".repeat(passwordOutput.value.length);
    }
  });

  copyBtn.addEventListener("click", function () {
    if (!passwordOutput.value) {
      showError("Generate a password first before copying.");
      return;
    }
    clearError();
    handleCopy(passwordOutput.value);
  });

  clearHistoryBtn.addEventListener("click", function () {
    sessionHistory = [];
    renderHistory();
  });

  generateBtn.addEventListener("click", handleGenerate);
  headerGenerateCta.addEventListener("click", function () {
    handleGenerate();
  });

  auditInput.addEventListener("input", updateStrengthLab);
  auditToggleBtn.addEventListener("click", function () {
    var showing = auditInput.type === "text";
    auditInput.type = showing ? "password" : "text";
    auditToggleBtn.textContent = showing ? "Show" : "Hide";
  });

  function renderSampleBenchmarks() {
    if (!sampleBenchmarksBody) return;
    sampleBenchmarksBody.innerHTML = "";

    SAMPLE_BENCHMARKS.forEach(function (item) {
      var res = evaluatePasswordStrength(item.value);
      var bits = calculateEntropyBits(item.value);
      var crack = formatCrackTime(bits);

      var tr = document.createElement("tr");

      var tdScenario = document.createElement("td");
      tdScenario.textContent = item.scenario;

      var tdSample = document.createElement("td");
      var codeEl = document.createElement("code");
      codeEl.className = "sample-code";
      codeEl.textContent = item.value;
      tdSample.appendChild(codeEl);

      var tdLen = document.createElement("td");
      tdLen.className = "num-col";
      tdLen.textContent = String(item.value.length);

      var tdEntropy = document.createElement("td");
      tdEntropy.className = "num-col";
      tdEntropy.textContent = bits.toFixed(1) + " bits";

      var tdCrack = document.createElement("td");
      tdCrack.textContent = crack;

      var tdRating = document.createElement("td");
      tdRating.className = "rating-" + res.label.toLowerCase();
      tdRating.textContent = res.label;

      var tdAction = document.createElement("td");
      tdAction.className = "action-col";
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn-test-sample";
      btn.textContent = "Test in Lab";
      btn.addEventListener("click", function () {
        auditInput.value = item.value;
        auditInput.type = "text";
        auditToggleBtn.textContent = "Hide";
        updateStrengthLab();
        if (entropyLabSection && typeof entropyLabSection.scrollIntoView === "function") {
          entropyLabSection.scrollIntoView({ behavior: "smooth" });
        }
      });
      tdAction.appendChild(btn);

      tr.appendChild(tdScenario);
      tr.appendChild(tdSample);
      tr.appendChild(tdLen);
      tr.appendChild(tdEntropy);
      tr.appendChild(tdCrack);
      tr.appendChild(tdRating);
      tr.appendChild(tdAction);
      sampleBenchmarksBody.appendChild(tr);
    });
  }

  // Render dummy benchmarks and seed initial preview without touching clipboard
  renderSampleBenchmarks();
  auditInput.value = "Summer2024";
  updateStrengthLab();
  handleGenerate(false);
})();
