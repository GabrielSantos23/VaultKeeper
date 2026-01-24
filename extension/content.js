const browserAPI = typeof browser !== "undefined" ? browser : chrome;

let detectedFields = null;
let currentDomain = window.location.hostname;
let pendingCredentials = null;
let savePromptShown = false;
let promptTimeoutId = null;
let existingCredentialId = null;

const MULTISTEP_STORAGE_KEY = "vaultkeeper_multistep_";

const PENDING_CREDENTIALS_KEY = "vaultkeeper_pending_credentials";

const USERNAME_SELECTORS = [
  'input[autocomplete="username"]',
  'input[autocomplete="email"]',
  'input[type="email"]',
  'input[name*="user" i]',
  'input[name*="login" i]',
  'input[name*="email" i]',
  'input[id*="user" i]',
  'input[id*="login" i]',
  'input[id*="email" i]',
  'input[placeholder*="email" i]',
  'input[placeholder*="user" i]',
  'input[type="text"][name*="user" i]',
  'input[type="text"][name*="login" i]',
  'input[type="text"][name*="email" i]',
  'input[type="text"][id*="user" i]',
  'input[type="text"][id*="login" i]',
  'input[type="text"][id*="email" i]',
];

const PASSWORD_SELECTORS = [
  'input[type="password"]',
  'input[autocomplete="current-password"]',
  'input[autocomplete="new-password"]',
];

const TOTP_SELECTORS = [
  'input[name="totp" i]', 'input[name="code" i]', 'input[name="otp" i]',
  'input[name*="2fa" i]', 'input[id*="totp" i]', 'input[id*="otp" i]',
  'input[autocomplete="one-time-code"]', 'input[placeholder*="code" i]',
  'input[placeholder*="6-digit" i]'
];
function escapeHtml(text) {
  if (text === null || text === undefined) return "";
  const div = document.createElement("div");
  div.textContent = String(text);
  return div.innerHTML;
}

function getBaseDomain() {
  const parts = currentDomain.split(".");
  if (parts.length > 2) {
    return parts.slice(-2).join(".");
  }
  return currentDomain;
}

function storeMultiStepUsername(username) {
  if (!username) return;
  const key = MULTISTEP_STORAGE_KEY + getBaseDomain();
  const data = {
    username: username,
    timestamp: Date.now(),
    originalDomain: currentDomain,
  };
  sessionStorage.setItem(key, JSON.stringify(data));
}

function getMultiStepUsername() {
  const key = MULTISTEP_STORAGE_KEY + getBaseDomain();
  try {
    const stored = sessionStorage.getItem(key);
    if (!stored) return null;

    const data = JSON.parse(stored);
    const age = Date.now() - data.timestamp;
    if (age > 5 * 60 * 1000) {
      sessionStorage.removeItem(key);
      return null;
    }

    return data.username;
  } catch (e) {
    return null;
  }
}

function clearMultiStepUsername() {
  const key = MULTISTEP_STORAGE_KEY + getBaseDomain();
  sessionStorage.removeItem(key);
}

function storePendingCredentials(
  credentials,
  isUpdate = false,
  credentialId = null,
) {
  const data = {
    credentials: credentials,
    isUpdate: isUpdate,
    credentialId: credentialId,
    timestamp: Date.now(),
  };
  sessionStorage.setItem(PENDING_CREDENTIALS_KEY, JSON.stringify(data));
}

function getPendingCredentials() {
  try {
    const stored = sessionStorage.getItem(PENDING_CREDENTIALS_KEY);
    if (!stored) return null;

    const data = JSON.parse(stored);
    const age = Date.now() - data.timestamp;
    if (age > 30 * 1000) {
      clearPendingCredentials();
      return null;
    }

    return data;
  } catch (e) {
    return null;
  }
}

function clearPendingCredentials() {
  sessionStorage.removeItem(PENDING_CREDENTIALS_KEY);
}

async function checkExistingCredential(domain, username) {
  return new Promise((resolve) => {
    browserAPI.runtime.sendMessage(
      {
        action: "check_credentials",
        domain: domain,
      },
      (response) => {
        if (response && response.success && response.credentials) {
          const existing = response.credentials.find(
            (cred) => cred.username.toLowerCase() === username.toLowerCase(),
          );
          resolve(existing || null);
        } else {
          resolve(null);
        }
      },
    );
  });
}

function detectLoginFields() {
  const fields = {
    username: null,
    password: null,
    form: null,
    isMultiStep: false,
  };
  for (const selector of PASSWORD_SELECTORS) {
    const passwordFields = document.querySelectorAll(selector);
    for (const field of passwordFields) {
      if (isVisible(field)) {
        fields.password = field;
        fields.form = field.closest("form");
        break;
      }
    }
    if (fields.password) break;
  }
  const searchContainer = fields.form || document;

  for (const selector of USERNAME_SELECTORS) {
    const candidates = searchContainer.querySelectorAll(selector);
    for (const candidate of candidates) {
      if (!isVisible(candidate)) continue;
      if (candidate === fields.password) continue;
      
      // Exclude obvious search/TOTP fields from being treated as username
      const name = (candidate.name || '').toLowerCase();
      const id = (candidate.id || '').toLowerCase();
      const placeholder = (candidate.placeholder || '').toLowerCase();
      
      if (
          name.includes('search') || id.includes('search') || placeholder.includes('search') ||
          name.includes('query') || id.includes('query') ||
          name.includes('totp') || id.includes('totp') || 
          name.includes('code') || id.includes('code') || placeholder.includes('code') ||
          name.includes('otp') || id.includes('otp') ||
          name.includes('2fa') || id.includes('2fa')
      ) {
          continue;
      }

      if (fields.password) {
        if (
          fields.password.compareDocumentPosition(candidate) &
          Node.DOCUMENT_POSITION_PRECEDING
        ) {
          fields.username = candidate;
          break;
        }
      }

      if (!fields.username) {
        fields.username = candidate;
      }
    }
    if (fields.username) break;
  }
  if (fields.password && !fields.username) {
    fields.isMultiStep = true;
  } else if (fields.username && !fields.password) {
    fields.isMultiStep = true;
    fields.form = fields.username.closest("form");
  }
  if (fields.username || fields.password) {
    return fields;
  }

  return null;
}

function isVisible(element) {
  if (!element) return false;
  const rect = element.getBoundingClientRect();
  const style = window.getComputedStyle(element);
  return (
    rect.width > 0 &&
    rect.height > 0 &&
    style.visibility !== "hidden" &&
    style.display !== "none" &&
    style.opacity !== "0"
  );
}

function fillCredentials(username, password, totpCode = null) {
  if (!detectedFields) {
    detectedFields = detectLoginFields();
  }

  let filled = false;
  
  let totpField = null;
  if (totpCode) {
      if (fillTOTP(totpCode)) {
          filled = true;
          // Try to find the filled TOTP field to avoid overwriting
           const totpSelectors = [
            'input[name="totp" i]', 'input[name="code" i]', 'input[name="otp" i]',
            'input[name*="2fa" i]', 'input[id*="totp" i]', 'input[id*="otp" i]',
            'input[autocomplete="one-time-code"]', 'input[placeholder*="code" i]',
            'input[placeholder*="6-digit" i]'
          ];
          for (const selector of totpSelectors) {
            const inputs = document.querySelectorAll(selector);
            for (const input of inputs) {
                if (isVisible(input) && input.value === totpCode) {
                    totpField = input;
                    break;
                }
            }
            if (totpField) break;
          }
      }
  }

  if (
    !detectedFields ||
    (!detectedFields.username && !detectedFields.password)
  ) {
    return filled; // Return true if TOTP was filled at least
  }

  // Prevent username fill if it targets the detected TOTP field
  if (detectedFields.username && !detectedFields.password) {
    if (username && detectedFields.username !== totpField) {
      setFieldValue(detectedFields.username, username);
      storeMultiStepUsername(username);
      filled = true;
    }
  } else if (detectedFields.password && !detectedFields.username) {
    if (password) {
      setFieldValue(detectedFields.password, password);
      filled = true;
    }
  } else {
    if (detectedFields.username && username && detectedFields.username !== totpField) {
      setFieldValue(detectedFields.username, username);
      filled = true;
    }
    
    // ... rest of function

    if (detectedFields.password && password) {
      setFieldValue(detectedFields.password, password);
      filled = true;
    }
  }

  return filled;
}

function fillTOTP(code) {
  if (!code) return false;
  
  for (const selector of TOTP_SELECTORS) {
    const inputs = document.querySelectorAll(selector);
    for (const input of inputs) {
      if (isVisible(input)) {
        setFieldValue(input, code);
        return true;
      }
    }
  }
  return false;
}

function setFieldValue(field, value) {
  field.focus();
  field.value = value;

  field.dispatchEvent(new Event("input", { bubbles: true }));
  field.dispatchEvent(new Event("change", { bubbles: true }));
  field.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true }));
  field.dispatchEvent(new KeyboardEvent("keyup", { bubbles: true }));

  const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype,
    "value",
  ).set;
  nativeInputValueSetter.call(field, value);
  field.dispatchEvent(new Event("input", { bubbles: true }));
}

function fillCreditCard(cardNumber, expiryDate, cvv, cardholderName) {
  let filled = false;

  const cardNumberSelectors = [
    'input[autocomplete="cc-number"]',
    'input[name*="card" i][name*="number" i]',
    'input[name*="cardnumber" i]',
    'input[id*="card" i][id*="number" i]',
    'input[id*="cardnumber" i]',
    'input[placeholder*="card number" i]',
    'input[data-card-field="number"]',
  ];

  const expirySelectors = [
    'input[autocomplete="cc-exp"]',
    'input[name*="expir" i]',
    'input[name*="exp" i][name*="date" i]',
    'input[id*="expir" i]',
    'input[placeholder*="MM" i]',
  ];

  const cvvSelectors = [
    'input[autocomplete="cc-csc"]',
    'input[name*="cvv" i]',
    'input[name*="cvc" i]',
    'input[name*="security" i][name*="code" i]',
    'input[id*="cvv" i]',
    'input[id*="cvc" i]',
    'input[placeholder*="CVV" i]',
    'input[placeholder*="CVC" i]',
  ];

  const nameSelectors = [
    'input[autocomplete="cc-name"]',
    'input[name*="card" i][name*="holder" i]',
    'input[name*="cardholder" i]',
    'input[name*="name" i][name*="card" i]',
    'input[id*="cardholder" i]',
    'input[placeholder*="name on card" i]',
  ];

  for (const selector of cardNumberSelectors) {
    const field = document.querySelector(selector);
    if (field && isVisible(field)) {
      setFieldValue(field, cardNumber);
      filled = true;
      break;
    }
  }

  for (const selector of expirySelectors) {
    const field = document.querySelector(selector);
    if (field && isVisible(field)) {
      setFieldValue(field, expiryDate);
      filled = true;
      break;
    }
  }

  for (const selector of cvvSelectors) {
    const field = document.querySelector(selector);
    if (field && isVisible(field)) {
      setFieldValue(field, cvv);
      filled = true;
      break;
    }
  }

  for (const selector of nameSelectors) {
    const field = document.querySelector(selector);
    if (field && isVisible(field)) {
      setFieldValue(field, cardholderName);
      filled = true;
      break;
    }
  }

  return filled;
}

function captureCredentials(form) {
  const passwordField = form.querySelector('input[type="password"]');
  let username = "";
  for (const selector of USERNAME_SELECTORS) {
    const field = form.querySelector(selector);
    if (field && field !== passwordField && field.value) {
      username = field.value;
      break;
    }
  }
  if (passwordField && passwordField.value && username) {
    clearMultiStepUsername();
    return {
      domain: currentDomain,
      username: username,
      password: passwordField.value,
    };
  }
  if (passwordField && passwordField.value && !username) {
    const storedUsername = getMultiStepUsername();
    if (storedUsername) {
      clearMultiStepUsername();
      return {
        domain: currentDomain,
        username: storedUsername,
        password: passwordField.value,
      };
    }
  }
  if (!passwordField && username) {
    storeMultiStepUsername(username);
    return null;
  }

  return null;
}

function captureVisibleUsername() {
  for (const selector of USERNAME_SELECTORS) {
    const fields = document.querySelectorAll(selector);
    for (const field of fields) {
      if (isVisible(field) && field.value && field.type !== "password") {
        return field.value;
      }
    }
  }
  return null;
}

function createSavePrompt(
  isUpdateMode = false,
  showUnlockForm = false,
  unlockContext = "save",
) {
  const existing = document.getElementById("vaultkeeper-save-prompt");
  if (existing) existing.remove();

  const prompt = document.createElement("div");
  prompt.id = "vaultkeeper-save-prompt";

  const overlay = document.createElement("div");
  overlay.className = "vk-prompt-overlay";
  prompt.appendChild(overlay);

  const container = document.createElement("div");
  container.className = "vk-prompt-container";
  const header = document.createElement("div");
  header.className = "vk-prompt-header";

  const iconSpan = document.createElement("span");
  iconSpan.className = "vk-prompt-icon";

  const lockSvg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  lockSvg.setAttribute("viewBox", "0 0 24 24");
  lockSvg.setAttribute("width", "20");
  lockSvg.setAttribute("height", "20");
  lockSvg.setAttribute("fill", "none");
  lockSvg.setAttribute("stroke", "currentColor");
  lockSvg.setAttribute("stroke-width", "2");

  const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  rect.setAttribute("x", "3");
  rect.setAttribute("y", "11");
  rect.setAttribute("width", "18");
  rect.setAttribute("height", "11");
  rect.setAttribute("rx", "2");
  lockSvg.appendChild(rect);

  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", "M7 11V7a5 5 0 0 1 10 0v4");
  lockSvg.appendChild(path);

  iconSpan.appendChild(lockSvg);
  header.appendChild(iconSpan);

  const titleSpan = document.createElement("span");
  titleSpan.className = "vk-prompt-title";
  titleSpan.textContent = "VaultKeeper";
  header.appendChild(titleSpan);

  const closeBtn = document.createElement("button");
  closeBtn.className = "vk-close-btn";
  closeBtn.id = "vk-close";
  closeBtn.textContent = "×";
  header.appendChild(closeBtn);

  container.appendChild(header);
  const body = document.createElement("div");
  body.className = "vk-prompt-body";

  const messageP = document.createElement("p");
  messageP.className = "vk-prompt-message";
  if (showUnlockForm) {
    messageP.textContent = "Unlock VaultKeeper";
  } else if (isUpdateMode) {
    messageP.textContent = "Update password?";
  } else {
    messageP.textContent = "Save this password?";
  }
  body.appendChild(messageP);

  if (showUnlockForm) {
    const unlockSection = document.createElement("div");
    unlockSection.className = "vk-unlock-section";
    unlockSection.id = "vk-unlock-section";

    const pUnlock = document.createElement("p");
    pUnlock.className = "vk-unlock-message";
    pUnlock.textContent =
      unlockContext === "fill"
        ? "Enter your master password to access credentials"
        : "Enter your master password to save credentials";
    unlockSection.appendChild(pUnlock);

    const inputGroup = document.createElement("div");
    inputGroup.className = "vk-input-group";
    const pwInput = document.createElement("input");
    pwInput.type = "password";
    pwInput.id = "vk-master-password";
    pwInput.className = "vk-input";
    pwInput.placeholder = "Master Password";
    pwInput.autofocus = true;
    inputGroup.appendChild(pwInput);
    unlockSection.appendChild(inputGroup);

    const errorP = document.createElement("p");
    errorP.id = "vk-unlock-error";
    errorP.className = "vk-error hidden";
    unlockSection.appendChild(errorP);

    body.appendChild(unlockSection);
  } else {
    const preview = document.createElement("div");
    preview.className = "vk-credential-preview";

    const createRow = (label, id, value) => {
      const row = document.createElement("div");
      row.className = "vk-cred-row";
      const labelSpan = document.createElement("span");
      labelSpan.className = "vk-cred-label";
      labelSpan.textContent = label;
      const valueSpan = document.createElement("span");
      valueSpan.className = "vk-cred-value";
      if (id) valueSpan.id = id;
      valueSpan.textContent = value;
      row.appendChild(labelSpan);
      row.appendChild(valueSpan);
      return row;
    };

    preview.appendChild(createRow("Website", "vk-domain", currentDomain));
    preview.appendChild(createRow("Username", "vk-username", "-"));
    preview.appendChild(createRow("Password", null, "••••••••"));

    body.appendChild(preview);
  }

  container.appendChild(body);
  const actions = document.createElement("div");
  actions.className = "vk-prompt-actions";

  const cancelBtn = document.createElement("button");
  cancelBtn.className = "vk-btn vk-btn-secondary";

  if (showUnlockForm) {
    cancelBtn.id = "vk-cancel";
    cancelBtn.textContent = "Cancel";
    actions.appendChild(cancelBtn);

    const unlockActionBtn = document.createElement("button");
    unlockActionBtn.className = "vk-btn vk-btn-primary";
    unlockActionBtn.id = "vk-unlock";
    unlockActionBtn.textContent =
      unlockContext === "fill" ? "Unlock & Fill" : "Unlock & Save";
    actions.appendChild(unlockActionBtn);
  } else {
    if (!isUpdateMode) {
      const neverBtn = document.createElement("button");
      neverBtn.className = "vk-btn vk-btn-secondary";
      neverBtn.id = "vk-never";
      neverBtn.textContent = "Never for this site";
      actions.appendChild(neverBtn);
    } else {
      cancelBtn.id = "vk-cancel";
      cancelBtn.textContent = "Cancel";
      actions.appendChild(cancelBtn);
    }

    const saveBtn = document.createElement("button");
    saveBtn.className = "vk-btn vk-btn-primary";
    saveBtn.id = "vk-save";
    saveBtn.textContent = isUpdateMode ? "Update Password" : "Save Password";
    actions.appendChild(saveBtn);
  }

  container.appendChild(actions);
  prompt.appendChild(container);

  document.body.appendChild(prompt);

  return prompt;
}

async function showSavePrompt(credentials) {
  if (savePromptShown) return;

  const neverSave = JSON.parse(
    localStorage.getItem("vaultkeeper_never_save") || "[]",
  );
  if (neverSave.includes(currentDomain)) return;

  const existingCred = await checkExistingCredential(
    credentials.domain,
    credentials.username,
  );

  let isUpdateMode = false;

  if (existingCred) {
    if (existingCred.password === credentials.password) {
      return;
    }
    isUpdateMode = true;
    existingCredentialId = existingCred.id;
  }

  savePromptShown = true;
  pendingCredentials = credentials;
  storePendingCredentials(credentials, isUpdateMode, existingCredentialId);

  displaySavePrompt(credentials, isUpdateMode);
}

function displaySavePrompt(credentials, isUpdateMode = false) {
  const prompt = createSavePrompt(isUpdateMode);

  document.getElementById("vk-domain").textContent = credentials.domain;
  document.getElementById("vk-username").textContent = credentials.username;
  if (promptTimeoutId) {
    clearTimeout(promptTimeoutId);
  }
  promptTimeoutId = setTimeout(() => {
    hidePrompt();
  }, 30000);

  document.getElementById("vk-save").addEventListener("click", () => {
    if (isUpdateMode && existingCredentialId) {
      updateCredentials(credentials, existingCredentialId);
    } else {
      saveCredentials(credentials);
    }
    hidePrompt();
  });

  const neverBtn = document.getElementById("vk-never");
  if (neverBtn) {
    neverBtn.addEventListener("click", () => {
      const neverSave = JSON.parse(
        localStorage.getItem("vaultkeeper_never_save") || "[]",
      );
      neverSave.push(currentDomain);
      localStorage.setItem("vaultkeeper_never_save", JSON.stringify(neverSave));
      hidePrompt();
    });
  }

  const cancelBtn = document.getElementById("vk-cancel");
  if (cancelBtn) {
    cancelBtn.addEventListener("click", hidePrompt);
  }

  document.getElementById("vk-close").addEventListener("click", hidePrompt);
}

function hidePrompt() {
  if (promptTimeoutId) {
    clearTimeout(promptTimeoutId);
    promptTimeoutId = null;
  }

  const prompt = document.getElementById("vaultkeeper-save-prompt");
  if (prompt) {
    prompt.style.animation = "vk-fade-out 0.2s ease forwards";
    setTimeout(() => prompt.remove(), 200);
  }
  savePromptShown = false;
  pendingCredentials = null;
  existingCredentialId = null;
  clearPendingCredentials();
}

async function saveCredentials(credentials) {
  try {
    const response = await browserAPI.runtime.sendMessage({
      action: "save_credentials",
      domain: credentials.domain,
      username: credentials.username,
      password: credentials.password,
    });
    if (response && response.success === true) {
      showNotification("Password saved!", "success");
    } else if (
      response &&
      (response.locked ||
        response.error?.includes("locked") ||
        response.error?.includes("Vault"))
    ) {
      showUnlockPrompt(credentials, false);
    } else if (!response) {
      showNotification("Connection error", "error");
    } else {
      showNotification(response.error || "Failed to save password", "error");
    }
  } catch (error) {
    if (error.message?.includes("locked") || error.message?.includes("Vault")) {
      showUnlockPrompt(credentials, false);
    } else {
      showNotification("Connection error", "error");
    }
  }
}

async function updateCredentials(credentials, id) {
  try {
    const response = await browserAPI.runtime.sendMessage({
      action: "update_credentials",
      id: id,
      domain: credentials.domain,
      username: credentials.username,
      password: credentials.password,
    });

    if (response && response.success) {
      showNotification("Password updated!", "success");
    } else if (
      response &&
      (response.locked ||
        response.error?.includes("locked") ||
        response.error?.includes("Vault"))
    ) {
      showUnlockPrompt(credentials, true, id);
    } else {
      showNotification("Failed to update password", "error");
    }
  } catch (error) {
    if (error.message?.includes("locked") || error.message?.includes("Vault")) {
      showUnlockPrompt(credentials, true, id);
    } else {
      showNotification("Connection error", "error");
    }
  }
}

function showUnlockPrompt(
  credentials,
  isUpdateMode = false,
  credentialId = null,
) {
  pendingCredentials = credentials;
  existingCredentialId = credentialId;

  const prompt = createSavePrompt(isUpdateMode, true, "save");
  const unlockBtn = document.getElementById("vk-unlock");
  const cancelBtn = document.getElementById("vk-cancel");
  const closeBtn = document.getElementById("vk-close");
  const passwordInput = document.getElementById("vk-master-password");
  if (promptTimeoutId) {
    clearTimeout(promptTimeoutId);
  }
  promptTimeoutId = setTimeout(() => {
    hidePrompt();
  }, 60000);

  unlockBtn?.addEventListener("click", async () => {
    const masterPassword = passwordInput?.value;
    if (!masterPassword) {
      showUnlockError("Please enter your master password");
      return;
    }

    unlockBtn.disabled = true;
    unlockBtn.textContent = "Unlocking...";

    try {
      const unlockResponse = await browserAPI.runtime.sendMessage({
        action: "unlock",
        password: masterPassword,
      });

      if (unlockResponse && unlockResponse.success) {
        hidePrompt();

        if (isUpdateMode && credentialId) {
          await updateCredentials(credentials, credentialId);
        } else {
          await saveCredentials(credentials);
        }
      } else {
        showUnlockError("Invalid master password");
        unlockBtn.disabled = false;
        unlockBtn.textContent = "Unlock & Save";
      }
    } catch (error) {
      showUnlockError("Failed to unlock vault");
      unlockBtn.disabled = false;
      unlockBtn.textContent = "Unlock & Save";
    }
  });
  passwordInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      unlockBtn?.click();
    }
  });

  cancelBtn?.addEventListener("click", hidePrompt);
  closeBtn?.addEventListener("click", hidePrompt);
  setTimeout(() => passwordInput?.focus(), 100);
}

function showUnlockAndFillPrompt(targetField) {
  const prompt = createSavePrompt(false, true, "fill");
  const unlockBtn = document.getElementById("vk-unlock");
  const cancelBtn = document.getElementById("vk-cancel");
  const closeBtn = document.getElementById("vk-close");
  const passwordInput = document.getElementById("vk-master-password");

  if (promptTimeoutId) {
    clearTimeout(promptTimeoutId);
  }
  promptTimeoutId = setTimeout(() => {
    hidePrompt();
  }, 60000);

  unlockBtn?.addEventListener("click", async () => {
    const masterPassword = passwordInput?.value;
    if (!masterPassword) {
      showUnlockError("Please enter your master password");
      return;
    }

    unlockBtn.disabled = true;
    unlockBtn.textContent = "Unlocking...";

    try {
      const unlockResponse = await browserAPI.runtime.sendMessage({
        action: "unlock",
        password: masterPassword,
      });

      if (unlockResponse && unlockResponse.success) {
        hidePrompt();
        requestCredentials(targetField);
      } else {
        // Fix for Issue 1: Double check status in case of false negative
        browserAPI.runtime.sendMessage({ action: "status" }, (statusResp) => {
            if (statusResp && statusResp.success && statusResp.unlocked) {
                 hidePrompt();
                 requestCredentials(targetField);
            } else {
                 showUnlockError("Invalid master password");
                 unlockBtn.disabled = false;
                 unlockBtn.textContent = "Unlock & Fill";
            }
        });
      }
    } catch (error) {
      showUnlockError("Failed to unlock vault");
      unlockBtn.disabled = false;
      unlockBtn.textContent = "Unlock & Fill";
    }
  });

  passwordInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      unlockBtn?.click();
    }
  });

  cancelBtn?.addEventListener("click", hidePrompt);
  closeBtn?.addEventListener("click", hidePrompt);
  setTimeout(() => passwordInput?.focus(), 100);
}

function showUnlockError(message) {
  const errorEl = document.getElementById("vk-unlock-error");
  if (errorEl) {
    errorEl.textContent = message;
    errorEl.classList.remove("hidden");
  }
}

function showNotification(message, type = "success") {
  const existing = document.getElementById("vaultkeeper-notification");
  if (existing) existing.remove();

  const notification = document.createElement("div");
  notification.id = "vaultkeeper-notification";
  notification.className = type;

  const iconSpan = document.createElement("span");
  iconSpan.className = "vk-notif-icon";

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("width", "18");
  svg.setAttribute("height", "18");
  svg.setAttribute("fill", "none");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("stroke-width", "3");

  if (type === "success") {
    const polyline = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "polyline",
    );
    polyline.setAttribute("points", "20 6 9 17 4 12");
    svg.appendChild(polyline);
  } else {
    const line1 = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "line",
    );
    line1.setAttribute("x1", "18");
    line1.setAttribute("y1", "6");
    line1.setAttribute("x2", "6");
    line1.setAttribute("y2", "18");
    const line2 = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "line",
    );
    line2.setAttribute("x1", "6");
    line2.setAttribute("y1", "6");
    line2.setAttribute("x2", "18");
    line2.setAttribute("y2", "18");
    svg.appendChild(line1);
    svg.appendChild(line2);
  }

  iconSpan.appendChild(svg);
  notification.appendChild(iconSpan);

  const messageSpan = document.createElement("span");
  messageSpan.className = "vk-notif-message";
  messageSpan.textContent = message;
  notification.appendChild(messageSpan);

  document.body.appendChild(notification);

  setTimeout(() => {
    notification.classList.add("fade-out");
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

function shouldNeverSave() {
  const neverSave = JSON.parse(
    localStorage.getItem("vaultkeeper_never_save") || "[]",
  );
  return neverSave.includes(currentDomain);
}

function setupFormInterception() {
  if (document._vaultKeeperInterceptionSetup) return;
  document._vaultKeeperInterceptionSetup = true;

  document.addEventListener(
    "submit",
    (e) => {
      const form = e.target;
      if (form.tagName !== "FORM") return;

      const credentials = captureCredentials(form);
      if (credentials && !shouldNeverSave()) {
        setTimeout(() => showSavePrompt(credentials), 500);
      }
    },
    true,
  );

  document.addEventListener(
    "click",
    (e) => {
      const button = e.target.closest(
        'button[type="submit"], input[type="submit"], button:not([type])',
      );
      if (!button) return;

      const form = button.closest("form");
      if (!form) return;
      const credentials = captureCredentials(form);

      if (credentials && !shouldNeverSave()) {
        setTimeout(() => showSavePrompt(credentials), 500);
      }
    },
    true,
  );

  document.addEventListener(
    "keydown",
    (e) => {
      if (e.key !== "Enter") return;

      const field = e.target;
      const form = field.closest("form");
      if (!form) return;
      if (
        field.type === "password" ||
        USERNAME_SELECTORS.some((s) => field.matches(s))
      ) {
        const credentials = captureCredentials(form);
        if (credentials && !shouldNeverSave()) {
          setTimeout(() => showSavePrompt(credentials), 500);
        }
      }
    },
    true,
  );
}

// Positioning helper
function updateIconPosition(field, icon) {
  if (!isVisible(field)) {
    icon.style.display = 'none';
    return;
  }
  icon.style.display = 'flex';
  const rect = field.getBoundingClientRect();
  const scrollX = window.scrollX || window.pageXOffset;
  const scrollY = window.scrollY || window.pageYOffset;

  // Position: centered vertically in input, right aligned with padding
  // But wait, if we append to body, we need absolute coords.
  const top = rect.top + scrollY + (rect.height / 2) - 10; // 10 is half icon height (20px)
  const left = rect.right + scrollX - 30; // 30px from right edge (20px icon + 10px padding)

  icon.style.top = `${top}px`;
  icon.style.left = `${left}px`;
}

function addVaultKeeperIcon(field) {
  if (field.dataset.vaultkeeperIcon) return;
  field.dataset.vaultkeeperIcon = "true";

  const icon = document.createElement("div");
  icon.className = "vaultkeeper-field-icon";

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("width", "16");
  svg.setAttribute("height", "16");
  svg.setAttribute("fill", "none");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("stroke-width", "2");

  const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  rect.setAttribute("x", "3");
  rect.setAttribute("y", "11");
  rect.setAttribute("width", "18");
  rect.setAttribute("height", "11");
  rect.setAttribute("rx", "2");
  svg.appendChild(rect);

  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", "M7 11V7a5 5 0 0 1 10 0v4");
  svg.appendChild(path);

  icon.appendChild(svg);
  icon.title = "VaultKeeper - Fill credential";

  icon.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    requestCredentials(field);
  });
  
  field.addEventListener("focus", () => {
    if (document.activeElement === field) {
      requestCredentials(field, true);
    }
  });

  // Append to body to avoid positioning issues relative to parent
  document.body.appendChild(icon);
  
  // Initial position
  updateIconPosition(field, icon);

  // Update position on events
  const updatePos = () => updateIconPosition(field, icon);
  window.addEventListener('scroll', updatePos, true);
  window.addEventListener('resize', updatePos);
  
  // Also update when field changes (e.g. dynamic resizing)
  const resizeObserver = new ResizeObserver(updatePos);
  resizeObserver.observe(field);

  // Clean up if field is removed
  const mutationObserver = new MutationObserver((mutations) => {
     if (!document.contains(field)) {
         icon.remove();
         window.removeEventListener('scroll', updatePos, true);
         window.removeEventListener('resize', updatePos);
         resizeObserver.disconnect();
         mutationObserver.disconnect();
     } else {
         updatePos();
     }
  });
  mutationObserver.observe(document.body, { childList: true, subtree: true });
}

let activeAutofillDropdown = null;

function showAutofillDropdown(credentials, targetField) {
  if (activeAutofillDropdown) {
    activeAutofillDropdown.remove();
    activeAutofillDropdown = null;
  }

  if (!targetField) return;

  const dropdown = document.createElement("div");
  dropdown.className = "vk-autofill-dropdown";
  const header = document.createElement("div");
  header.className = "vk-autofill-header";
  header.textContent = "VaultKeeper";
  dropdown.appendChild(header);
  credentials.forEach((cred) => {
    const item = document.createElement("div");
    item.className = "vk-autofill-item";
    const icon = document.createElement("div");
    icon.className = "vk-autofill-icon";
    const letter = document.createElement("span");
    letter.textContent = (cred.domain || "?").charAt(0).toUpperCase();
    icon.appendChild(letter);
    item.appendChild(icon);
    const text = document.createElement("div");
    text.className = "vk-autofill-text";

    const title = document.createElement("div");
    title.className = "vk-autofill-title";
    title.textContent = cred.domain;
    text.appendChild(title);

    const sub = document.createElement("div");
    sub.className = "vk-autofill-subtitle";
    sub.textContent = cred.username;
    text.appendChild(sub);

    item.appendChild(text);

    item.addEventListener("click", (e) => {
      e.stopPropagation();
      dropdown.remove();
      activeAutofillDropdown = null;
      
      const doFill = (code = null) => {
         fillCredentials(cred.username, cred.password, code);
         showNotification("Credentials filled!", "success");
      };

      if (cred.totp_secret || cred.id) { 
          browserAPI.runtime.sendMessage({ action: "get_totp", id: cred.id }, (resp) => {
               if(resp.success) {
                   doFill(resp.code);
               } else {
                   doFill(null);
               }
          });
      } else {
          doFill(null);
      }
    });

    dropdown.appendChild(item);
  });
  const rect = targetField.getBoundingClientRect();
  dropdown.style.top = rect.bottom + window.scrollY + 5 + "px";
  dropdown.style.left = rect.left + window.scrollX + "px";

  document.body.appendChild(dropdown);
  activeAutofillDropdown = dropdown;
  const closeListener = (e) => {
    if (!dropdown.contains(e.target) && e.target !== targetField) {
      dropdown.remove();
      activeAutofillDropdown = null;
      document.removeEventListener("click", closeListener);
    }
  };
  setTimeout(() => {
    document.addEventListener("click", closeListener);
  }, 100);
}

function requestCredentials(targetField = null, isFocus = false) {
  browserAPI.runtime.sendMessage(
    {
      action: "get_credentials",
      domain: currentDomain,
    },
    (response) => {
      if (
        response &&
        response.success &&
        response.credentials &&
        response.credentials.length > 0
      ) {
        const credentials = response.credentials;
        const count = credentials.length;

        if ((count > 1 || isFocus) && targetField) {
          showAutofillDropdown(credentials, targetField);
        } else {
          const cred = credentials[0];
          
          const performFill = (totpCode = null) => {
             const filled = fillCredentials(cred.username, cred.password, totpCode);

             if (filled) {
                if (detectedFields?.isMultiStep) {
                  if (detectedFields.username && !detectedFields.password) {
                    showNotification("Email/username filled!", "success");
                  } else if (detectedFields.password && !detectedFields.username) {
                    showNotification("Password filled!", "success");
                  } else {
                    showNotification("Credentials filled!", "success");
                  }
                } else {
                  showNotification("Credentials filled!", "success");
                }
             } else {
               showNotification("Could not fill credentials", "error");
             }
          };

          if (cred.totp_secret || cred.id) {
               browserAPI.runtime.sendMessage({ action: "get_totp", id: cred.id }, (resp) => {
                   if(resp.success) {
                        performFill(resp.code);
                   } else {
                        performFill(null);
                   }
               });
          } else {
               performFill(null);
          }
        }
      } else if (response && response.locked) {
        if (!isFocus) {
          showUnlockAndFillPrompt(targetField);
        } else {
        }
      } else {
        if (!isFocus) showNotification("No credentials found", "error");
      }
    },
  );
}

function init() {
  const pendingData = getPendingCredentials();
  if (pendingData && pendingData.credentials) {
    pendingCredentials = pendingData.credentials;
    existingCredentialId = pendingData.credentialId;
    savePromptShown = true;
    setTimeout(() => {
      displaySavePrompt(pendingData.credentials, pendingData.isUpdate);
    }, 300);
  }

  detectedFields = detectLoginFields();
  if (detectedFields && (detectedFields.username || detectedFields.password)) {
    const fieldType =
      detectedFields.password && detectedFields.username
        ? "standard"
        : detectedFields.password
          ? "password-only"
          : "username-only";
    if (detectedFields.password) {
      document
        .querySelectorAll('input[type="password"]')
        .forEach(addVaultKeeperIcon);
    }
    if (
      detectedFields.isMultiStep &&
      detectedFields.username &&
      !detectedFields.password
    ) {
      addVaultKeeperIconToUsername(detectedFields.username);
    }

    setupFormInterception();
  }
  
  // Always search for TOTP fields regardless of login detection
  for (const selector of TOTP_SELECTORS) {
      document.querySelectorAll(selector).forEach(field => {
          if (isVisible(field)) {
              addVaultKeeperIcon(field);
          }
      });
  }
}

function addVaultKeeperIconToUsername(field) {
  if (field.dataset.vaultkeeperIcon) return;
  field.dataset.vaultkeeperIcon = "true";

  const icon = document.createElement("div");
  icon.className = "vaultkeeper-field-icon";

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("width", "16");
  svg.setAttribute("height", "16");
  svg.setAttribute("fill", "none");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("stroke-width", "2");

  const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  rect.setAttribute("x", "3");
  rect.setAttribute("y", "11");
  rect.setAttribute("width", "18");
  rect.setAttribute("height", "11");
  rect.setAttribute("rx", "2");
  svg.appendChild(rect);

  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", "M7 11V7a5 5 0 0 1 10 0v4");
  svg.appendChild(path);

  icon.appendChild(svg);
  icon.title = "VaultKeeper - Fill credential";

  icon.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    requestCredentials(field);
  });
  field.addEventListener("focus", () => {
    if (document.activeElement === field) {
      requestCredentials(field, true);
    }
  });

  if (field.parentElement) {
    field.parentElement.style.position = "relative";
    field.parentElement.appendChild(icon);
  }
}

browserAPI.runtime.onMessage.addListener((request, sender, sendResponse) => {
  switch (request.action) {
    case "fill":
      detectedFields = detectLoginFields();
      const success = fillCredentials(request.username, request.password, request.totp);
      sendResponse({
        success,
        isMultiStep: detectedFields?.isMultiStep || false,
      });
      break;
    case "fill_password_only":
      detectedFields = detectLoginFields();
      let passwordFilled = false;
      if (detectedFields && detectedFields.password) {
        setFieldValue(detectedFields.password, request.password);
        passwordFilled = true;
      }
      sendResponse({ success: passwordFilled });
      break;
    case "detect":
      detectedFields = detectLoginFields();
      sendResponse({
        hasForm: !!(detectedFields?.username || detectedFields?.password),
        hasPassword: !!detectedFields?.password,
        hasUsername: !!detectedFields?.username,
        isMultiStep: detectedFields?.isMultiStep || false,
        domain: currentDomain,
      });
      break;
    case "fill_card":
      const cardFilled = fillCreditCard(
        request.card_number,
        request.expiry_date,
        request.cvv,
        request.cardholder_name,
      );
      sendResponse({ success: cardFilled });
      break;
  }
  return true;
});

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
const observer = new MutationObserver(() => {
  const newFields = detectLoginFields();
  if (newFields) {
    const hasNewPassword = newFields.password && !detectedFields?.password;
    const hasNewUsername = newFields.username && !detectedFields?.username;

    if (hasNewPassword || hasNewUsername) {
      detectedFields = newFields;

      if (newFields.password) {
        document
          .querySelectorAll('input[type="password"]')
          .forEach(addVaultKeeperIcon);
      }

      if (newFields.isMultiStep && newFields.username && !newFields.password) {
        addVaultKeeperIconToUsername(newFields.username);
      }

      setupFormInterception();
    }
  }
  
  // Independent TOTP check on mutation
  for (const selector of TOTP_SELECTORS) {
      document.querySelectorAll(selector).forEach(field => {
          if (isVisible(field)) {
               addVaultKeeperIcon(field);
          }
      });
  }
});

observer.observe(document.body, {
  childList: true,
  subtree: true,
});
