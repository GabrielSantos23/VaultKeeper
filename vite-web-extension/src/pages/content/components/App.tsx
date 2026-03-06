import React, { useState, useEffect } from "react";
import { uiBridge } from "../uiBridge";
import { Notification } from "./Notification";
import { SavePrompt } from "./SavePrompt";
import { AutofillDropdown } from "./AutofillDropdown";
import { FieldIcon } from "./FieldIcon";

export const App = () => {
  const [notification, setNotification] = useState<{
    message: string;
    type: "success" | "error";
  } | null>(null);
  const [promptConfig, setPromptConfig] = useState<any>(null);
  const [dropdownConfig, setDropdownConfig] = useState<any>(null);
  const [icons, setIcons] = useState<
    { field: HTMLInputElement; type: string; id: string }[]
  >([]);

  useEffect(() => {
    uiBridge.showPrompt = setPromptConfig;
    uiBridge.hidePrompt = () => setPromptConfig(null);
    uiBridge.showNotification = (msg, type) =>
      setNotification({ message: msg, type: type || "success" });
    uiBridge.showDropdown = setDropdownConfig;
    uiBridge.hideDropdown = () => setDropdownConfig(null);
    uiBridge.addFieldIcon = (field, type) => {
      if (
        field.id === "vk-master-password" ||
        field.closest("#vaultkeeper-react-root")
      )
        return;
      setIcons((prev) => {
        if (prev.find((i) => i.field === field)) return prev;
        return [...prev, { field, type, id: Math.random().toString(36) }];
      });
    };
  }, []);

  return (
    <>
      {notification && (
        <Notification
          message={notification.message}
          type={notification.type}
          onClose={() => setNotification(null)}
        />
      )}
      {promptConfig && (
        <SavePrompt
          config={promptConfig}
          onClose={() => setPromptConfig(null)}
        />
      )}
      {dropdownConfig && (
        <AutofillDropdown
          config={dropdownConfig}
          onClose={() => setDropdownConfig(null)}
        />
      )}
      {icons.map((icon) => (
        <FieldIcon
          key={icon.id}
          field={icon.field}
          type={icon.type}
          onRemove={() =>
            setIcons((prev) => prev.filter((i) => i.id !== icon.id))
          }
        />
      ))}
    </>
  );
};
