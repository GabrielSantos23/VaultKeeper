import browser from "webextension-polyfill";
import {
  USERNAME_SELECTORS,
  PASSWORD_SELECTORS,
  TOTP_SELECTORS,
  currentDomain,
  state,
} from "./constants";
import {
  isVisible,
  setFieldValue,
  storeMultiStepUsername,
  getMultiStepUsername,
  clearMultiStepUsername,
  storePendingCredentials,
} from "./helpers";
import { uiBridge } from "./uiBridge";
import { checkExistingCredential } from "./api";

export function detectLoginFields() {
  const fields: {
    username: HTMLInputElement | null;
    password: HTMLInputElement | null;
    form: HTMLFormElement | null;
    isMultiStep: boolean;
  } = { username: null, password: null, form: null, isMultiStep: false };

  for (const selector of PASSWORD_SELECTORS) {
    for (const field of document.querySelectorAll(selector)) {
      if (isVisible(field as HTMLElement)) {
        fields.password = field as HTMLInputElement;
        fields.form = (field as HTMLInputElement).closest("form");
        break;
      }
    }
    if (fields.password) break;
  }

  const searchContainer = fields.form || document;
  for (const selector of USERNAME_SELECTORS) {
    for (const candidate of searchContainer.querySelectorAll(selector)) {
      if (!isVisible(candidate as HTMLElement) || candidate === fields.password)
        continue;
      const name = ((candidate as HTMLInputElement).name || "").toLowerCase();
      const id = ((candidate as HTMLInputElement).id || "").toLowerCase();
      const ph = (
        (candidate as HTMLInputElement).placeholder || ""
      ).toLowerCase();

      if (
        [name, id, ph].some(
          (v) => v.includes("search") || v.includes("query"),
        ) ||
        [name, id].some(
          (v) =>
            v.includes("totp") ||
            v.includes("code") ||
            v.includes("otp") ||
            v.includes("2fa"),
        ) ||
        ph.includes("code")
      )
        continue;

      if (
        fields.password &&
        fields.password.compareDocumentPosition(candidate as Node) &
          Node.DOCUMENT_POSITION_PRECEDING
      ) {
        fields.username = candidate as HTMLInputElement;
        break;
      }
      if (!fields.username) fields.username = candidate as HTMLInputElement;
    }
    if (fields.username) break;
  }

  if (fields.password && !fields.username) fields.isMultiStep = true;
  else if (fields.username && !fields.password) {
    fields.isMultiStep = true;
    fields.form = fields.username.closest("form");
  }

  return fields.username || fields.password ? fields : null;
}

export function fillTOTP(code: string): boolean {
  if (!code) return false;
  for (const sel of TOTP_SELECTORS)
    for (const inp of document.querySelectorAll(sel))
      if (isVisible(inp as HTMLElement)) {
        setFieldValue(inp as HTMLInputElement, code);
        return true;
      }
  return false;
}

export function fillCredentials(
  username: string,
  password: string,
  totpCode: string | null = null,
): boolean {
  if (!state.detectedFields) state.detectedFields = detectLoginFields();
  let filled = false;
  let totpField: HTMLInputElement | null = null;

  if (totpCode && fillTOTP(totpCode)) {
    filled = true;
    for (const sel of TOTP_SELECTORS)
      for (const inp of document.querySelectorAll(sel))
        if (
          isVisible(inp as HTMLElement) &&
          (inp as HTMLInputElement).value === totpCode
        ) {
          totpField = inp as HTMLInputElement;
          break;
        }
  }

  if (
    !state.detectedFields ||
    (!state.detectedFields.username && !state.detectedFields.password)
  )
    return filled;

  if (state.detectedFields.username && !state.detectedFields.password) {
    if (username && state.detectedFields.username !== totpField) {
      setFieldValue(state.detectedFields.username, username);
      storeMultiStepUsername(username);
      filled = true;
    }
  } else if (state.detectedFields.password && !state.detectedFields.username) {
    if (password) {
      setFieldValue(state.detectedFields.password, password);
      filled = true;
    }
  } else {
    if (
      state.detectedFields.username &&
      username &&
      state.detectedFields.username !== totpField
    ) {
      setFieldValue(state.detectedFields.username, username);
      filled = true;
    }
    if (state.detectedFields.password && password) {
      setFieldValue(state.detectedFields.password, password);
      filled = true;
    }
  }
  return filled;
}

export function fillCreditCard(
  cardNumber: string,
  expiryDate: string,
  cvv: string,
  cardholderName: string,
): boolean {
  let filled = false;
  const tryFill = (sels: string[], val: string) => {
    for (const s of sels) {
      const f = document.querySelector(s) as HTMLInputElement | null;
      if (f && isVisible(f)) {
        setFieldValue(f, val);
        filled = true;
        return;
      }
    }
  };
  tryFill(
    [
      'input[autocomplete="cc-number"]',
      'input[name*="card" i][name*="number" i]',
      'input[name*="cardnumber" i]',
      'input[id*="card" i][id*="number" i]',
      'input[placeholder*="card number" i]',
    ],
    cardNumber,
  );
  tryFill(
    [
      'input[autocomplete="cc-exp"]',
      'input[name*="expir" i]',
      'input[name*="exp" i][name*="date" i]',
      'input[id*="expir" i]',
      'input[placeholder*="MM" i]',
    ],
    expiryDate,
  );
  tryFill(
    [
      'input[autocomplete="cc-csc"]',
      'input[name*="cvv" i]',
      'input[name*="cvc" i]',
      'input[id*="cvv" i]',
      'input[placeholder*="CVV" i]',
    ],
    cvv,
  );
  tryFill(
    [
      'input[autocomplete="cc-name"]',
      'input[name*="cardholder" i]',
      'input[id*="cardholder" i]',
      'input[placeholder*="name on card" i]',
    ],
    cardholderName,
  );
  return filled;
}

export function captureCredentials(form: HTMLFormElement) {
  const pw = form.querySelector(
    'input[type="password"]',
  ) as HTMLInputElement | null;
  let username = "";
  for (const s of USERNAME_SELECTORS) {
    const f = form.querySelector(s) as HTMLInputElement | null;
    if (f && f !== pw && f.value) {
      username = f.value;
      break;
    }
  }

  if (pw?.value && username) {
    clearMultiStepUsername();
    return { domain: currentDomain, username, password: pw.value };
  }
  if (pw?.value && !username) {
    const stored = getMultiStepUsername();
    if (stored) {
      clearMultiStepUsername();
      return { domain: currentDomain, username: stored, password: pw.value };
    }
  }
  if (!pw && username) {
    storeMultiStepUsername(username);
    return null;
  }
  return null;
}

export function shouldNeverSave(): boolean {
  return JSON.parse(
    localStorage.getItem("vaultkeeper_never_save") || "[]",
  ).includes(currentDomain);
}

export async function triggerSaveFlow(creds: any) {
  if (shouldNeverSave()) return;
  const existing = await checkExistingCredential(creds.domain, creds.username);
  let isUpdateMode = false;
  let existingCredentialId = null;

  if (existing) {
    if (existing.password === creds.password) return;
    isUpdateMode = true;
    existingCredentialId = existing.id;
  }

  storePendingCredentials(creds, isUpdateMode, existingCredentialId);
  uiBridge.showPrompt({
    credentials: creds,
    isUpdateMode,
    showUnlockForm: false,
    credentialId: existingCredentialId,
  });
}

export function setupFormInterception() {
  if ((document as any)._vkIntercept) return;
  (document as any)._vkIntercept = true;

  document.addEventListener(
    "submit",
    (e) => {
      const form = e.target as HTMLFormElement;
      if (form.tagName !== "FORM") return;
      const creds = captureCredentials(form);
      if (creds) setTimeout(() => triggerSaveFlow(creds), 500);
    },
    true,
  );

  document.addEventListener(
    "click",
    (e) => {
      const btn = (e.target as HTMLElement).closest(
        'button[type="submit"], input[type="submit"], button:not([type])',
      );
      if (!btn) return;
      const form = btn.closest("form") as HTMLFormElement | null;
      if (!form) return;
      const creds = captureCredentials(form);
      if (creds) setTimeout(() => triggerSaveFlow(creds), 500);
    },
    true,
  );

  document.addEventListener(
    "keydown",
    (e) => {
      if (e.key !== "Enter") return;
      const field = e.target as HTMLInputElement;
      const form = field.closest("form") as HTMLFormElement | null;
      if (!form) return;
      if (
        field.type === "password" ||
        USERNAME_SELECTORS.some((s) => field.matches(s))
      ) {
        const creds = captureCredentials(form);
        if (creds) setTimeout(() => triggerSaveFlow(creds), 500);
      }
    },
    true,
  );
}

export function requestCredentials(
  targetField: HTMLInputElement | null = null,
  isFocus = false,
) {
  browser.runtime
    .sendMessage({ action: "get_credentials", domain: currentDomain })
    .then((response: any) => {
      if (response?.success && response.credentials?.length > 0) {
        const creds = response.credentials;
        if ((creds.length > 1 || isFocus) && targetField) {
          uiBridge.showDropdown({ credentials: creds, targetField });
        } else {
          const cred = creds[0];
          const performFill = (code: string | null = null) => {
            const filled = fillCredentials(cred.username, cred.password, code);
            if (filled) {
              if (state.detectedFields?.isMultiStep) {
                if (
                  state.detectedFields.username &&
                  !state.detectedFields.password
                )
                  uiBridge.showNotification(
                    "Email/username filled!",
                    "success",
                  );
                else if (
                  state.detectedFields.password &&
                  !state.detectedFields.username
                )
                  uiBridge.showNotification("Password filled!", "success");
                else
                  uiBridge.showNotification("Credentials filled!", "success");
              } else
                uiBridge.showNotification("Credentials filled!", "success");
            } else
              uiBridge.showNotification("Could not fill credentials", "error");
          };

          if (cred.totp_secret || cred.id) {
            browser.runtime
              .sendMessage({ action: "get_totp", id: cred.id })
              .then((r: any) => performFill(r.success ? r.code : null))
              .catch(() => performFill(null));
          } else performFill(null);
        }
      } else if (response?.locked) {
        if (!isFocus)
          uiBridge.showPrompt({
            showUnlockForm: true,
            unlockContext: "fill",
            targetField,
          });
      } else {
        if (!isFocus)
          uiBridge.showNotification("No credentials found", "error");
      }
    })
    .catch(() => {
      if (!isFocus) uiBridge.showNotification("Connection error", "error");
    });
}
