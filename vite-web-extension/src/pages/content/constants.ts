export const currentDomain = window.location.hostname;
export const MULTISTEP_STORAGE_KEY = "vaultkeeper_multistep_";
export const PENDING_CREDENTIALS_KEY = "vaultkeeper_pending_credentials";

export const USERNAME_SELECTORS = [
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
  'input[type="text"][name*="user" i]',
  'input[type="text"][name*="login" i]',
  'input[type="text"][name*="email" i]',
  'input[type="text"][id*="user" i]',
  'input[type="text"][id*="login" i]',
  'input[type="text"][id*="email" i]',
];

export const PASSWORD_SELECTORS = [
  'input[type="password"]',
  'input[autocomplete="current-password"]',
  'input[autocomplete="new-password"]',
];

export const TOTP_SELECTORS = [
  'input[name="totp" i]',
  'input[name="code" i]',
  'input[name="otp" i]',
  'input[name*="2fa" i]',
  'input[id*="totp" i]',
  'input[id*="otp" i]',
  'input[autocomplete="one-time-code"]',
  'input[placeholder*="code" i]',
  'input[placeholder*="6-digit" i]',
];

export const state = {
  detectedFields: null as {
    username: HTMLInputElement | null;
    password: HTMLInputElement | null;
    form: HTMLFormElement | null;
    isMultiStep: boolean;
  } | null,
};
