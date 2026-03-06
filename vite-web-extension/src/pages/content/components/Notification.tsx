import React, { useEffect, useState } from "react";

export const Notification = ({
  message,
  type,
  onClose,
}: {
  message: string;
  type: "success" | "error";
  onClose: () => void;
}) => {
  const [isClosing, setIsClosing] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsClosing(true);
      setTimeout(onClose, 300);
    }, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const isSuccess = type === "success";
  return (
    <div
      className={`fixed bottom-6! right-6! z-2147483647 flex! items-center! gap-2.5! px-4! py-3! rounded-[10px]! text-[13px]! font-medium! tracking-tight! font-['Inter','Segoe_UI',system-ui,sans-serif] bg-popover! border! border-border! pointer-events-auto! ${isClosing ? "animate-[vk-toast-out_0.3s_cubic-bezier(0.4,0,1,1)_forwards]" : "animate-[vk-toast-in_0.4s_cubic-bezier(0.16,1,0.3,1)]"}`}
    >
      <span
        className={
          isSuccess
            ? "text-[#4ade80]! leading-snug! m-0! p-0!"
            : "text-destructive! leading-snug! m-0! p-0!"
        }
      >
        {message}
      </span>
    </div>
  );
};
