
const browserAPI = typeof browser !== 'undefined' ? browser : chrome;

let detectedFields = null;
let currentDomain = window.location.hostname;
let pendingCredentials = null;
let savePromptShown = false;
let promptTimeoutId = null;
let existingCredentialId = null; 

const MULTISTEP_STORAGE_KEY = 'vaultkeeper_multistep_';

const PENDING_CREDENTIALS_KEY = 'vaultkeeper_pending_credentials';

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
    'input[type="text"]'
];

const PASSWORD_SELECTORS = [
    'input[type="password"]',
    'input[autocomplete="current-password"]',
    'input[autocomplete="new-password"]'
];


// === MULTI-STEP LOGIN SUPPORT ===

/**
 * Get the base domain for storage key (handles subdomains)
 */
function getBaseDomain() {
    const parts = currentDomain.split('.');
    if (parts.length > 2) {
        // Handle cases like accounts.firefox.com -> firefox.com
        return parts.slice(-2).join('.');
    }
    return currentDomain;
}

/**
 * Store username for multi-step login
 */
function storeMultiStepUsername(username) {
    if (!username) return;
    const key = MULTISTEP_STORAGE_KEY + getBaseDomain();
    const data = {
        username: username,
        timestamp: Date.now(),
        originalDomain: currentDomain
    };
    sessionStorage.setItem(key, JSON.stringify(data));
}

/**
 * Retrieve username from previous step (valid for 5 minutes)
 */
function getMultiStepUsername() {
    const key = MULTISTEP_STORAGE_KEY + getBaseDomain();
    try {
        const stored = sessionStorage.getItem(key);
        if (!stored) return null;
        
        const data = JSON.parse(stored);
        const age = Date.now() - data.timestamp;
        
        // Valid for 5 minutes
        if (age > 5 * 60 * 1000) {
            sessionStorage.removeItem(key);
            return null;
        }
        
        return data.username;
    } catch (e) {
        return null;
    }
}

/**
 * Clear stored multi-step username
 */
function clearMultiStepUsername() {
    const key = MULTISTEP_STORAGE_KEY + getBaseDomain();
    sessionStorage.removeItem(key);
}

/**
 * Store pending credentials for persistence across navigations
 */
function storePendingCredentials(credentials, isUpdate = false, credentialId = null) {
    const data = {
        credentials: credentials,
        isUpdate: isUpdate,
        credentialId: credentialId,
        timestamp: Date.now()
    };
    sessionStorage.setItem(PENDING_CREDENTIALS_KEY, JSON.stringify(data));
}

/**
 * Retrieve pending credentials (valid for 30 seconds)
 */
function getPendingCredentials() {
    try {
        const stored = sessionStorage.getItem(PENDING_CREDENTIALS_KEY);
        if (!stored) return null;
        
        const data = JSON.parse(stored);
        const age = Date.now() - data.timestamp;
        
        // Valid for 30 seconds
        if (age > 30 * 1000) {
            clearPendingCredentials();
            return null;
        }
        
        return data;
    } catch (e) {
        return null;
    }
}

/**
 * Clear stored pending credentials
 */
function clearPendingCredentials() {
    sessionStorage.removeItem(PENDING_CREDENTIALS_KEY);
}

/**
 * Check if a credential with the same username already exists for this domain
 */
async function checkExistingCredential(domain, username) {
    return new Promise((resolve) => {
        browserAPI.runtime.sendMessage({
            action: 'get_credentials',
            domain: domain
        }, (response) => {
            if (response && response.success && response.credentials) {
                // Find a credential with the same username
                const existing = response.credentials.find(
                    cred => cred.username.toLowerCase() === username.toLowerCase()
                );
                resolve(existing || null);
            } else {
                resolve(null);
            }
        });
    });
}


/**
 * Detect login fields - supports both full forms and multi-step login
 * Returns fields even if only username OR only password is found
 */
function detectLoginFields() {
    const fields = {
        username: null,
        password: null,
        form: null,
        isMultiStep: false
    };
    
    // First, try to find a password field
    for (const selector of PASSWORD_SELECTORS) {
        const passwordFields = document.querySelectorAll(selector);
        for (const field of passwordFields) {
            if (isVisible(field)) {
                fields.password = field;
                fields.form = field.closest('form');
                break;
            }
        }
        if (fields.password) break;
    }
    
    // Search for username field
    const searchContainer = fields.form || document;
    
    for (const selector of USERNAME_SELECTORS) {
        const candidates = searchContainer.querySelectorAll(selector);
        for (const candidate of candidates) {
            if (!isVisible(candidate)) continue;
            if (candidate === fields.password) continue;
            
            // If we have a password field, prefer username that comes before it
            if (fields.password) {
                if (fields.password.compareDocumentPosition(candidate) & Node.DOCUMENT_POSITION_PRECEDING) {
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
    
    // Determine if this is a multi-step login scenario
    if (fields.password && !fields.username) {
        // Password field visible but no username - likely step 2 of multi-step login
        fields.isMultiStep = true;
    } else if (fields.username && !fields.password) {
        // Only username visible - likely step 1 of multi-step login
        fields.isMultiStep = true;
        fields.form = fields.username.closest('form');
    }
    
    // Return fields if we have at least one field
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
        style.visibility !== 'hidden' &&
        style.display !== 'none' &&
        style.opacity !== '0'
    );
}


function fillCredentials(username, password) {
    if (!detectedFields) {
        detectedFields = detectLoginFields();
    }
    
    if (!detectedFields || (!detectedFields.username && !detectedFields.password)) {
        return false;
    }
    
    let filled = false;
    
    // Multi-step login: only username field visible
    if (detectedFields.username && !detectedFields.password) {
        if (username) {
            setFieldValue(detectedFields.username, username);
            // Store username for the password step
            storeMultiStepUsername(username);
            filled = true;
        }
    }
    // Multi-step login: only password field visible
    else if (detectedFields.password && !detectedFields.username) {
        if (password) {
            setFieldValue(detectedFields.password, password);
            filled = true;
        }
    }
    // Traditional login: both fields visible
    else {
        if (detectedFields.username && username) {
            setFieldValue(detectedFields.username, username);
            filled = true;
        }
        
        if (detectedFields.password && password) {
            setFieldValue(detectedFields.password, password);
            filled = true;
        }
        
        if (filled) {
        }
    }
    
    return filled;
}


function setFieldValue(field, value) {
    field.focus();
    field.value = value;
    
    field.dispatchEvent(new Event('input', { bubbles: true }));
    field.dispatchEvent(new Event('change', { bubbles: true }));
    field.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true }));
    field.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
    
    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    nativeInputValueSetter.call(field, value);
    field.dispatchEvent(new Event('input', { bubbles: true }));
}


function captureCredentials(form) {
    const passwordField = form.querySelector('input[type="password"]');
    
    // Try to find username in the current form
    let username = '';
    for (const selector of USERNAME_SELECTORS) {
        const field = form.querySelector(selector);
        if (field && field !== passwordField && field.value) {
            username = field.value;
            break;
        }
    }
    
    // CASE 1: Standard login - both username and password in the form
    if (passwordField && passwordField.value && username) {
        clearMultiStepUsername(); // Clear any stored username
        return {
            domain: currentDomain,
            username: username,
            password: passwordField.value
        };
    }
    
    // CASE 2: Multi-step login - password step (no username in form)
    if (passwordField && passwordField.value && !username) {
        // Try to get username from previous step
        const storedUsername = getMultiStepUsername();
        if (storedUsername) {
            clearMultiStepUsername(); // Clear after use
            return {
                domain: currentDomain,
                username: storedUsername,
                password: passwordField.value
            };
        }
    }
    
    // CASE 3: Multi-step login - username step (store for later)
    if (!passwordField && username) {
        storeMultiStepUsername(username);
        return null; // Don't prompt yet, wait for password
    }
    
    return null;
}

/**
 * Capture username from any visible input field (for multi-step detection)
 */
function captureVisibleUsername() {
    for (const selector of USERNAME_SELECTORS) {
        const fields = document.querySelectorAll(selector);
        for (const field of fields) {
            if (isVisible(field) && field.value && field.type !== 'password') {
                return field.value;
            }
        }
    }
    return null;
}


function createSavePrompt(isUpdateMode = false, showUnlockForm = false) {
    const existing = document.getElementById('vaultkeeper-save-prompt');
    if (existing) existing.remove();
    
    const lockSvg = `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>`;
    
    const title = showUnlockForm ? 'Unlock VaultKeeper' : (isUpdateMode ? 'Update password?' : 'Save this password?');
    const buttonText = isUpdateMode ? 'Update Password' : 'Save Password';
    const showNeverButton = !isUpdateMode && !showUnlockForm;
    
    // Build the unlock form HTML if needed
    const unlockFormHtml = showUnlockForm ? `
        <div class="vk-unlock-section" id="vk-unlock-section">
            <p class="vk-unlock-message">Enter your master password to save credentials</p>
            <div class="vk-input-group">
                <input type="password" id="vk-master-password" class="vk-input" placeholder="Master Password" autofocus>
            </div>
            <p id="vk-unlock-error" class="vk-error hidden"></p>
        </div>
    ` : '';
    
    // Build credential preview (hidden when showing unlock form)
    const credentialPreviewHtml = !showUnlockForm ? `
        <div class="vk-credential-preview">
            <div class="vk-cred-row">
                <span class="vk-cred-label">Website</span>
                <span class="vk-cred-value" id="vk-domain">${currentDomain}</span>
            </div>
            <div class="vk-cred-row">
                <span class="vk-cred-label">Username</span>
                <span class="vk-cred-value" id="vk-username">-</span>
            </div>
            <div class="vk-cred-row">
                <span class="vk-cred-label">Password</span>
                <span class="vk-cred-value">••••••••</span>
            </div>
        </div>
    ` : '';
    
    // Build action buttons
    let actionsHtml = '';
    if (showUnlockForm) {
        actionsHtml = `
            <button class="vk-btn vk-btn-secondary" id="vk-cancel">Cancel</button>
            <button class="vk-btn vk-btn-primary" id="vk-unlock">Unlock & Save</button>
        `;
    } else {
        actionsHtml = `
            ${showNeverButton ? '<button class="vk-btn vk-btn-secondary" id="vk-never">Never for this site</button>' : '<button class="vk-btn vk-btn-secondary" id="vk-cancel">Cancel</button>'}
            <button class="vk-btn vk-btn-primary" id="vk-save">${buttonText}</button>
        `;
    }
    
    const prompt = document.createElement('div');
    prompt.id = 'vaultkeeper-save-prompt';
    prompt.innerHTML = `
        <div class="vk-prompt-overlay"></div>
        <div class="vk-prompt-container">
            <div class="vk-prompt-header">
                <span class="vk-prompt-icon">${lockSvg}</span>
                <span class="vk-prompt-title">VaultKeeper</span>
                <button class="vk-close-btn" id="vk-close">&times;</button>
            </div>
            <div class="vk-prompt-body">
                <p class="vk-prompt-message">${title}</p>
                ${unlockFormHtml}
                ${credentialPreviewHtml}
            </div>
            <div class="vk-prompt-actions">
                ${actionsHtml}
            </div>
        </div>
    `;
    
    document.body.appendChild(prompt);
    
    return prompt;
}


async function showSavePrompt(credentials) {
    if (savePromptShown) return;
    
    // Check if a credential with the same username already exists for this domain
    const existingCred = await checkExistingCredential(credentials.domain, credentials.username);
    
    let isUpdateMode = false;
    
    if (existingCred) {
        // Check if password is different
        if (existingCred.password === credentials.password) {
            // Same password, no need to prompt
            return;
        }
        // Different password, prompt to update
        isUpdateMode = true;
        existingCredentialId = existingCred.id;
    }
    
    savePromptShown = true;
    pendingCredentials = credentials;
    
    // Store for persistence across navigations
    storePendingCredentials(credentials, isUpdateMode, existingCredentialId);
    
    displaySavePrompt(credentials, isUpdateMode);
}


function displaySavePrompt(credentials, isUpdateMode = false) {
    const prompt = createSavePrompt(isUpdateMode);
    
    document.getElementById('vk-domain').textContent = credentials.domain;
    document.getElementById('vk-username').textContent = credentials.username;
    
    // Set up 30-second auto-dismiss timeout
    if (promptTimeoutId) {
        clearTimeout(promptTimeoutId);
    }
    promptTimeoutId = setTimeout(() => {
        hidePrompt();
    }, 30000);
    
    document.getElementById('vk-save').addEventListener('click', () => {
        if (isUpdateMode && existingCredentialId) {
            updateCredentials(credentials, existingCredentialId);
        } else {
            saveCredentials(credentials);
        }
        hidePrompt();
    });
    
    const neverBtn = document.getElementById('vk-never');
    if (neverBtn) {
        neverBtn.addEventListener('click', () => {
            const neverSave = JSON.parse(localStorage.getItem('vaultkeeper_never_save') || '[]');
            neverSave.push(currentDomain);
            localStorage.setItem('vaultkeeper_never_save', JSON.stringify(neverSave));
            hidePrompt();
        });
    }
    
    const cancelBtn = document.getElementById('vk-cancel');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', hidePrompt);
    }
    
    document.getElementById('vk-close').addEventListener('click', hidePrompt);
    
    // Note: Overlay click no longer closes the prompt
    // This prevents accidental dismissal during page navigation
}


function hidePrompt() {
    // Clear the timeout
    if (promptTimeoutId) {
        clearTimeout(promptTimeoutId);
        promptTimeoutId = null;
    }
    
    const prompt = document.getElementById('vaultkeeper-save-prompt');
    if (prompt) {
        prompt.style.animation = 'vk-fade-out 0.2s ease forwards';
        setTimeout(() => prompt.remove(), 200);
    }
    savePromptShown = false;
    pendingCredentials = null;
    existingCredentialId = null;
    
    // Clear stored pending credentials
    clearPendingCredentials();
}


async function saveCredentials(credentials) {
    try {
        const response = await browserAPI.runtime.sendMessage({
            action: 'save_credentials',
            domain: credentials.domain,
            username: credentials.username,
            password: credentials.password
        });
        
        if (response && response.success) {
            showNotification('Password saved!', 'success');
        } else if (response && (response.locked || response.error?.includes('locked') || response.error?.includes('Vault'))) {
            // Vault is locked - show unlock form
            showUnlockPrompt(credentials, false);
        } else {
            showNotification('Failed to save password', 'error');
        }
    } catch (error) {
        // Check if it's a locked vault error
        if (error.message?.includes('locked') || error.message?.includes('Vault')) {
            showUnlockPrompt(credentials, false);
        } else {
            showNotification('Connection error', 'error');
        }
    }
}


async function updateCredentials(credentials, id) {
    try {
        const response = await browserAPI.runtime.sendMessage({
            action: 'update_credentials',
            id: id,
            domain: credentials.domain,
            username: credentials.username,
            password: credentials.password
        });
        
        if (response && response.success) {
            showNotification('Password updated!', 'success');
        } else if (response && (response.locked || response.error?.includes('locked') || response.error?.includes('Vault'))) {
            // Vault is locked - show unlock form
            showUnlockPrompt(credentials, true, id);
        } else {
            showNotification('Failed to update password', 'error');
        }
    } catch (error) {
        // Check if it's a locked vault error
        if (error.message?.includes('locked') || error.message?.includes('Vault')) {
            showUnlockPrompt(credentials, true, id);
        } else {
            showNotification('Connection error', 'error');
        }
    }
}


/**
 * Show unlock prompt when vault is locked during save/update attempt
 */
function showUnlockPrompt(credentials, isUpdateMode = false, credentialId = null) {
    // Store pending credentials for after unlock
    pendingCredentials = credentials;
    existingCredentialId = credentialId;
    
    const prompt = createSavePrompt(isUpdateMode, true);
    
    // Set up event listeners for unlock form
    const unlockBtn = document.getElementById('vk-unlock');
    const cancelBtn = document.getElementById('vk-cancel');
    const closeBtn = document.getElementById('vk-close');
    const passwordInput = document.getElementById('vk-master-password');
    
    // Clear any existing timeout
    if (promptTimeoutId) {
        clearTimeout(promptTimeoutId);
    }
    
    // Set up 60-second timeout for unlock form (longer than regular save prompt)
    promptTimeoutId = setTimeout(() => {
        hidePrompt();
    }, 60000);
    
    unlockBtn?.addEventListener('click', async () => {
        const masterPassword = passwordInput?.value;
        if (!masterPassword) {
            showUnlockError('Please enter your master password');
            return;
        }
        
        unlockBtn.disabled = true;
        unlockBtn.textContent = 'Unlocking...';
        
        try {
            const unlockResponse = await browserAPI.runtime.sendMessage({
                action: 'unlock',
                password: masterPassword
            });
            
            if (unlockResponse && unlockResponse.success) {
                // Vault unlocked successfully - now save/update credentials
                hidePrompt();
                
                if (isUpdateMode && credentialId) {
                    await updateCredentials(credentials, credentialId);
                } else {
                    await saveCredentials(credentials);
                }
            } else {
                showUnlockError('Invalid master password');
                unlockBtn.disabled = false;
                unlockBtn.textContent = 'Unlock & Save';
            }
        } catch (error) {
            showUnlockError('Failed to unlock vault');
            unlockBtn.disabled = false;
            unlockBtn.textContent = 'Unlock & Save';
        }
    });
    
    // Handle Enter key in password field
    passwordInput?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            unlockBtn?.click();
        }
    });
    
    cancelBtn?.addEventListener('click', hidePrompt);
    closeBtn?.addEventListener('click', hidePrompt);
    
    // Focus the password input
    setTimeout(() => passwordInput?.focus(), 100);
}


/**
 * Show error message in unlock form
 */
function showUnlockError(message) {
    const errorEl = document.getElementById('vk-unlock-error');
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.classList.remove('hidden');
    }
}


function showNotification(message, type = 'success') {
    const existing = document.getElementById('vaultkeeper-notification');
    if (existing) existing.remove();
    
    const checkSvg = `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>`;
    const xSvg = `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`;
    
    const notification = document.createElement('div');
    notification.id = 'vaultkeeper-notification';
    notification.className = type;
    notification.innerHTML = `
        <span class="vk-notif-icon">${type === 'success' ? checkSvg : xSvg}</span>
        <span class="vk-notif-message">${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}


function shouldNeverSave() {
    const neverSave = JSON.parse(localStorage.getItem('vaultkeeper_never_save') || '[]');
    return neverSave.includes(currentDomain);
}


function setupFormInterception() {
    // Track if interception is already set up
    if (document._vaultKeeperInterceptionSetup) return;
    document._vaultKeeperInterceptionSetup = true;
    
    document.addEventListener('submit', (e) => {
        const form = e.target;
        if (form.tagName !== 'FORM') return;
        
        const credentials = captureCredentials(form);
        if (credentials && !shouldNeverSave()) {
            setTimeout(() => showSavePrompt(credentials), 500);
        }
    }, true);
    
    document.addEventListener('click', (e) => {
        const button = e.target.closest('button[type="submit"], input[type="submit"], button:not([type])');
        if (!button) return;
        
        const form = button.closest('form');
        if (!form) return;
        
        // Capture credentials (handles both single and multi-step)
        const credentials = captureCredentials(form);
        
        if (credentials && !shouldNeverSave()) {
            setTimeout(() => showSavePrompt(credentials), 500);
        }
    }, true);
    
    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Enter') return;
        
        const field = e.target;
        const form = field.closest('form');
        if (!form) return;
        
        // Handle Enter key for both username and password fields
        if (field.type === 'password' || USERNAME_SELECTORS.some(s => field.matches(s))) {
            const credentials = captureCredentials(form);
            if (credentials && !shouldNeverSave()) {
                setTimeout(() => showSavePrompt(credentials), 500);
            }
        }
    }, true);
}


function addVaultKeeperIcon(field) {
    if (field.dataset.vaultkeeperIcon) return;
    field.dataset.vaultkeeperIcon = 'true';
    
    const lockSvg = `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>`;
    
    const icon = document.createElement('div');
    icon.className = 'vaultkeeper-field-icon';
    icon.innerHTML = lockSvg;
    icon.title = 'VaultKeeper - Fill credential';
    
    icon.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        requestCredentials();
    });
    
    if (field.parentElement) {
        field.parentElement.style.position = 'relative';
        field.parentElement.appendChild(icon);
    }
}


function requestCredentials() {
    browserAPI.runtime.sendMessage({
        action: 'get_credentials',
        domain: currentDomain
    }, (response) => {
        if (response && response.success && response.credentials && response.credentials.length > 0) {
            const cred = response.credentials[0];
            const filled = fillCredentials(cred.username, cred.password);
            
            if (filled) {
                // Provide appropriate feedback based on what was filled
                if (detectedFields?.isMultiStep) {
                    if (detectedFields.username && !detectedFields.password) {
                        showNotification('Email/username filled!', 'success');
                    } else if (detectedFields.password && !detectedFields.username) {
                        showNotification('Password filled!', 'success');
                    } else {
                        showNotification('Credentials filled!', 'success');
                    }
                } else {
                    showNotification('Credentials filled!', 'success');
                }
            } else {
                showNotification('Could not fill credentials', 'error');
            }
        } else if (response && response.locked) {
            showNotification('Vault is locked', 'error');
        } else {
            showNotification('No credentials found', 'error');
        }
    });
}


function init() {
    // Check for pending credentials from a previous navigation
    const pendingData = getPendingCredentials();
    if (pendingData && pendingData.credentials) {
        // Restore the state
        pendingCredentials = pendingData.credentials;
        existingCredentialId = pendingData.credentialId;
        savePromptShown = true;
        
        // Re-display the prompt
        setTimeout(() => {
            displaySavePrompt(pendingData.credentials, pendingData.isUpdate);
        }, 300);
    }
    
    detectedFields = detectLoginFields();
    
    // Check for any login fields (username OR password)
    if (detectedFields && (detectedFields.username || detectedFields.password)) {
        const fieldType = detectedFields.password && detectedFields.username ? 'standard' :
                         detectedFields.password ? 'password-only' : 'username-only';
        
        // Add icon to password fields if present
        if (detectedFields.password) {
            document.querySelectorAll('input[type="password"]').forEach(addVaultKeeperIcon);
        }
        
        // Add icon to username fields in multi-step scenarios
        if (detectedFields.isMultiStep && detectedFields.username && !detectedFields.password) {
            // Add icon to username field for multi-step login
            addVaultKeeperIconToUsername(detectedFields.username);
        }
        
        setupFormInterception();
    }
}

/**
 * Add VaultKeeper icon to username field (for multi-step login first step)
 */
function addVaultKeeperIconToUsername(field) {
    if (field.dataset.vaultkeeperIcon) return;
    field.dataset.vaultkeeperIcon = 'true';
    
    const lockSvg = `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>`;
    
    const icon = document.createElement('div');
    icon.className = 'vaultkeeper-field-icon';
    icon.innerHTML = lockSvg;
    icon.title = 'VaultKeeper - Fill credential';
    
    icon.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        requestCredentials();
    });
    
    if (field.parentElement) {
        field.parentElement.style.position = 'relative';
        field.parentElement.appendChild(icon);
    }
}

browserAPI.runtime.onMessage.addListener((request, sender, sendResponse) => {
    switch (request.action) {
        case 'fill':
            // Re-detect fields to ensure we have the latest state
            detectedFields = detectLoginFields();
            const success = fillCredentials(request.username, request.password);
            sendResponse({ success, isMultiStep: detectedFields?.isMultiStep || false });
            break;
        case 'detect':
            detectedFields = detectLoginFields();
            sendResponse({ 
                hasForm: !!(detectedFields?.username || detectedFields?.password),
                hasPassword: !!detectedFields?.password,
                hasUsername: !!detectedFields?.username, 
                isMultiStep: detectedFields?.isMultiStep || false,
                domain: currentDomain 
            });
            break;
    }
    return true;
});

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// MutationObserver to detect dynamically added login fields
const observer = new MutationObserver(() => {
    const newFields = detectLoginFields();
    
    // React to new fields being added
    if (newFields) {
        const hasNewPassword = newFields.password && !detectedFields?.password;
        const hasNewUsername = newFields.username && !detectedFields?.username;
        
        if (hasNewPassword || hasNewUsername) {
            detectedFields = newFields;
            
            if (newFields.password) {
                document.querySelectorAll('input[type="password"]').forEach(addVaultKeeperIcon);
            }
            
            if (newFields.isMultiStep && newFields.username && !newFields.password) {
                addVaultKeeperIconToUsername(newFields.username);
            }
            
            setupFormInterception();
        }
    }
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});

