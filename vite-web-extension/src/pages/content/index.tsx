import React from "react";
import { createRoot } from "react-dom/client";
import browser from "webextension-polyfill";
import "./style.css";
import { App } from "./components/App";
import { currentDomain, state, TOTP_SELECTORS } from "./constants";
import { getPendingCredentials, setFieldValue, isVisible } from "./helpers";
import {
  detectLoginFields,
  setupFormInterception,
  fillCredentials,
  fillCreditCard,
} from "./core";
import { uiBridge } from "./uiBridge";

browser.runtime.onMessage.addListener((request: any) => {
  switch (request.action) {
    case "fill":
      state.detectedFields = detectLoginFields();
      return Promise.resolve({
        success: fillCredentials(
          request.username,
          request.password,
          request.totp,
        ),
        isMultiStep: state.detectedFields?.isMultiStep || false,
      });
    case "fill_password_only":
      state.detectedFields = detectLoginFields();
      let pwFilled = false;
      if (state.detectedFields?.password) {
        setFieldValue(state.detectedFields.password, request.password);
        pwFilled = true;
      }
      return Promise.resolve({ success: pwFilled });
    case "detect":
      state.detectedFields = detectLoginFields();
      return Promise.resolve({
        hasForm: !!(
          state.detectedFields?.username || state.detectedFields?.password
        ),
        hasPassword: !!state.detectedFields?.password,
        hasUsername: !!state.detectedFields?.username,
        isMultiStep: state.detectedFields?.isMultiStep || false,
        domain: currentDomain,
      });
    case "fill_card":
      return Promise.resolve({
        success: fillCreditCard(
          request.card_number,
          request.expiry_date,
          request.cvv,
          request.cardholder_name,
        ),
      });
  }
});

function initDOMObservers() {
  const pendingData = getPendingCredentials();
  if (pendingData?.credentials) {
    setTimeout(() => {
      uiBridge.showPrompt({
        credentials: pendingData.credentials,
        isUpdateMode: pendingData.isUpdate,
        credentialId: pendingData.credentialId,
        showUnlockForm: false,
      });
    }, 300);
  }

  state.detectedFields = detectLoginFields();
  if (
    state.detectedFields &&
    (state.detectedFields.username || state.detectedFields.password)
  ) {
    if (state.detectedFields.password)
      document
        .querySelectorAll('input[type="password"]')
        .forEach((f) =>
          uiBridge.addFieldIcon(f as HTMLInputElement, "password"),
        );
    if (
      state.detectedFields.isMultiStep &&
      state.detectedFields.username &&
      !state.detectedFields.password
    ) {
      uiBridge.addFieldIcon(state.detectedFields.username, "username");
    }
    setupFormInterception();
  }

  for (const sel of TOTP_SELECTORS) {
    document.querySelectorAll(sel).forEach((f) => {
      if (isVisible(f as HTMLElement))
        uiBridge.addFieldIcon(f as HTMLInputElement, "totp");
    });
  }

  const observer = new MutationObserver(() => {
    const nf = detectLoginFields();
    if (nf) {
      const newPw = nf.password && !state.detectedFields?.password;
      const newUn = nf.username && !state.detectedFields?.username;
      if (newPw || newUn) {
        state.detectedFields = nf;
        if (nf.password)
          document
            .querySelectorAll('input[type="password"]')
            .forEach((f) =>
              uiBridge.addFieldIcon(f as HTMLInputElement, "password"),
            );
        if (nf.isMultiStep && nf.username && !nf.password)
          uiBridge.addFieldIcon(nf.username, "username");
        setupFormInterception();
      }
    }
    for (const sel of TOTP_SELECTORS) {
      document.querySelectorAll(sel).forEach((f) => {
        if (isVisible(f as HTMLElement))
          uiBridge.addFieldIcon(f as HTMLInputElement, "totp");
      });
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });
}

const rootDiv = document.createElement("div");
rootDiv.id = "vaultkeeper-react-root";
document.body.appendChild(rootDiv);

const root = createRoot(rootDiv);
root.render(<App />);

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initDOMObservers);
} else {
  initDOMObservers();
}

console.log("[VaultKeeper] Content script loaded (React Edition)");
