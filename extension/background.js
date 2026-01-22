const browserAPI = typeof browser !== "undefined" ? browser : chrome;

const NATIVE_HOST_NAME = "com.vaultkeeper.host";

let nativePort = null;
let isConnected = false;
let pendingRequests = new Map();
let requestId = 0;

// Internal Cache to avoid redundant native requests
let inMemoryCache = {
  credentials: null,
  notes: null,
  cards: null,
};

function connectNativeHost() {
  if (nativePort) {
    return;
  }

  try {
    nativePort = browserAPI.runtime.connectNative(NATIVE_HOST_NAME);

    nativePort.onMessage.addListener((message) => {
      handleNativeMessage(message);
    });

    nativePort.onDisconnect.addListener(() => {
      nativePort = null;
      isConnected = false;
      // Clear cache on disconnect/restart
      inMemoryCache = { credentials: null, notes: null, cards: null };

      for (const [id, { reject }] of pendingRequests) {
        reject(new Error("Native host disconnected"));
      }
      pendingRequests.clear();
    });

    isConnected = true;
  } catch (error) {
    isConnected = false;
  }
}

function handleNativeMessage(message) {
  if (message._requestId !== undefined) {
    const pending = pendingRequests.get(message._requestId);
    if (pending) {
      pendingRequests.delete(message._requestId);
      pending.resolve(message);
    }
  }
}

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

// Helpers that manage cache
async function getStatus() {
  return sendNativeMessage("status");
}

async function unlock(password) {
  // Clear cache on unlock to ensure fresh start, or keep null
  inMemoryCache = { credentials: null, notes: null, cards: null };
  return sendNativeMessage("unlock", { password });
}

async function lock() {
  // Clear cache on lock
  inMemoryCache = { credentials: null, notes: null, cards: null };
  return sendNativeMessage("lock");
}

browserAPI.runtime.onMessage.addListener((request, sender, sendResponse) => {
  (async () => {
    try {
      let response;

      switch (request.action) {
        case "ping":
          response = await sendNativeMessage("ping");
          break;

        case "status":
          response = await getStatus();
          // If locked or disconnected, clear cache
          if (response.success && !response.unlocked) {
            if (
              inMemoryCache.credentials ||
              inMemoryCache.notes ||
              inMemoryCache.cards
            ) {
              inMemoryCache = { credentials: null, notes: null, cards: null };
            }
          }
          break;

        case "unlock":
          response = await unlock(request.password);
          break;

        case "lock":
          response = await lock();
          break;

        case "get_credentials":
          response = await sendNativeMessage("get_credentials", {
            domain: request.domain,
          });
          break;

        case "check_credentials":
          response = await sendNativeMessage("check_credentials", {
            domain: request.domain,
          });
          break;

        case "invalidate_cache":
          inMemoryCache = { credentials: null, notes: null, cards: null };
          response = { success: true };
          break;

        case "save_credentials":
          inMemoryCache.credentials = null; // Invalidate cache
          response = await sendNativeMessage("save_credentials", {
            domain: request.domain,
            username: request.username,
            password: request.password,
            notes: request.notes,
          });
          break;

        case "get_all_credentials":
          if (inMemoryCache.credentials) {
            response = inMemoryCache.credentials;
            // Background refresh? Maybe implemented later if stale data is an issue
          } else {
            response = await sendNativeMessage("get_all_credentials");
            if (response.success) {
              inMemoryCache.credentials = response;
            }
          }
          break;

        case "search":
          // Search should probably bypass cache or filter local cache if complete?
          // Native search is better for large datasets (but here datasets are small-ish).
          response = await sendNativeMessage("search", {
            query: request.query,
          });
          break;

        case "toggle_favorite":
          inMemoryCache.credentials = null; // Invalidate
          response = await sendNativeMessage("toggle_favorite", {
            id: request.id,
          });
          break;

        case "delete_credentials":
          inMemoryCache.credentials = null; // Invalidate
          response = await sendNativeMessage("delete_credentials", {
            id: request.id,
          });
          break;

        case "update_credentials":
          inMemoryCache.credentials = null; // Invalidate
          response = await sendNativeMessage("update_credentials", {
            id: request.id,
            domain: request.domain,
            username: request.username,
            password: request.password,
            notes: request.notes,
          });
          break;

        case "get_folders":
          response = await sendNativeMessage("get_folders");
          break;

        case "set_folder":
          inMemoryCache.credentials = null; // Moving folder affects list order/grouping? Maybe. Best to invalidate.
          response = await sendNativeMessage("set_folder", {
            id: request.id,
            folder_id: request.folder_id,
          });
          break;

        case "get_totp":
          // Dynamic data, do not cache
          response = await sendNativeMessage("get_totp", {
            id: request.id,
          });
          break;

        case "fill_credentials":
          browserAPI.tabs.sendMessage(sender.tab?.id || request.tabId, {
            action: "fill",
            username: request.username,
            password: request.password,
          });
          response = { success: true };
          break;

        case "get_all_credit_cards":
          if (inMemoryCache.cards) {
            response = inMemoryCache.cards;
          } else {
            response = await sendNativeMessage("get_all_credit_cards");
            if (response.success) {
              inMemoryCache.cards = response;
            }
          }
          break;

        case "save_credit_card":
          inMemoryCache.cards = null; // Invalidate
          response = await sendNativeMessage("save_credit_card", {
            id: request.id,
            title: request.title,
            cardholder_name: request.cardholder_name,
            card_number: request.card_number,
            expiry_date: request.expiry_date,
            cvv: request.cvv,
            notes: request.notes,
          });
          break;

        case "delete_credit_card":
          inMemoryCache.cards = null; // Invalidate
          response = await sendNativeMessage("delete_credit_card", {
            id: request.id,
          });
          break;

        case "get_all_secure_notes":
          if (inMemoryCache.notes) {
            response = inMemoryCache.notes;
          } else {
            response = await sendNativeMessage("get_all_secure_notes");
            if (response.success) {
              inMemoryCache.notes = response;
            }
          }
          break;

        case "save_secure_note":
          inMemoryCache.notes = null; // Invalidate
          response = await sendNativeMessage("save_secure_note", {
            id: request.id,
            title: request.title,
            content: request.content,
          });
          break;

        case "delete_secure_note":
          inMemoryCache.notes = null; // Invalidate
          response = await sendNativeMessage("delete_secure_note", {
            id: request.id,
          });
          break;

        case "fill_card":
          browserAPI.tabs.sendMessage(sender.tab?.id || request.tabId, {
            action: "fill_card",
            card_number: request.card_number,
            expiry_date: request.expiry_date,
            cvv: request.cvv,
            cardholder_name: request.cardholder_name,
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
      sendResponse({ success: false, error: error.message });
    }
  })();

  return true;
});

connectNativeHost();
