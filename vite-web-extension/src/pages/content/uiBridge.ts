export const uiBridge = {
  showPrompt: (config: any) => {},
  hidePrompt: () => {},
  showNotification: (msg: string, type: "success" | "error" = "success") => {},
  showDropdown: (config: {
    credentials: any[];
    targetField: HTMLInputElement;
  }) => {},
  hideDropdown: () => {},
  addFieldIcon: (
    field: HTMLInputElement,
    type: "password" | "username" | "totp",
  ) => {},
};
