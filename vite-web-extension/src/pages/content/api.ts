import browser from "webextension-polyfill";
import { currentDomain } from "./constants";
import { uiBridge } from "./uiBridge";

export async function checkExistingCredential(
  domain: string,
  username: string,
) {
  try {
    const r: any = await browser.runtime.sendMessage({
      action: "get_credentials",
      domain,
    });
    if (r?.success && r.credentials?.length > 0) {
      return r.credentials.find((c: any) => c.username === username);
    }
    return null;
  } catch {
    return null;
  }
}

export async function saveCredentials(credentials: any) {
  try {
    const response: any = await browser.runtime.sendMessage({
      action: "save_credentials",
      domain: currentDomain,
      username: credentials.username,
      password: credentials.password,
    });
    if (response?.locked) {
      uiBridge.showPrompt({ showUnlockForm: true, credentials });
      return "locked";
    }
    if (response?.success) {
      uiBridge.showNotification("Password saved successfully!", "success");
      return true;
    }
    throw new Error();
  } catch {
    uiBridge.showNotification("Failed to save password", "error");
    return false;
  }
}

export async function updateCredentials(credentials: any, id: number) {
  try {
    const response: any = await browser.runtime.sendMessage({
      action: "update_credentials",
      id,
      domain: credentials.domain,
      username: credentials.username,
      password: credentials.password,
    });
    if (response?.locked) {
      uiBridge.showPrompt({
        showUnlockForm: true,
        credentials,
        isUpdateMode: true,
        credentialId: id,
      });
      return "locked";
    }
    if (response?.success) {
      uiBridge.showNotification("Password updated successfully!", "success");
      return true;
    }
    throw new Error();
  } catch {
    uiBridge.showNotification("Failed to update password", "error");
    return false;
  }
}
