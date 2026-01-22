const browserAPI = typeof browser !== "undefined" ? browser : chrome;

const NATIVE_HOST_NAME = "com.vaultkeeper.host";

let nativePort = null;
let isConnected = false;
let pendingRequests = new Map();
let requestId = 0;

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

async function getCredentials(domain) {
  return sendNativeMessage("get_credentials", { domain });
}

async function saveCredentials(domain, username, password, notes = null) {
  return sendNativeMessage("save_credentials", {
    domain,
    username,
    password,
    notes,
  });
}

async function getStatus() {
  return sendNativeMessage("status");
}

async function unlock(password) {
  return sendNativeMessage("unlock", { password });
}

async function lock() {
  return sendNativeMessage("lock");
}

async function getAllCredentials() {
  return sendNativeMessage("get_all_credentials");
}

async function searchCredentials(query) {
  return sendNativeMessage("search", { query });
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

        case "check_credentials":
          response = await sendNativeMessage("check_credentials", {
            domain: request.domain,
          });
          break;

        case "save_credentials":
          response = await saveCredentials(
            request.domain,
            request.username,
            request.password,
            request.notes,
          );
          break;

        case "get_all_credentials":
          response = await getAllCredentials();
          break;

        case "search":
          response = await searchCredentials(request.query);
          break;

        case "toggle_favorite":
          response = await sendNativeMessage("toggle_favorite", {
            id: request.id,
          });
          break;

        case "delete_credentials":
          response = await sendNativeMessage("delete_credentials", {
            id: request.id,
          });
          break;

        case "update_credentials":
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
          response = await sendNativeMessage("set_folder", {
            id: request.id,
            folder_id: request.folder_id,
          });
          break;

        case "get_totp":
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
          response = await sendNativeMessage("get_all_credit_cards");
          break;

        case "save_credit_card":
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
          response = await sendNativeMessage("delete_credit_card", {
            id: request.id,
          });
          break;

        case "get_all_secure_notes":
          response = await sendNativeMessage("get_all_secure_notes");
          break;

        case "save_secure_note":
          response = await sendNativeMessage("save_secure_note", {
            id: request.id,
            title: request.title,
            content: request.content,
          });
          break;

        case "delete_secure_note":
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
