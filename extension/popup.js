const browserAPI = typeof browser !== "undefined" ? browser : chrome;

let currentCredentials = [];
let selectedCredential = null;
let actualPasswords = {};

const loadingView = document.getElementById("loading-view");
const lockedView = document.getElementById("locked-view");
const unlockedView = document.getElementById("unlocked-view");
const disconnectedView = document.getElementById("disconnected-view");
const setupView = document.getElementById("setup-view");
const modal = document.getElementById("modal");

const masterPasswordInput = document.getElementById("master-password");
const errorMessage = document.getElementById("error-message");
const unlockBtn = document.getElementById("unlock-btn");
const lockBtn = document.getElementById("lock-btn");
const addBtn = document.getElementById("add-btn");
const retryBtn = document.getElementById("retry-btn");

const searchInput = document.getElementById("search-input");
const credentialsList = document.getElementById("credentials-list");
const credentialCount = document.getElementById("credential-count");

const emptyState = document.getElementById("empty-state");
const detailContent = document.getElementById("detail-content");
const detailFavicon = document.getElementById("detail-favicon");
const detailTitle = document.getElementById("detail-title");
const detailUsername = document.getElementById("detail-username");
const detailPassword = document.getElementById("detail-password");
const detailUrl = document.getElementById("detail-url");
const fillBtn = document.getElementById("fill-btn");
const togglePasswordBtn = document.getElementById("toggle-password");

const credentialForm = document.getElementById("credential-form");
const modalTitle = document.getElementById("modal-title");
const modalClose = document.getElementById("modal-close");
const cancelBtn = document.getElementById("cancel-btn");
const generateBtn = document.getElementById("generate-btn");
const toggleBtn = document.getElementById("toggle-btn");
const credDomain = document.getElementById("cred-domain");
const credUsername = document.getElementById("cred-username");
const credPassword = document.getElementById("cred-password");
const credNotes = document.getElementById("cred-notes");
const strengthBadge = document.querySelector(".strength-badge");

function showView(viewId) {
  [loadingView, lockedView, unlockedView, disconnectedView, setupView].forEach(
    (v) => {
      if (v) v.classList.add("hidden");
    },
  );
  const view = document.getElementById(viewId);
  if (view) view.classList.remove("hidden");
}

function sendMessage(message) {
  return new Promise((resolve, reject) => {
    browserAPI.runtime.sendMessage(message, (response) => {
      if (browserAPI.runtime.lastError) {
        reject(new Error(browserAPI.runtime.lastError.message));
      } else {
        resolve(response);
      }
    });
  });
}

let checkInterval = null;

async function checkStatus() {
  try {
    const response = await sendMessage({ action: "status" });

    if (!response.success) {
      showView("disconnected-view");
      return;
    }

    // Stop checking if we are connected and good
    if (checkInterval && (response.unlocked || !response.first_run)) {
      clearInterval(checkInterval);
      checkInterval = null;
    }

    if (response.first_run) {
      showView("setup-view");

      // Start polling if not already polling
      if (!checkInterval) {
        checkInterval = setInterval(checkStatus, 2000);
      }
      return;
    }

    if (response.unlocked) {
      showView("unlocked-view");
      loadCredentials();
    } else {
      showView("locked-view");
    }
  } catch (error) {
    showView("disconnected-view");
  }
}

async function unlock() {
  const password = masterPasswordInput.value;

  if (!password) {
    showError("Enter your master password");
    return;
  }

  try {
    unlockBtn.disabled = true;
    unlockBtn.textContent = "Unlocking...";

    const response = await sendMessage({ action: "unlock", password });

    if (response.success) {
      masterPasswordInput.value = "";
      hideError();
      showView("unlocked-view");
      loadCredentials();
    } else {
      showError(response.error || "Incorrect password");
    }
  } catch (error) {
    showError("Connection error");
  } finally {
    unlockBtn.disabled = false;
    unlockBtn.textContent = "Unlock";
  }
}

async function lock() {
  try {
    await sendMessage({ action: "lock" });
    selectedCredential = null;
    currentCredentials = [];
    showView("locked-view");
  } catch (error) {}
}

async function loadCredentials() {
  try {
    const response = await sendMessage({ action: "get_all_credentials" });

    if (response.success) {
      currentCredentials = response.credentials || [];

      actualPasswords = {};
      currentCredentials.forEach((cred) => {
        actualPasswords[cred.id] = cred.password;
      });

      currentCredentials.sort((a, b) => a.domain.localeCompare(b.domain));

      renderCredentials();
      updateCredentialCount();

      if (currentCredentials.length > 0 && !selectedCredential) {
        selectCredential(currentCredentials[0]);
      }
    }
  } catch (error) {}
}

function renderCredentials(filter = "") {
  credentialsList.innerHTML = "";

  const filtered = currentCredentials.filter(
    (cred) =>
      cred.domain.toLowerCase().includes(filter.toLowerCase()) ||
      cred.username.toLowerCase().includes(filter.toLowerCase()),
  );

  if (filtered.length === 0) {
    credentialsList.innerHTML = `
            <div class="empty-list">
                <div class="empty-list-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M21 8v13H3V8"/>
                        <path d="M1 3h22v5H1z"/>
                        <path d="M10 12h4"/>
                    </svg>
                </div>
                <p>${filter ? "No results" : "No credentials yet"}</p>
            </div>
        `;
    return;
  }

  filtered.forEach((cred) => {
    const item = createCredentialItem(cred);
    credentialsList.appendChild(item);
  });
}

function createCredentialItem(cred) {
  const item = document.createElement("div");
  item.className = "credential-item";
  item.dataset.id = cred.id;

  if (selectedCredential && selectedCredential.id === cred.id) {
    item.classList.add("selected");
  }

  const faviconUrl = `https://www.google.com/s2/favicons?domain=${cred.domain}&sz=32`;

  // Create favicon with proper fallback
  const faviconDiv = document.createElement("div");
  faviconDiv.className = "credential-favicon";
  const faviconImg = document.createElement("img");
  faviconImg.src = faviconUrl;
  faviconImg.onerror = function () {
    this.style.display = "none";
    const fallback = document.createElement("div");
    fallback.className = "fallback-icon";
    fallback.innerHTML =
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>';
    this.parentElement.appendChild(fallback);
  };
  faviconDiv.appendChild(faviconImg);

  const infoDiv = document.createElement("div");
  infoDiv.className = "credential-info";
  infoDiv.innerHTML = `
        <div class="credential-domain">${escapeHtml(getDomainDisplay(cred.domain))}</div>
        <div class="credential-username">${escapeHtml(cred.username)}</div>
    `;

  item.appendChild(faviconDiv);
  item.appendChild(infoDiv);

  item.addEventListener("click", () => selectCredential(cred));

  return item;
}

function getDomainDisplay(domain) {
  let display = domain.replace(/^(https?:\/\/)?(www\.)?/, "");
  display = display.split("/")[0];
  return display.charAt(0).toUpperCase() + display.slice(1);
}

function selectCredential(cred) {
  selectedCredential = cred;

  document.querySelectorAll(".credential-item").forEach((item) => {
    item.classList.remove("selected");
    if (item.dataset.id == cred.id) {
      item.classList.add("selected");
    }
  });

  emptyState.classList.add("hidden");
  detailContent.classList.remove("hidden");

  // Create favicon with proper fallback
  const faviconUrl = `https://www.google.com/s2/favicons?domain=${cred.domain}&sz=64`;
  detailFavicon.innerHTML = "";
  const faviconImg = document.createElement("img");
  faviconImg.className = "detail-favicon-img";
  faviconImg.src = faviconUrl;
  faviconImg.onerror = function () {
    this.style.display = "none";
    const fallback = document.createElement("div");
    fallback.className = "fallback-icon";
    fallback.innerHTML =
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>';
    this.parentElement.appendChild(fallback);
  };
  detailFavicon.appendChild(faviconImg);

  detailTitle.textContent = getDomainDisplay(cred.domain);
  detailUsername.textContent = cred.username;
  detailPassword.textContent = "••••••••••";

  // Update strength badge
  const password = actualPasswords[cred.id] || "";
  updateStrengthBadge(password);
  detailPassword.classList.add("password-masked");
  detailPassword.dataset.visible = "false";

  let url = cred.domain;
  if (!url.startsWith("http")) {
    url = "https://" + url;
  }
  detailUrl.textContent = url;
  detailUrl.href = url;
}

function toggleDetailPassword() {
  if (!selectedCredential) return;

  const isVisible = detailPassword.dataset.visible === "true";

  if (isVisible) {
    detailPassword.textContent = "••••••••••";
    detailPassword.classList.add("password-masked");
    detailPassword.dataset.visible = "false";
  } else {
    detailPassword.textContent = actualPasswords[selectedCredential.id] || "";
    detailPassword.classList.remove("password-masked");
    detailPassword.dataset.visible = "true";
  }
}

async function fillCredential() {
  if (!selectedCredential) return;

  try {
    const [tab] = await browserAPI.tabs.query({
      active: true,
      currentWindow: true,
    });

    await browserAPI.tabs.sendMessage(tab.id, {
      action: "fill",
      username: selectedCredential.username,
      password: actualPasswords[selectedCredential.id] || "",
    });

    window.close();
  } catch (error) {}
}

async function copyToClipboard(type) {
  if (!selectedCredential) return;

  let text = "";
  switch (type) {
    case "username":
      text = selectedCredential.username;
      break;
    case "password":
      text = actualPasswords[selectedCredential.id] || "";
      break;
    case "url":
      text = selectedCredential.domain;
      break;
  }

  try {
    await navigator.clipboard.writeText(text);

    const btn = document.querySelector(`[data-copy="${type}"]`);
    if (btn) {
      const originalHTML = btn.innerHTML;
      btn.innerHTML = "✓";
      setTimeout(() => (btn.innerHTML = originalHTML), 1500);
    }

    if (type === "password") {
      setTimeout(async () => {
        try {
          const current = await navigator.clipboard.readText();
          if (current === text) {
            await navigator.clipboard.writeText("");
          }
        } catch (e) {}
      }, 30000);
    }
  } catch (error) {}
}

function updateCredentialCount() {
  credentialCount.textContent = currentCredentials.length;
}

function openAddModal() {
  modalTitle.textContent = "New Item";
  credentialForm.reset();
  updateStrengthBadge("");

  browserAPI.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      try {
        const url = new URL(tabs[0].url);
        credDomain.value = url.hostname;
      } catch (e) {}
    }
  });

  modal.classList.remove("hidden");
}

function closeModal() {
  modal.classList.add("hidden");
  credentialForm.reset();
  delete credentialForm.dataset.editId;
}

async function saveCredential(e) {
  e.preventDefault();

  const data = {
    domain: credDomain.value.trim(),
    username: credUsername.value.trim(),
    password: credPassword.value,
    notes: credNotes.value.trim() || null,
  };

  if (!data.domain || !data.username || !data.password) {
    return;
  }

  try {
    const response = await sendMessage({
      action: "save_credentials",
      ...data,
    });

    if (response.success) {
      closeModal();
      await loadCredentials();
    } else {
      alert(response.error || "Save failed");
    }
  } catch (error) {
    alert("Error saving credential");
  }
}

function updateStrengthBadge(password) {
  if (!password) {
    strengthBadge.textContent = "Empty";
    strengthBadge.className = "strength-badge";
    strengthBadge.style.backgroundColor = "#d1d5db"; // gray-300
    strengthBadge.style.color = "#374151"; // gray-700
    return;
  }

  const analysis = analyzePassword(password);

  strengthBadge.textContent = analysis.label;
  strengthBadge.className = "strength-badge"; // reset classes
  strengthBadge.style.backgroundColor = analysis.color;
  strengthBadge.style.color = "#fff"; // White text for colored badges

  // Add specific class based on label for potential CSS styling
  strengthBadge.classList.add(analysis.label.toLowerCase());
}

function generatePassword() {
  const chars =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*";
  const length = 16;

  // Use crypto.getRandomValues for cryptographically secure random numbers
  const randomValues = new Uint32Array(length);
  crypto.getRandomValues(randomValues);

  let password = "";
  for (let i = 0; i < length; i++) {
    password += chars.charAt(randomValues[i] % chars.length);
  }

  credPassword.value = password;
  credPassword.type = "text";

  updateStrengthBadge(password);
}

function toggleModalPassword() {
  credPassword.type = credPassword.type === "password" ? "text" : "password";
}

function showError(message) {
  errorMessage.textContent = message;
  errorMessage.classList.remove("hidden");
}

function hideError() {
  errorMessage.classList.add("hidden");
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

unlockBtn.addEventListener("click", unlock);
masterPasswordInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") unlock();
});

lockBtn.addEventListener("click", lock);
addBtn.addEventListener("click", openAddModal);
retryBtn.addEventListener("click", checkStatus);

searchInput.addEventListener("input", (e) => {
  renderCredentials(e.target.value);
});

fillBtn.addEventListener("click", fillCredential);
togglePasswordBtn.addEventListener("click", toggleDetailPassword);

document.querySelectorAll(".copy-btn").forEach((btn) => {
  btn.addEventListener("click", () => copyToClipboard(btn.dataset.copy));
});

modalClose.addEventListener("click", closeModal);
cancelBtn.addEventListener("click", closeModal);
credentialForm.addEventListener("submit", saveCredential);
generateBtn.addEventListener("click", generatePassword);
toggleBtn.addEventListener("click", toggleModalPassword);

modal.querySelector(".modal-backdrop").addEventListener("click", closeModal);

// Menu button (3 dots) functionality
const menuBtn = document.getElementById("menu-btn");
let activeDropdown = null;

function createDropdownMenu() {
  // Remove existing dropdown if any
  const existing = document.querySelector(".vk-dropdown-menu");
  if (existing) existing.remove();

  const dropdown = document.createElement("div");
  dropdown.className = "vk-dropdown-menu";
  dropdown.innerHTML = `
        <button class="vk-dropdown-item" data-action="edit">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg>
            Edit
        </button>
        <button class="vk-dropdown-item" data-action="favorite">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
            </svg>
            Toggle Favorite
        </button>
        <div class="vk-dropdown-divider"></div>
        <button class="vk-dropdown-item danger" data-action="delete">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
            Delete
        </button>
    `;

  return dropdown;
}

function showDropdownMenu(e) {
  e.stopPropagation();

  if (!selectedCredential) return;

  // Close existing dropdown
  closeDropdownMenu();

  const dropdown = createDropdownMenu();
  document.body.appendChild(dropdown);
  activeDropdown = dropdown;

  // Position dropdown
  const btnRect = menuBtn.getBoundingClientRect();
  dropdown.style.position = "fixed";
  dropdown.style.top = `${btnRect.bottom + 4}px`;
  dropdown.style.right = `${window.innerWidth - btnRect.right}px`;

  // Add click handlers
  dropdown.querySelectorAll(".vk-dropdown-item").forEach((item) => {
    item.addEventListener("click", (e) => {
      e.stopPropagation();
      handleMenuAction(item.dataset.action);
      closeDropdownMenu();
    });
  });

  // Close on click outside
  setTimeout(() => {
    document.addEventListener("click", closeDropdownMenu, { once: true });
  }, 0);
}

function closeDropdownMenu() {
  if (activeDropdown) {
    activeDropdown.remove();
    activeDropdown = null;
  }
}

async function handleMenuAction(action) {
  if (!selectedCredential) return;

  switch (action) {
    case "edit":
      openEditModal(selectedCredential);
      break;
    case "favorite":
      await toggleFavorite(selectedCredential.id);
      break;
    case "delete":
      await deleteCredential(selectedCredential.id);
      break;
  }
}

function openEditModal(cred) {
  modalTitle.textContent = "Edit Item";
  credDomain.value = cred.domain;
  credUsername.value = cred.username;
  credPassword.value = actualPasswords[cred.id] || "";
  credNotes.value = cred.notes || "";

  updateStrengthBadge(credPassword.value);

  // Store the editing credential ID
  credentialForm.dataset.editId = cred.id;

  modal.classList.remove("hidden");
}

async function toggleFavorite(id) {
  try {
    const response = await sendMessage({ action: "toggle_favorite", id });
    if (response.success) {
      // Find the credential to check new state
      const cred = credentials.find((c) => c.id === id);
      const newState = cred ? !cred.is_favorite : true;

      // Show feedback notification
      showPopupNotification(
        newState ? "Added to favorites" : "Removed from favorites",
        "success",
      );

      await loadCredentials();
    }
  } catch (error) {
    showPopupNotification("Failed to update favorite", "error");
  }
}

// Show notification in popup
function showPopupNotification(message, type = "success") {
  // Remove existing notification
  const existing = document.querySelector(".popup-notification");
  if (existing) existing.remove();

  const notification = document.createElement("div");
  notification.className = `popup-notification ${type}`;
  notification.innerHTML = `
        <span class="popup-notification-icon">
            ${
              type === "success"
                ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>'
                : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/></svg>'
            }
        </span>
        <span>${escapeHtml(message)}</span>
    `;

  document.body.appendChild(notification);

  // Auto remove after 2 seconds
  setTimeout(() => {
    notification.classList.add("fade-out");
    setTimeout(() => notification.remove(), 300);
  }, 2000);
}

async function deleteCredential(id) {
  if (!confirm("Are you sure you want to delete this credential?")) return;

  try {
    const response = await sendMessage({ action: "delete_credentials", id });
    if (response.success) {
      showPopupNotification("Credential deleted", "success");
      selectedCredential = null;
      emptyState.classList.remove("hidden");
      detailContent.classList.add("hidden");
      await loadCredentials();
    }
  } catch (error) {
    showPopupNotification("Failed to delete credential", "error");
  }
}

// Update saveCredential to handle edit mode
const originalSaveCredential = saveCredential;
async function saveCredentialWithEdit(e) {
  e.preventDefault();

  const editId = credentialForm.dataset.editId;

  const data = {
    domain: credDomain.value.trim(),
    username: credUsername.value.trim(),
    password: credPassword.value,
    notes: credNotes.value.trim() || null,
  };

  if (!data.domain || !data.username || !data.password) {
    return;
  }

  try {
    let response;
    if (editId) {
      // Update existing
      response = await sendMessage({
        action: "update_credentials",
        id: parseInt(editId),
        ...data,
      });
    } else {
      // Create new
      response = await sendMessage({
        action: "save_credentials",
        ...data,
      });
    }

    if (response.success) {
      closeModal();
      delete credentialForm.dataset.editId;
      await loadCredentials();
    } else {
      alert(response.error || "Save failed");
    }
  } catch (error) {
    alert("Error saving credential");
  }
}

// Override the form submit handler
credentialForm.removeEventListener("submit", saveCredential);
credentialForm.addEventListener("submit", saveCredentialWithEdit);

credPassword.addEventListener("input", (e) => {
  updateStrengthBadge(e.target.value);
});

// Add menu button listener
menuBtn.addEventListener("click", showDropdownMenu);

document.addEventListener("DOMContentLoaded", checkStatus);
