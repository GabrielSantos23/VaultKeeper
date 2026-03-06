import React, { useState, useEffect } from "react";
import { Icons } from "./Icons";
import { requestCredentials } from "../core";

export const FieldIcon = ({
  field,
  type,
  onRemove,
}: {
  field: HTMLInputElement;
  type: string;
  onRemove: () => void;
}) => {
  const [style, setStyle] = useState({ display: "none", top: 0, left: 0 });

  useEffect(() => {
    const updatePosition = () => {
      const rect = field.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) return onRemove();
      const st = window.getComputedStyle(field);
      const pr = parseFloat(st.paddingRight) || 0;
      setStyle({
        display: "block",
        top: rect.top + window.scrollY + (rect.height - 24) / 2,
        left: rect.left + window.scrollX + rect.width - pr - 30,
      });
    };
    updatePosition();
    const ro = new ResizeObserver(updatePosition);
    ro.observe(field);
    window.addEventListener("resize", updatePosition);
    document.addEventListener("scroll", updatePosition, true);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", updatePosition);
      document.removeEventListener("scroll", updatePosition, true);
    };
  }, [field, onRemove]);

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (type === "totp") {
      field.focus();
    } else {
      requestCredentials(field);
    }
  };

  return (
    <div
      onClick={handleClick}
      className={`absolute! cursor-pointer! z-2147483647 flex! w-6! h-6! rounded-md! bg-background! border! border-border! text-primary! opacity-70! transition-all! duration-200! hover:opacity-100! hover:bg-accent! items-center! justify-center! animate-[vk-pulse-ring_2s_ease-out_1] ${type === "username" ? "hover:shadow-md! hover:scale-110!" : "hover:scale-110!"}`}
      style={{
        display: style.display,
        top: `${style.top}px`,
        left: `${style.left}px`,
      }}
    >
      <Icons.Lock size={15} color="currentColor" strokeWidth={2.5} />
    </div>
  );
};
