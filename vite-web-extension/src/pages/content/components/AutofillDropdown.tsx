import React, { useRef, useState, useEffect } from "react";
import { uiBridge } from "../uiBridge";
import { setFieldValue } from "../helpers";
import { fillTOTP } from "../core";
import browser from "webextension-polyfill";

export const AutofillDropdown = ({
  config,
  onClose,
}: {
  config: { credentials: any[]; targetField: HTMLInputElement };
  onClose: () => void;
}) => {
  const [style, setStyle] = useState({ top: 0, left: 0, opacity: 0 });
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const rect = config.targetField.getBoundingClientRect();
    setStyle({
      top: rect.bottom + window.scrollY + 6,
      left: rect.left + window.scrollX,
      opacity: 1,
    });

    const handleClickOutside = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        e.target !== config.targetField
      ) {
        onClose();
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("scroll", onClose, true);
    window.addEventListener("resize", onClose);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("scroll", onClose, true);
      window.removeEventListener("resize", onClose);
    };
  }, [config, onClose]);

  const handleSelect = (cred: any) => {
    if (config.targetField.type === "password") {
      setFieldValue(config.targetField, cred.password);
    } else {
      setFieldValue(config.targetField, cred.username);
      const form = config.targetField.closest("form");
      if (form) {
        const pw = form.querySelector('input[type="password"]');
        if (pw) setFieldValue(pw as HTMLInputElement, cred.password);
      }
    }
    if (cred.totp_secret || cred.id) {
      browser.runtime
        .sendMessage({ action: "get_totp", id: cred.id })
        .then((r: any) => {
          if (r.success && r.code) fillTOTP(r.code);
        });
    }
    uiBridge.hideDropdown();
  };

  return (
    <div
      ref={dropdownRef}
      className="absolute! z-2147483647 w-80! bg-popover! border! border-border! rounded-[10px]! shadow-lg! overflow-hidden! font-['Inter','Segoe_UI',system-ui,sans-serif]! animate-[vk-dropdown-in_0.25s_cubic-bezier(0.16,1,0.3,1)]!"
      style={{ top: style.top, left: style.left, opacity: style.opacity }}
    >
      {config.credentials.map((cred, i) => (
        <div
          key={i}
          onClick={() => handleSelect(cred)}
          className="vk-autofill-chevron flex! items-center! gap-3! px-3.5! py-3! cursor-pointer! transition-all! duration-200! border-b! border-border! last:border-b-0! hover:bg-accent! active:bg-accent/50!"
        >
          <div className="w-9! h-9! bg-primary/20! border! border-primary/30! rounded-md! flex! items-center! justify-center! shrink-0!">
            <span className="text-[15px]! font-bold! text-primary!">
              {(cred.domain || "?").charAt(0).toUpperCase()}
            </span>
          </div>
          <div className="flex-1! overflow-hidden! min-w-0!">
            <div className="text-[13px]! font-semibold! text-popover-foreground! truncate! tracking-tight!">
              {cred.domain}
            </div>
            <div className="text-[12px]! text-muted-foreground! truncate! mt-0.5!">
              {cred.username}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
