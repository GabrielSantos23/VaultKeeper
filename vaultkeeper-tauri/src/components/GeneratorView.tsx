import { useState, useCallback, useEffect } from "react";
import {
  RefreshIcon,
  Copy01Icon,
  CheckmarkCircle01Icon,
  Settings02Icon,
  FlashIcon,
  InformationCircleIcon,
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { invoke } from "@tauri-apps/api/core";
import { writeText } from "@tauri-apps/plugin-clipboard-manager";
import { Switch } from "@/components/ui/switch";

const STRENGTH_CONFIG = [
  {
    label: "Very Weak",
    colorClass: "bg-destructive",
    textClass: "text-destructive",
  },
  {
    label: "Weak",
    colorClass: "bg-destructive",
    textClass: "text-destructive",
  },
  { label: "Fair", colorClass: "bg-primary", textClass: "text-primary" },
  { label: "Strong", colorClass: "bg-primary", textClass: "text-primary" },
  { label: "Very Strong", colorClass: "bg-primary", textClass: "text-primary" },
];

const CHARACTER_OPTIONS = [
  { key: "uppercase", label: "Uppercase letters", hint: "A–Z" },
  { key: "lowercase", label: "Lowercase letters", hint: "a–z" },
  { key: "numbers", label: "Numbers", hint: "0–9" },
  { key: "symbols", label: "Special characters", hint: "!@#$%" },
] as const;

function calculateStrength(pwd: string): number {
  let score = 0;
  if (pwd.length >= 8) score++;
  if (pwd.length >= 12) score++;
  if (/[A-Z]/.test(pwd)) score++;
  if (/[0-9]/.test(pwd)) score++;
  if (/[^A-Za-z0-9]/.test(pwd)) score++;
  return Math.min(score, 4);
}

export function GeneratorView() {
  const [password, setPassword] = useState("");
  const [length, setLength] = useState(16);
  const [options, setOptions] = useState({
    uppercase: true,
    lowercase: true,
    numbers: true,
    symbols: true,
  });
  const [copied, setCopied] = useState(false);
  const [strength, setStrength] = useState(0);
  const [generating, setGenerating] = useState(false);

  const hasAnyOption = Object.values(options).some(Boolean);

  const generatePassword = useCallback(
    async (len: number, opts: typeof options) => {
      const anyEnabled = Object.values(opts).some(Boolean);
      if (!anyEnabled) {
        setPassword("");
        setStrength(0);
        return;
      }

      setGenerating(true);
      try {
        const result = await invoke<string>("generate_password", {
          length: len,
          includeUppercase: opts.uppercase,
          includeLowercase: opts.lowercase,
          includeNumbers: opts.numbers,
          includeSymbols: opts.symbols,
        });
        setPassword(result);
        setStrength(calculateStrength(result));
      } catch (error) {
        console.error("Failed to generate password:", error);
      } finally {
        setGenerating(false);
      }
    },
    [],
  );

  useEffect(() => {
    generatePassword(length, options);
  }, [length, options]);

  const copyToClipboard = async () => {
    if (!password) return;
    try {
      await writeText(password);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error("Failed to copy:", error);
    }
  };

  const handleOptionChange = (key: keyof typeof options, value: boolean) => {
    setOptions((prev) => ({ ...prev, [key]: value }));
  };

  const strengthConfig = STRENGTH_CONFIG[strength];

  return (
    <div className="flex-1 h-full overflow-y-auto bg-background">
      <div className="h-full flex flex-col p-6 gap-5">
        <div className="flex items-center gap-3 pb-4 border-b border-border shrink-0">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 bg-primary/10">
            <HugeiconsIcon
              icon={FlashIcon}
              size={20}
              className="text-primary"
            />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-foreground">
              Password Generator
            </h1>
            <p className="text-xs text-muted-foreground">
              Generate strong, customisable passwords instantly
            </p>
          </div>
        </div>

        <div className="flex-1 flex gap-5 min-h-0">
          <div className="flex-1 flex flex-col gap-4 min-w-0">
            <div className="rounded-xl border border-border overflow-hidden">
              <div className="px-5 py-5 flex items-start gap-4 bg-muted">
                {!hasAnyOption ? (
                  <p className="flex-1 text-sm text-muted-foreground/60 italic">
                    Enable at least one character type to generate a password.
                  </p>
                ) : (
                  <p
                    className={`flex-1 font-mono text-lg break-all leading-relaxed select-all ${password ? "text-foreground" : "text-muted-foreground/40"}`}
                  >
                    {password || "Generating…"}
                  </p>
                )}
                <button
                  onClick={copyToClipboard}
                  disabled={!password || !hasAnyOption}
                  title={copied ? "Copied!" : "Copy password"}
                  className={`w-9 h-9 flex items-center justify-center rounded-lg flex-shrink-0 transition-colors disabled:opacity-30 mt-0.5 ${
                    copied
                      ? "text-primary"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <HugeiconsIcon
                    icon={copied ? CheckmarkCircle01Icon : Copy01Icon}
                    size={18}
                  />
                </button>
              </div>

              <div className="px-5 py-3 border-t border-border bg-background flex items-center gap-4">
                <div className="flex-1 flex gap-1.5">
                  {[0, 1, 2, 3].map((i) => (
                    <div
                      key={i}
                      className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${
                        password && i < strength
                          ? strengthConfig.colorClass
                          : "bg-border"
                      }`}
                    />
                  ))}
                </div>
                <span
                  className={`text-xs font-semibold w-20 text-right shrink-0 ${password ? strengthConfig.textClass : "text-muted-foreground"}`}
                >
                  {password ? strengthConfig.label : "—"}
                </span>
              </div>
            </div>

            <button
              onClick={() => generatePassword(length, options)}
              disabled={generating || !hasAnyOption}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold transition-all disabled:opacity-50 shrink-0 bg-primary text-primary-foreground shadow-lg shadow-primary/30 hover:opacity-90"
            >
              <HugeiconsIcon
                icon={RefreshIcon}
                size={16}
                className={generating ? "animate-spin" : ""}
              />
              {generating ? "Generating…" : "Generate New Password"}
            </button>

            <div className="rounded-xl p-5 shrink-0 bg-primary/5 border border-primary/20">
              <div className="flex items-center gap-2 mb-3">
                <HugeiconsIcon
                  icon={InformationCircleIcon}
                  size={14}
                  className="text-primary"
                />
                <h3 className="text-xs font-semibold uppercase tracking-wider text-primary">
                  Security Tips
                </h3>
              </div>
              <ul className="space-y-1.5 text-xs text-muted-foreground">
                <li>Use at least 12 characters for strong security</li>
                <li>Mix letters, numbers, and symbols for best results</li>
                <li>Never reuse passwords across different accounts</li>
                <li>Consider a passphrase if you need to memorise it</li>
              </ul>
            </div>
          </div>

          <div className="w-80 shrink-0 rounded-xl border border-border overflow-hidden flex flex-col self-start">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-border bg-background">
              <HugeiconsIcon
                icon={Settings02Icon}
                size={14}
                className="text-muted-foreground"
              />
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Options
              </span>
            </div>

            <div className="p-4 space-y-5 bg-muted">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Length
                  </label>
                  <span className="text-sm font-bold tabular-nums text-primary">
                    {length}
                  </span>
                </div>
                <input
                  type="range"
                  min={6}
                  max={64}
                  value={length}
                  onChange={(e) => setLength(parseInt(e.target.value))}
                  className="w-full h-1.5 rounded-full appearance-none cursor-pointer bg-border accent-primary"
                />
                <div className="flex justify-between text-xs text-muted-foreground/60">
                  <span>6</span>
                  <span>32</span>
                  <span>64</span>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Include
                </label>
                <div className="space-y-1">
                  {CHARACTER_OPTIONS.map(({ key, label, hint }) => (
                    <div
                      key={key}
                      className="flex items-center justify-between px-3 py-2.5 rounded-lg bg-background"
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <Switch
                          checked={options[key]}
                          onCheckedChange={(val) =>
                            handleOptionChange(key, val)
                          }
                          id={`switch-${key}`}
                        />
                        <label
                          htmlFor={`switch-${key}`}
                          className="text-sm text-foreground cursor-pointer truncate"
                        >
                          {label}
                        </label>
                      </div>
                      <span className="text-xs text-muted-foreground font-mono shrink-0 ml-2">
                        {hint}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
