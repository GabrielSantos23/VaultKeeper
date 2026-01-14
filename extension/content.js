/**
 * VaultKeeper - Content Script
 * Detects login forms, handles autofill, and prompts to save credentials
 */

// Browser API compatibility
const browserAPI = typeof browser !== 'undefined' ? browser : chrome;

// State
let detectedFields = null;
let currentDomain = window.location.hostname;
let pendingCredentials = null;
let savePromptShown = false;

// Selectors for form detection
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

/**
 * Detect login form fields on the page
 */
function detectLoginFields() {
    const fields = {
        username: null,
        password: null,
        form: null
    };
    
    // Find visible password field
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
    
    if (!fields.password) {
        return null;
    }
    
    // Find username field
    const searchContainer = fields.form || document;
    
    for (const selector of USERNAME_SELECTORS) {
        const candidates = searchContainer.querySelectorAll(selector);
        for (const candidate of candidates) {
            if (!isVisible(candidate)) continue;
            if (candidate === fields.password) continue;
            
            // Prefer fields before password in DOM
            if (fields.password.compareDocumentPosition(candidate) & Node.DOCUMENT_POSITION_PRECEDING) {
                fields.username = candidate;
                break;
            }
            
            // Fallback to any visible text/email field
            if (!fields.username) {
                fields.username = candidate;
            }
        }
        if (fields.username) break;
    }
    
    return fields;
}

/**
 * Check if element is visible
 */
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

/**
 * Fill login form with credentials
 */
function fillCredentials(username, password) {
    if (!detectedFields) {
        detectedFields = detectLoginFields();
    }
    
    if (!detectedFields || !detectedFields.password) {
        console.log('VaultKeeper: No login form detected');
        return false;
    }
    
    if (detectedFields.username && username) {
        setFieldValue(detectedFields.username, username);
    }
    
    if (detectedFields.password && password) {
        setFieldValue(detectedFields.password, password);
    }
    
    console.log('VaultKeeper: Credentials filled');
    return true;
}

/**
 * Set field value with proper event dispatching
 */
function setFieldValue(field, value) {
    field.focus();
    field.value = value;
    
    // Dispatch events for React/Angular/Vue
    field.dispatchEvent(new Event('input', { bubbles: true }));
    field.dispatchEvent(new Event('change', { bubbles: true }));
    field.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true }));
    field.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
    
    // For React 16+
    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    nativeInputValueSetter.call(field, value);
    field.dispatchEvent(new Event('input', { bubbles: true }));
}

/**
 * Capture credentials before form submission
 */
function captureCredentials(form) {
    const passwordField = form.querySelector('input[type="password"]');
    if (!passwordField || !passwordField.value) return null;
    
    // Find username field
    let username = '';
    for (const selector of USERNAME_SELECTORS) {
        const field = form.querySelector(selector);
        if (field && field !== passwordField && field.value) {
            username = field.value;
            break;
        }
    }
    
    if (!username) return null;
    
    return {
        domain: currentDomain,
        username: username,
        password: passwordField.value
    };
}

/**
 * Create save prompt UI
 */
function createSavePrompt() {
    // Remove existing prompt
    const existing = document.getElementById('vaultkeeper-save-prompt');
    if (existing) existing.remove();
    
    const prompt = document.createElement('div');
    prompt.id = 'vaultkeeper-save-prompt';
    prompt.innerHTML = `
        <div class="vk-prompt-overlay"></div>
        <div class="vk-prompt-container">
            <div class="vk-prompt-header">
                <span class="vk-prompt-icon">🔐</span>
                <span class="vk-prompt-title">VaultKeeper</span>
                <button class="vk-close-btn" id="vk-close">&times;</button>
            </div>
            <div class="vk-prompt-body">
                <p class="vk-prompt-message">Save this password?</p>
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
            </div>
            <div class="vk-prompt-actions">
                <button class="vk-btn vk-btn-secondary" id="vk-never">Never for this site</button>
                <button class="vk-btn vk-btn-primary" id="vk-save">Save Password</button>
            </div>
        </div>
    `;
    
    // Add styles
    const style = document.createElement('style');
    style.textContent = `
        #vaultkeeper-save-prompt {
            position: fixed;
            top: 0;
            right: 0;
            bottom: 0;
            left: 0;
            z-index: 2147483647;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        .vk-prompt-overlay {
            position: absolute;
            inset: 0;
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(2px);
        }
        
        .vk-prompt-container {
            position: absolute;
            top: 20px;
            right: 20px;
            width: 360px;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            animation: vk-slide-in 0.3s ease;
            overflow: hidden;
        }
        
        @keyframes vk-slide-in {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .vk-prompt-header {
            display: flex;
            align-items: center;
            padding: 16px 20px;
            background: linear-gradient(135deg, #0066ff 0%, #0052cc 100%);
            color: white;
        }
        
        .vk-prompt-icon {
            font-size: 20px;
            margin-right: 10px;
        }
        
        .vk-prompt-title {
            flex: 1;
            font-size: 16px;
            font-weight: 600;
        }
        
        .vk-close-btn {
            background: transparent;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            opacity: 0.8;
            line-height: 1;
        }
        
        .vk-close-btn:hover {
            opacity: 1;
        }
        
        .vk-prompt-body {
            padding: 20px;
        }
        
        .vk-prompt-message {
            font-size: 15px;
            font-weight: 500;
            margin: 0 0 16px 0;
            color: #1a1a1a;
        }
        
        .vk-credential-preview {
            background: #f5f6f7;
            border-radius: 8px;
            padding: 12px 16px;
        }
        
        .vk-cred-row {
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
        }
        
        .vk-cred-row:not(:last-child) {
            border-bottom: 1px solid #e0e0e0;
        }
        
        .vk-cred-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .vk-cred-value {
            font-size: 13px;
            color: #1a1a1a;
            font-weight: 500;
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .vk-prompt-actions {
            display: flex;
            gap: 10px;
            padding: 0 20px 20px;
        }
        
        .vk-btn {
            flex: 1;
            padding: 12px 16px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .vk-btn-primary {
            background: #0066ff;
            color: white;
        }
        
        .vk-btn-primary:hover {
            background: #0052cc;
        }
        
        .vk-btn-secondary {
            background: #e8eaed;
            color: #333;
        }
        
        .vk-btn-secondary:hover {
            background: #d0d4d8;
        }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(prompt);
    
    return prompt;
}

/**
 * Show save prompt
 */
function showSavePrompt(credentials) {
    if (savePromptShown) return;
    savePromptShown = true;
    pendingCredentials = credentials;
    
    const prompt = createSavePrompt();
    
    // Update with captured credentials
    document.getElementById('vk-domain').textContent = credentials.domain;
    document.getElementById('vk-username').textContent = credentials.username;
    
    // Event handlers
    document.getElementById('vk-save').addEventListener('click', () => {
        saveCredentials(credentials);
        hidePrompt();
    });
    
    document.getElementById('vk-never').addEventListener('click', () => {
        // Store in local storage to never ask again for this domain
        const neverSave = JSON.parse(localStorage.getItem('vaultkeeper_never_save') || '[]');
        neverSave.push(currentDomain);
        localStorage.setItem('vaultkeeper_never_save', JSON.stringify(neverSave));
        hidePrompt();
    });
    
    document.getElementById('vk-close').addEventListener('click', hidePrompt);
    
    prompt.querySelector('.vk-prompt-overlay').addEventListener('click', hidePrompt);
}

/**
 * Hide save prompt
 */
function hidePrompt() {
    const prompt = document.getElementById('vaultkeeper-save-prompt');
    if (prompt) {
        prompt.style.animation = 'vk-fade-out 0.2s ease forwards';
        setTimeout(() => prompt.remove(), 200);
    }
    savePromptShown = false;
    pendingCredentials = null;
}

/**
 * Save credentials via background script
 */
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
        } else {
            showNotification('Failed to save password', 'error');
        }
    } catch (error) {
        console.error('VaultKeeper: Save error', error);
        showNotification('Connection error', 'error');
    }
}

/**
 * Show a small notification
 */
function showNotification(message, type = 'success') {
    const existing = document.getElementById('vaultkeeper-notification');
    if (existing) existing.remove();
    
    const notification = document.createElement('div');
    notification.id = 'vaultkeeper-notification';
    notification.innerHTML = `
        <span class="vk-notif-icon">${type === 'success' ? '✓' : '✕'}</span>
        <span class="vk-notif-message">${message}</span>
    `;
    
    const style = document.createElement('style');
    style.textContent = `
        #vaultkeeper-notification {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: ${type === 'success' ? '#34c759' : '#ff3b30'};
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 10px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
            z-index: 2147483647;
            animation: vk-notif-in 0.3s ease;
        }
        
        @keyframes vk-notif-in {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
        }
        
        .vk-notif-icon {
            font-size: 18px;
        }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'vk-notif-out 0.3s ease forwards';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

/**
 * Check if domain is in never-save list
 */
function shouldNeverSave() {
    const neverSave = JSON.parse(localStorage.getItem('vaultkeeper_never_save') || '[]');
    return neverSave.includes(currentDomain);
}

/**
 * Setup form submission interception
 */
function setupFormInterception() {
    // Listen for form submissions
    document.addEventListener('submit', (e) => {
        const form = e.target;
        if (form.tagName !== 'FORM') return;
        
        const credentials = captureCredentials(form);
        if (credentials && !shouldNeverSave()) {
            // Small delay to allow form to submit
            setTimeout(() => showSavePrompt(credentials), 500);
        }
    }, true);
    
    // Also intercept click on submit buttons (for SPAs)
    document.addEventListener('click', (e) => {
        const button = e.target.closest('button[type="submit"], input[type="submit"], button:not([type])');
        if (!button) return;
        
        const form = button.closest('form');
        if (!form) return;
        
        // Check if form has password field
        const passwordField = form.querySelector('input[type="password"]');
        if (!passwordField || !passwordField.value) return;
        
        const credentials = captureCredentials(form);
        if (credentials && !shouldNeverSave()) {
            setTimeout(() => showSavePrompt(credentials), 500);
        }
    }, true);
    
    // Intercept Enter key in password fields
    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Enter') return;
        
        const field = e.target;
        if (field.type !== 'password') return;
        
        const form = field.closest('form');
        if (!form) return;
        
        const credentials = captureCredentials(form);
        if (credentials && !shouldNeverSave()) {
            setTimeout(() => showSavePrompt(credentials), 500);
        }
    }, true);
}

/**
 * Create VaultKeeper icon in password fields
 */
function addVaultKeeperIcon(field) {
    if (field.dataset.vaultkeeperIcon) return;
    field.dataset.vaultkeeperIcon = 'true';
    
    // Create wrapper if needed
    const wrapper = document.createElement('div');
    wrapper.style.cssText = 'position: relative; display: inline-block;';
    
    const icon = document.createElement('div');
    icon.className = 'vaultkeeper-field-icon';
    icon.innerHTML = '🔐';
    icon.title = 'VaultKeeper - Fill credential';
    icon.style.cssText = `
        position: absolute;
        right: 8px;
        top: 50%;
        transform: translateY(-50%);
        cursor: pointer;
        font-size: 14px;
        z-index: 10000;
        opacity: 0.6;
        transition: opacity 0.2s;
        user-select: none;
    `;
    
    icon.addEventListener('mouseenter', () => icon.style.opacity = '1');
    icon.addEventListener('mouseleave', () => icon.style.opacity = '0.6');
    icon.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        requestCredentials();
    });
    
    // Insert icon after field
    if (field.parentElement) {
        field.parentElement.style.position = 'relative';
        field.parentElement.appendChild(icon);
    }
}

/**
 * Request credentials from background
 */
function requestCredentials() {
    browserAPI.runtime.sendMessage({
        action: 'get_credentials',
        domain: currentDomain
    }, (response) => {
        if (response && response.success && response.credentials && response.credentials.length > 0) {
            const cred = response.credentials[0];
            fillCredentials(cred.username, cred.password);
            showNotification('Credentials filled!', 'success');
        } else if (response && response.locked) {
            showNotification('Vault is locked', 'error');
        } else {
            showNotification('No credentials found', 'error');
        }
    });
}

/**
 * Initialize content script
 */
function init() {
    detectedFields = detectLoginFields();
    
    if (detectedFields && detectedFields.password) {
        console.log('VaultKeeper: Login form detected on', currentDomain);
        
        // Add icons to password fields
        document.querySelectorAll('input[type="password"]').forEach(addVaultKeeperIcon);
        
        // Setup form interception for save prompts
        setupFormInterception();
    }
}

// Listen for messages from background script
browserAPI.runtime.onMessage.addListener((request, sender, sendResponse) => {
    switch (request.action) {
        case 'fill':
            const success = fillCredentials(request.username, request.password);
            sendResponse({ success });
            break;
        case 'detect':
            detectedFields = detectLoginFields();
            sendResponse({ hasForm: !!detectedFields?.password, domain: currentDomain });
            break;
    }
    return true;
});

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Re-run detection on dynamic content
const observer = new MutationObserver(() => {
    const newFields = detectLoginFields();
    if (newFields?.password && !detectedFields?.password) {
        detectedFields = newFields;
        document.querySelectorAll('input[type="password"]').forEach(addVaultKeeperIcon);
        setupFormInterception();
    }
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});

console.log('VaultKeeper content script loaded');
