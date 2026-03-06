import {
  currentDomain,
  MULTISTEP_STORAGE_KEY,
  PENDING_CREDENTIALS_KEY,
} from "./constants";

export function getBaseDomain() {
  const parts = currentDomain.split(".");
  return parts.length > 2 ? parts.slice(-2).join(".") : currentDomain;
}

export function isVisible(element: HTMLElement | null): boolean {
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

export function setFieldValue(field: HTMLInputElement, value: string) {
  field.focus();
  field.value = value;
  field.dispatchEvent(new Event("input", { bubbles: true }));
  field.dispatchEvent(new Event("change", { bubbles: true }));
  field.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true }));
  field.dispatchEvent(new KeyboardEvent("keyup", { bubbles: true }));
  const setter = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype,
    "value",
  )?.set;
  if (setter) {
    setter.call(field, value);
    field.dispatchEvent(new Event("input", { bubbles: true }));
  }
}

export function storeMultiStepUsername(username: string) {
  if (!username) return;
  const key = MULTISTEP_STORAGE_KEY + getBaseDomain();
  sessionStorage.setItem(
    key,
    JSON.stringify({
      username,
      timestamp: Date.now(),
      originalDomain: currentDomain,
    }),
  );
}

export function getMultiStepUsername(): string | null {
  const key = MULTISTEP_STORAGE_KEY + getBaseDomain();
  try {
    const stored = sessionStorage.getItem(key);
    if (!stored) return null;
    const data = JSON.parse(stored);
    if (Date.now() - data.timestamp > 5 * 60 * 1000) {
      sessionStorage.removeItem(key);
      return null;
    }
    return data.username;
  } catch {
    return null;
  }
}

export function clearMultiStepUsername() {
  sessionStorage.removeItem(MULTISTEP_STORAGE_KEY + getBaseDomain());
}

export function storePendingCredentials(
  credentials: any,
  isUpdate = false,
  credentialId: number | null = null,
) {
  sessionStorage.setItem(
    PENDING_CREDENTIALS_KEY,
    JSON.stringify({
      credentials,
      isUpdate,
      credentialId,
      timestamp: Date.now(),
    }),
  );
}

export function getPendingCredentials(): any {
  try {
    const stored = sessionStorage.getItem(PENDING_CREDENTIALS_KEY);
    if (!stored) return null;
    const data = JSON.parse(stored);
    if (Date.now() - data.timestamp > 30 * 1000) {
      clearPendingCredentials();
      return null;
    }
    return data;
  } catch {
    return null;
  }
}

export function clearPendingCredentials() {
  sessionStorage.removeItem(PENDING_CREDENTIALS_KEY);
}
