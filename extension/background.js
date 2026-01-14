/**
 * VaultKeeper - Background Service Worker
 * Handles native messaging communication with the desktop app
 */

// Browser API compatibility (Firefox uses 'browser', Chrome uses 'chrome')
const browserAPI = typeof browser !== 'undefined' ? browser : chrome;

const NATIVE_HOST_NAME = "com.vaultkeeper.host";

// State
let nativePort = null;
let isConnected = false;
let pendingRequests = new Map();
let requestId = 0;

/**
 * Connect to the native host
 */
function connectNativeHost() {
  if (nativePort) {
    return;
  }

  try {
    nativePort = browserAPI.runtime.connectNative(NATIVE_HOST_NAME);

    nativePort.onMessage.addListener((message) => {
      console.log("Received from native host:", message);
      handleNativeMessage(message);
    });

    nativePort.onDisconnect.addListener(() => {
      console.log(
        "Native host disconnected:",
        browserAPI.runtime.lastError?.message
      );
      nativePort = null;
      isConnected = false;

      // Reject all pending requests
      for (const [id, { reject }] of pendingRequests) {
        reject(new Error("Native host disconnected"));
      }
      pendingRequests.clear();
    });

    isConnected = true;
    console.log("Connected to native host");
  } catch (error) {
    console.error("Failed to connect to native host:", error);
    isConnected = false;
  }
}

/**
 * Handle messages from the native host
 */
function handleNativeMessage(message) {
  // If this is a response to a pending request
  if (message._requestId !== undefined) {
    const pending = pendingRequests.get(message._requestId);
    if (pending) {
      pendingRequests.delete(message._requestId);
      pending.resolve(message);
    }
  }
}

/**
 * Send a message to the native host
 */
async function sendNativeMessage(action, data = {}) {
  return new Promise((resolve, reject) => {
    if (!nativePort) {
      connectNativeHost();
    }

    if (!nativePort) {
      reject(new Error("Could not connect to native host"));
      return;
    }

    const id = requestId++;
    const message = { action, ...data, _requestId: id };

    pendingRequests.set(id, { resolve, reject });

    // Timeout after 30 seconds
    setTimeout(() => {
      if (pendingRequests.has(id)) {
        pendingRequests.delete(id);
        reject(new Error("Request timed out"));
      }
    }, 30000);

    try {
      nativePort.postMessage(message);
    } catch (error) {
      pendingRequests.delete(id);
      reject(error);
    }
  });
}

/**
 * Get credentials for a domain
 */
async function getCredentials(domain) {
  return sendNativeMessage("get_credentials", { domain });
}

/**
 * Save credentials
 */
async function saveCredentials(domain, username, password, notes = null) {
  return sendNativeMessage("save_credentials", {
    domain,
    username,
    password,
    notes,
  });
}

/**
 * Get vault status
 */
async function getStatus() {
  return sendNativeMessage("status");
}

/**
 * Unlock the vault
 */
async function unlock(password) {
  return sendNativeMessage("unlock", { password });
}

/**
 * Lock the vault
 */
async function lock() {
  return sendNativeMessage("lock");
}

/**
 * Get all credentials
 */
async function getAllCredentials() {
  return sendNativeMessage("get_all_credentials");
}

/**
 * Search credentials
 */
async function searchCredentials(query) {
  return sendNativeMessage("search", { query });
}

// Listen for messages from popup and content scripts
browserAPI.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log("Background received message:", request);

  (async () => {
    try {
      let response;

      switch (request.action) {
        case "ping":
          response = await sendNativeMessage("ping");
          break;

        case "status":
          response = await getStatus();
          break;

        case "unlock":
          response = await unlock(request.password);
          break;

        case "lock":
          response = await lock();
          break;

        case "get_credentials":
          response = await getCredentials(request.domain);
          break;

        case "save_credentials":
          response = await saveCredentials(
            request.domain,
            request.username,
            request.password,
            request.notes
          );
          break;

        case "get_all_credentials":
          response = await getAllCredentials();
          break;

        case "search":
          response = await searchCredentials(request.query);
          break;

        case "fill_credentials":
          // Send credentials to content script
          browserAPI.tabs.sendMessage(sender.tab?.id || request.tabId, {
            action: "fill",
            username: request.username,
            password: request.password,
          });
          response = { success: true };
          break;

        default:
          response = {
            success: false,
            error: `Unknown action: ${request.action}`,
          };
      }

      sendResponse(response);
    } catch (error) {
      console.error("Error handling message:", error);
      sendResponse({ success: false, error: error.message });
    }
  })();

  return true; // Keep the message channel open for async response
});

// Connect on startup
connectNativeHost();

console.log("VaultKeeper background service worker started");
