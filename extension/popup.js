/**
 * VaultKeeper - Popup Script
 * 1Password-style split view UI
 */

// Browser API compatibility
const browserAPI = typeof browser !== 'undefined' ? browser : chrome;

// State
let currentCredentials = [];
let selectedCredential = null;
let actualPasswords = {}; // Store actual passwords for display

// DOM Elements
const loadingView = document.getElementById('loading-view');
const lockedView = document.getElementById('locked-view');
const unlockedView = document.getElementById('unlocked-view');
const disconnectedView = document.getElementById('disconnected-view');
const modal = document.getElementById('modal');

const masterPasswordInput = document.getElementById('master-password');
const errorMessage = document.getElementById('error-message');
const unlockBtn = document.getElementById('unlock-btn');
const lockBtn = document.getElementById('lock-btn');
const addBtn = document.getElementById('add-btn');
const retryBtn = document.getElementById('retry-btn');

const searchInput = document.getElementById('search-input');
const credentialsList = document.getElementById('credentials-list');
const credentialCount = document.getElementById('credential-count');

// Detail elements
const emptyState = document.getElementById('empty-state');
const detailContent = document.getElementById('detail-content');
const detailFavicon = document.getElementById('detail-favicon');
const detailTitle = document.getElementById('detail-title');
const detailUsername = document.getElementById('detail-username');
const detailPassword = document.getElementById('detail-password');
const detailUrl = document.getElementById('detail-url');
const fillBtn = document.getElementById('fill-btn');
const togglePasswordBtn = document.getElementById('toggle-password');

// Modal elements
const credentialForm = document.getElementById('credential-form');
const modalTitle = document.getElementById('modal-title');
const modalClose = document.getElementById('modal-close');
const cancelBtn = document.getElementById('cancel-btn');
const generateBtn = document.getElementById('generate-btn');
const toggleBtn = document.getElementById('toggle-btn');
const credDomain = document.getElementById('cred-domain');
const credUsername = document.getElementById('cred-username');
const credPassword = document.getElementById('cred-password');
const credNotes = document.getElementById('cred-notes');

/**
 * Show a specific view
 */
function showView(viewId) {
    [loadingView, lockedView, unlockedView, disconnectedView].forEach(v => {
        v.classList.add('hidden');
    });
    document.getElementById(viewId).classList.remove('hidden');
}

/**
 * Send message to background script
 */
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

/**
 * Check vault status
 */
async function checkStatus() {
    try {
        const response = await sendMessage({ action: 'status' });
        
        if (!response.success) {
            showView('disconnected-view');
            return;
        }
        
        if (response.unlocked) {
            showView('unlocked-view');
            loadCredentials();
        } else {
            showView('locked-view');
        }
        
    } catch (error) {
        console.error('Status check failed:', error);
        showView('disconnected-view');
    }
}

/**
 * Unlock the vault
 */
async function unlock() {
    const password = masterPasswordInput.value;
    
    if (!password) {
        showError('Enter your master password');
        return;
    }
    
    try {
        unlockBtn.disabled = true;
        unlockBtn.textContent = 'Unlocking...';
        
        const response = await sendMessage({ action: 'unlock', password });
        
        if (response.success) {
            masterPasswordInput.value = '';
            hideError();
            showView('unlocked-view');
            loadCredentials();
        } else {
            showError(response.error || 'Incorrect password');
        }
        
    } catch (error) {
        showError('Connection error');
    } finally {
        unlockBtn.disabled = false;
        unlockBtn.textContent = 'Unlock';
    }
}

/**
 * Lock the vault
 */
async function lock() {
    try {
        await sendMessage({ action: 'lock' });
        selectedCredential = null;
        currentCredentials = [];
        showView('locked-view');
    } catch (error) {
        console.error('Lock failed:', error);
    }
}

/**
 * Load credentials
 */
async function loadCredentials() {
    try {
        const response = await sendMessage({ action: 'get_all_credentials' });
        
        if (response.success) {
            currentCredentials = response.credentials || [];
            
            // Store actual passwords
            actualPasswords = {};
            currentCredentials.forEach(cred => {
                actualPasswords[cred.id] = cred.password;
            });
            
            // Sort alphabetically
            currentCredentials.sort((a, b) => a.domain.localeCompare(b.domain));
            
            renderCredentials();
            updateCredentialCount();
            
            // Select first item if any
            if (currentCredentials.length > 0 && !selectedCredential) {
                selectCredential(currentCredentials[0]);
            }
        }
        
    } catch (error) {
        console.error('Failed to load credentials:', error);
    }
}

/**
 * Render credentials list
 */
function renderCredentials(filter = '') {
    credentialsList.innerHTML = '';
    
    const filtered = currentCredentials.filter(cred => 
        cred.domain.toLowerCase().includes(filter.toLowerCase()) ||
        cred.username.toLowerCase().includes(filter.toLowerCase())
    );
    
    if (filtered.length === 0) {
        credentialsList.innerHTML = `
            <div class="empty-list">
                <div class="empty-list-icon">📭</div>
                <p>${filter ? 'No results' : 'No credentials yet'}</p>
            </div>
        `;
        return;
    }
    
    filtered.forEach(cred => {
        const item = createCredentialItem(cred);
        credentialsList.appendChild(item);
    });
}

/**
 * Create credential item element
 */
function createCredentialItem(cred) {
    const item = document.createElement('div');
    item.className = 'credential-item';
    item.dataset.id = cred.id;
    
    if (selectedCredential && selectedCredential.id === cred.id) {
        item.classList.add('selected');
    }
    
    // Get favicon
    const faviconUrl = `https://www.google.com/s2/favicons?domain=${cred.domain}&sz=32`;
    
    item.innerHTML = `
        <div class="credential-favicon">
            <img src="${faviconUrl}" onerror="this.parentElement.innerHTML='🌐'">
        </div>
        <div class="credential-info">
            <div class="credential-domain">${escapeHtml(getDomainDisplay(cred.domain))}</div>
            <div class="credential-username">${escapeHtml(cred.username)}</div>
        </div>
    `;
    
    item.addEventListener('click', () => selectCredential(cred));
    
    return item;
}

/**
 * Get display name from domain
 */
function getDomainDisplay(domain) {
    // Remove protocol and www
    let display = domain.replace(/^(https?:\/\/)?(www\.)?/, '');
    // Remove path
    display = display.split('/')[0];
    // Capitalize first letter
    return display.charAt(0).toUpperCase() + display.slice(1);
}

/**
 * Select a credential and show details
 */
function selectCredential(cred) {
    selectedCredential = cred;
    
    // Update list selection
    document.querySelectorAll('.credential-item').forEach(item => {
        item.classList.remove('selected');
        if (item.dataset.id == cred.id) {
            item.classList.add('selected');
        }
    });
    
    // Show detail panel
    emptyState.classList.add('hidden');
    detailContent.classList.remove('hidden');
    
    // Get favicon
    const faviconUrl = `https://www.google.com/s2/favicons?domain=${cred.domain}&sz=64`;
    detailFavicon.innerHTML = `<img src="${faviconUrl}" onerror="this.parentElement.innerHTML='🌐'" style="width:32px;height:32px">`;
    
    detailTitle.textContent = getDomainDisplay(cred.domain);
    detailUsername.textContent = cred.username;
    detailPassword.textContent = '••••••••••';
    detailPassword.classList.add('password-masked');
    detailPassword.dataset.visible = 'false';
    
    // Set URL
    let url = cred.domain;
    if (!url.startsWith('http')) {
        url = 'https://' + url;
    }
    detailUrl.textContent = url;
    detailUrl.href = url;
}

/**
 * Toggle password visibility in detail view
 */
function toggleDetailPassword() {
    if (!selectedCredential) return;
    
    const isVisible = detailPassword.dataset.visible === 'true';
    
    if (isVisible) {
        detailPassword.textContent = '••••••••••';
        detailPassword.classList.add('password-masked');
        detailPassword.dataset.visible = 'false';
    } else {
        detailPassword.textContent = actualPasswords[selectedCredential.id] || '';
        detailPassword.classList.remove('password-masked');
        detailPassword.dataset.visible = 'true';
    }
}

/**
 * Fill credential in page
 */
async function fillCredential() {
    if (!selectedCredential) return;
    
    try {
        const [tab] = await browserAPI.tabs.query({ active: true, currentWindow: true });
        
        await browserAPI.tabs.sendMessage(tab.id, {
            action: 'fill',
            username: selectedCredential.username,
            password: actualPasswords[selectedCredential.id] || ''
        });
        
        window.close();
        
    } catch (error) {
        console.error('Fill failed:', error);
    }
}

/**
 * Copy to clipboard
 */
async function copyToClipboard(type) {
    if (!selectedCredential) return;
    
    let text = '';
    switch (type) {
        case 'username':
            text = selectedCredential.username;
            break;
        case 'password':
            text = actualPasswords[selectedCredential.id] || '';
            break;
        case 'url':
            text = selectedCredential.domain;
            break;
    }
    
    try {
        await navigator.clipboard.writeText(text);
        
        // Show feedback
        const btn = document.querySelector(`[data-copy="${type}"]`);
        if (btn) {
            const originalHTML = btn.innerHTML;
            btn.innerHTML = '✓';
            setTimeout(() => btn.innerHTML = originalHTML, 1500);
        }
        
        // Clear clipboard after 30 seconds for password
        if (type === 'password') {
            setTimeout(async () => {
                try {
                    const current = await navigator.clipboard.readText();
                    if (current === text) {
                        await navigator.clipboard.writeText('');
                    }
                } catch (e) {}
            }, 30000);
        }
        
    } catch (error) {
        console.error('Copy failed:', error);
    }
}

/**
 * Update credential count
 */
function updateCredentialCount() {
    credentialCount.textContent = currentCredentials.length;
}

/**
 * Open add modal
 */
function openAddModal() {
    modalTitle.textContent = 'New Item';
    credentialForm.reset();
    
    // Pre-fill domain from current tab
    browserAPI.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
            try {
                const url = new URL(tabs[0].url);
                credDomain.value = url.hostname;
            } catch (e) {}
        }
    });
    
    modal.classList.remove('hidden');
}

/**
 * Close modal
 */
function closeModal() {
    modal.classList.add('hidden');
    credentialForm.reset();
}

/**
 * Save credential
 */
async function saveCredential(e) {
    e.preventDefault();
    
    const data = {
        domain: credDomain.value.trim(),
        username: credUsername.value.trim(),
        password: credPassword.value,
        notes: credNotes.value.trim() || null
    };
    
    if (!data.domain || !data.username || !data.password) {
        return;
    }
    
    try {
        const response = await sendMessage({
            action: 'save_credentials',
            ...data
        });
        
        if (response.success) {
            closeModal();
            await loadCredentials();
        } else {
            alert(response.error || 'Save failed');
        }
        
    } catch (error) {
        console.error('Save failed:', error);
        alert('Error saving credential');
    }
}

/**
 * Generate password
 */
function generatePassword() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
    let password = '';
    for (let i = 0; i < 16; i++) {
        password += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    credPassword.value = password;
    credPassword.type = 'text';
}

/**
 * Toggle modal password visibility
 */
function toggleModalPassword() {
    credPassword.type = credPassword.type === 'password' ? 'text' : 'password';
}

/**
 * Show error message
 */
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
}

/**
 * Hide error message
 */
function hideError() {
    errorMessage.classList.add('hidden');
}

/**
 * Escape HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Event Listeners
unlockBtn.addEventListener('click', unlock);
masterPasswordInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') unlock();
});

lockBtn.addEventListener('click', lock);
addBtn.addEventListener('click', openAddModal);
retryBtn.addEventListener('click', checkStatus);

searchInput.addEventListener('input', (e) => {
    renderCredentials(e.target.value);
});

fillBtn.addEventListener('click', fillCredential);
togglePasswordBtn.addEventListener('click', toggleDetailPassword);

// Copy buttons
document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', () => copyToClipboard(btn.dataset.copy));
});

modalClose.addEventListener('click', closeModal);
cancelBtn.addEventListener('click', closeModal);
credentialForm.addEventListener('submit', saveCredential);
generateBtn.addEventListener('click', generatePassword);
toggleBtn.addEventListener('click', toggleModalPassword);

// Close modal on backdrop click
modal.querySelector('.modal-backdrop').addEventListener('click', closeModal);

// Initialize
document.addEventListener('DOMContentLoaded', checkStatus);
