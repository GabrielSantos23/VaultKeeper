import { useEffect, useState, useMemo, useCallback } from "react";
import {
  CheckmarkSquare01Icon,
  Alert02Icon,
  RefreshIcon,
  ArrowUpDownIcon,
  Clock01Icon,
  SecurityCheckIcon,
  Link01Icon,
  ShieldUserIcon,
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { useVaultStore, Credential } from "../stores/vaultStore";
import { open } from "@tauri-apps/plugin-shell";

interface Incident {
  credential: Credential;
  issue_type: "LEAKED" | "REUSED" | "WEAK";
  details?: string;
  breachCount?: number;
}

type Category = "action_required" | "leaked" | "reused" | "weak";

interface SecurityReport {
  total_items: number;
  weak_passwords: number;
  reused_passwords: number;
  compromised_passwords: number;
  unsecured_websites: number;
  overall_score: number;
  last_scan: string;
  avg_age_days: number;
  two_fa_count: number;
  incidents: Incident[];
}

interface NavTabProps {
  title: string;
  count: number;
  isActive: boolean;
  onClick: () => void;
  alert?: boolean;
}

function NavTab({ title, count, isActive, onClick, alert }: NavTabProps) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-3 transition-colors border-b-2 ${
        isActive
          ? "border-primary text-primary"
          : "border-transparent text-muted-foreground hover:text-foreground"
      }`}
    >
      <span className="text-sm font-semibold">{title}</span>
      <span
        className={`text-xs font-bold px-2 py-0.5 rounded ${
          isActive && alert
            ? "bg-destructive text-destructive-foreground"
            : isActive
              ? "bg-primary/20 text-primary"
              : "bg-muted text-muted-foreground"
        }`}
      >
        {count}
      </span>
    </button>
  );
}

interface IncidentItemProps {
  credential: Credential;
  issueType: "LEAKED" | "REUSED" | "WEAK";
  details?: string;
  breachCount?: number;
}

function IncidentItem({ credential, issueType, details, breachCount }: IncidentItemProps) {
  const themeColors: Record<string, string> = {
    LEAKED: "text-destructive bg-destructive/10",
    WEAK: "text-destructive bg-destructive/10",
    REUSED: "text-amber-500 bg-amber-500/10",
  };

  const issueLabels: Record<string, string> = {
    LEAKED: "LEAKED",
    WEAK: "WEAK",
    REUSED: "REUSED",
  };

  const issueIcons: Record<string, string> = {
    LEAKED: "!",
    WEAK: "!",
    REUSED: "⇄",
  };

  const handleUpdatePassword = async () => {
    let url = credential.domain;
    if (!url.startsWith("http")) {
      url = "https://" + url;
    }
    await open(url);
  };

  return (
    <div className="flex items-center gap-4 px-4 py-3 bg-card rounded-xl border border-border">
      <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center text-foreground font-bold text-sm flex-shrink-0">
        {credential.domain?.slice(0, 1).toUpperCase() || "?"}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className="font-semibold text-foreground text-sm">
            {credential.domain}
          </span>
          <span
            className={`text-xs font-bold px-2 py-0.5 rounded ${themeColors[issueType]}`}
          >
            {issueIcons[issueType]} {issueLabels[issueType]}
          </span>
        </div>
        <p className="text-xs text-muted-foreground truncate">
          {credential.username}
          {details && ` • ${details}`}
          {breachCount && breachCount > 0 && ` • Found in ${breachCount.toLocaleString()} breaches`}
        </p>
      </div>

      <button
        onClick={handleUpdatePassword}
        className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold bg-primary text-primary-foreground hover:opacity-90 transition-opacity"
      >
        <HugeiconsIcon icon={Link01Icon} size={14} />
        Update Password
      </button>
    </div>
  );
}

interface HealthCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  progress?: number;
  progressColor?: string;
  icon: React.ComponentType<any>;
}

function HealthCard({
  title,
  value,
  subtitle,
  progress,
  progressColor = "bg-primary",
  icon,
}: HealthCardProps) {
  return (
    <div className="flex-1 bg-card rounded-xl border border-border p-5">
      <div className="flex items-start justify-between mb-3">
        <span className="text-sm font-medium text-foreground">{title}</span>
        <HugeiconsIcon icon={icon} size={16} className="text-muted-foreground" />
      </div>
      <div className="flex items-baseline gap-2 mb-3">
        <span className="text-2xl font-bold text-foreground">{value}</span>
        {subtitle && (
          <span className="text-xs text-muted-foreground">{subtitle}</span>
        )}
      </div>
      {progress !== undefined && (
        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${progressColor}`}
            style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
          />
        </div>
      )}
    </div>
  );
}

function CircularScore({ score }: { score: number }) {
  const circumference = 2 * Math.PI * 28;
  const dashOffset = circumference - (score / 100) * circumference;
  const colorClass = score >= 60 ? "text-primary" : "text-destructive";

  return (
    <div className="relative w-16 h-16">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 64 64">
        <circle
          cx="32"
          cy="32"
          r="28"
          fill="none"
          strokeWidth="6"
          className="stroke-muted"
        />
        <circle
          cx="32"
          cy="32"
          r="28"
          fill="none"
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          className={`transition-all duration-700 ease-out stroke-current ${colorClass}`}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-lg font-bold text-foreground">{score}</span>
      </div>
    </div>
  );
}

// Compute SHA-1 hash of a string
async function sha1(message: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(message);
  const hashBuffer = await crypto.subtle.digest('SHA-1', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('').toUpperCase();
}

// Check password against Have I Been Pwned API using k-Anonymity
async function checkHIBP(password: string): Promise<{ found: boolean; count: number }> {
  try {
    const hash = await sha1(password);
    const prefix = hash.slice(0, 5);
    const suffix = hash.slice(5);

    const response = await fetch(`https://api.pwnedpasswords.com/range/${prefix}`, {
      headers: {
        'Add-Padding': 'true'
      }
    });

    if (!response.ok) {
      throw new Error(`HIBP API error: ${response.status}`);
    }

    const text = await response.text();
    const lines = text.split('\n');

    for (const line of lines) {
      const [hashSuffix, countStr] = line.trim().split(':');
      if (hashSuffix === suffix) {
        return { found: true, count: parseInt(countStr, 10) };
      }
    }

    return { found: false, count: 0 };
  } catch (error) {
    console.error('HIBP check failed:', error);
    return { found: false, count: 0 };
  }
}

// Common weak passwords
const COMMON_PASSWORDS = new Set([
  "password", "123456", "12345678", "qwerty", "abc123", "monkey", "letmein",
  "dragon", "111111", "baseball", "iloveyou", "trustno1", "sunshine",
  "princess", "admin", "welcome", "shadow", "ashley", "football", "jesus",
  "michael", "ninja", "mustang", "password1", "123456789", "adobe123",
  "admin123", "login", "master", "photoshop", "1q2w3e4r", "zaq12wsx",
  "password123", "qwerty123", "lovely", "whatever", "starwars", "1234567",
  "1234567890", "000000", "555555", "654321", "121212", "7777777", "696969"
]);

// Cache for HIBP results to avoid redundant API calls
const hibpCache = new Map<string, { found: boolean; count: number }>();

async function analyzeSecurity(
  credentials: Credential[],
  checkCompromised: boolean
): Promise<SecurityReport> {
  const incidents: Incident[] = [];
  const passwordMap = new Map<string, Credential[]>();
  const compromisedPasswords = new Set<string>();
  
  let weakCount = 0;
  let reusedCount = 0;
  let compromisedCount = 0;
  let unsecuredCount = 0;
  let totalAgeDays = 0;
  let twoFaCount = 0;

  const now = new Date();

  // Group credentials by password to find reused passwords
  for (const cred of credentials) {
    const existing = passwordMap.get(cred.password) || [];
    existing.push(cred);
    passwordMap.set(cred.password, existing);

    if (cred.totp_secret) {
      twoFaCount++;
    }

    if (cred.created_at) {
      const created = new Date(cred.created_at);
      const ageDays = Math.floor((now.getTime() - created.getTime()) / (1000 * 60 * 60 * 24));
      totalAgeDays += ageDays;
    }

    if (cred.domain && cred.domain.startsWith("http://")) {
      unsecuredCount++;
    }
  }

  // Check for compromised passwords if network scan is enabled
  if (checkCompromised) {
    const uniquePasswords = Array.from(passwordMap.keys());
    const batchSize = 5; // Process in small batches to avoid rate limiting
    
    for (let i = 0; i < uniquePasswords.length; i += batchSize) {
      const batch = uniquePasswords.slice(i, i + batchSize);
      const results = await Promise.all(
        batch.map(async (password) => {
          if (hibpCache.has(password)) {
            return { password, result: hibpCache.get(password)! };
          }
          const result = await checkHIBP(password);
          hibpCache.set(password, result);
          return { password, result };
        })
      );

      for (const { password, result } of results) {
        if (result.found) {
          compromisedPasswords.add(password);
          const credsWithPassword = passwordMap.get(password) || [];
          compromisedCount += credsWithPassword.length;
          
          for (const cred of credsWithPassword) {
            incidents.push({
              credential: cred,
              issue_type: "LEAKED",
              details: "Password found in data breaches",
              breachCount: result.count
            });
          }
        }
      }
    }
  }

  // Find weak and reused passwords
  for (const cred of credentials) {
    // Skip if already marked as compromised
    if (compromisedPasswords.has(cred.password)) {
      continue;
    }

    // Check weak password
    const isWeak = cred.password.length < 8 || 
                   COMMON_PASSWORDS.has(cred.password.toLowerCase()) ||
                   /^\d+$/.test(cred.password) ||
                   /^[a-zA-Z]+$/.test(cred.password);
    
    if (isWeak) {
      weakCount++;
      incidents.push({
        credential: cred,
        issue_type: "WEAK",
        details: cred.password.length < 8 
          ? `Only ${cred.password.length} characters`
          : "Common or simple password"
      });
      continue;
    }

    // Check reused password
    const samePasswordCreds = passwordMap.get(cred.password) || [];
    if (samePasswordCreds.length > 1) {
      const isFirstOccurrence = samePasswordCreds[0].id === cred.id;
      if (isFirstOccurrence) {
        reusedCount += samePasswordCreds.length;
        for (const reusedCred of samePasswordCreds) {
          incidents.push({
            credential: reusedCred,
            issue_type: "REUSED",
            details: `Shared with ${samePasswordCreds.length - 1} other site${samePasswordCreds.length > 2 ? 's' : ''}`
          });
        }
      }
    }
  }

  const avgAgeDays = credentials.length > 0 ? Math.round(totalAgeDays / credentials.length) : 0;

  // Calculate score
  let score = 100;
  if (credentials.length > 0) {
    const weakPenalty = (weakCount / credentials.length) * 25;
    const reusedPenalty = (reusedCount / credentials.length) * 20;
    const compromisedPenalty = (compromisedCount / credentials.length) * 35;
    const unsecuredPenalty = (unsecuredCount / credentials.length) * 5;
    const agePenalty = Math.min(15, (avgAgeDays / 365) * 10);
    
    score = Math.max(0, Math.round(100 - weakPenalty - reusedPenalty - compromisedPenalty - unsecuredPenalty - agePenalty));
  }

  return {
    total_items: credentials.length,
    weak_passwords: weakCount,
    reused_passwords: reusedCount,
    compromised_passwords: compromisedCount,
    unsecured_websites: unsecuredCount,
    overall_score: score,
    last_scan: new Date().toISOString(),
    avg_age_days: avgAgeDays,
    two_fa_count: twoFaCount,
    incidents,
  };
}

export function SecurityDashboard() {
  const [report, setReport] = useState<SecurityReport | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [activeCategory, setActiveCategory] = useState<Category>("action_required");
  const [expandedIncidents, setExpandedIncidents] = useState(false);
  const [lastScanTime, setLastScanTime] = useState<string>("");
  const [hasRunNetworkScan, setHasRunNetworkScan] = useState(false);
  
  const credentials = useVaultStore((state) => state.credentials);
  const loadVaultData = useVaultStore((state) => state.loadVaultData);

  const runSecurityCheck = useCallback(async (networkScan = false) => {
    if (credentials.length === 0) {
      await loadVaultData();
      return;
    }

    setIsScanning(true);
    try {
      const result = await analyzeSecurity(credentials, networkScan);
      setReport(result);
      setLastScanTime(new Date().toLocaleString());
      if (networkScan) {
        setHasRunNetworkScan(true);
      }
    } catch (error) {
      console.error("Security scan failed:", error);
    } finally {
      setIsScanning(false);
    }
  }, [credentials, loadVaultData]);

  // Initial scan (local only, no network)
  useEffect(() => {
    if (credentials.length > 0 && !report) {
      runSecurityCheck(false);
    }
  }, [credentials.length, report, runSecurityCheck]);

  const filteredIncidents = useMemo(() => {
    if (!report) return [];
    
    switch (activeCategory) {
      case "action_required":
        return report.incidents;
      case "leaked":
        return report.incidents.filter((i) => i.issue_type === "LEAKED");
      case "reused":
        return report.incidents.filter((i) => i.issue_type === "REUSED");
      case "weak":
        return report.incidents.filter((i) => i.issue_type === "WEAK");
      default:
        return report.incidents;
    }
  }, [report, activeCategory]);

  const leakedCount = report?.incidents.filter((i) => i.issue_type === "LEAKED").length || 0;
  const reusedCount = report?.incidents.filter((i) => i.issue_type === "REUSED").length || 0;
  const weakCount = report?.incidents.filter((i) => i.issue_type === "WEAK").length || 0;
  const totalAction = leakedCount + reusedCount + weakCount;

  const displayedIncidents = expandedIncidents
    ? filteredIncidents
    : filteredIncidents.slice(0, 5);

  const remainingCount = filteredIncidents.length - displayedIncidents.length;

  const score = report?.overall_score ?? 0;
  const avgAge = report?.avg_age_days ?? 0;
  const twoFaCount = report?.two_fa_count ?? 0;
  const totalItems = report?.total_items ?? 1;
  const compromisedCount = report?.compromised_passwords ?? 0;

  const ageProgress = Math.max(0, Math.min(100, 100 - avgAge / 3.65));
  const twoFaProgress = Math.round((twoFaCount / totalItems) * 100);

  return (
    <div className="flex-1 h-full overflow-y-auto bg-background">
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="px-10 pt-8 pb-6">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-foreground mb-1">
                Watchtower
              </h1>
              <p className="text-sm text-muted-foreground">
                Unified Security Remediation Dashboard
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-card text-foreground text-sm font-semibold border border-border hover:bg-muted transition-colors">
                <HugeiconsIcon icon={ArrowUpDownIcon} size={14} />
                Sort by Severity
              </button>
              <button
                onClick={() => runSecurityCheck(true)}
                disabled={isScanning}
                className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                <HugeiconsIcon
                  icon={RefreshIcon}
                  size={14}
                  className={isScanning ? "animate-spin" : ""}
                />
                {isScanning ? "Scanning..." : hasRunNetworkScan ? "Scan Again" : "Full Scan"}
              </button>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-border">
            <NavTab
              title="Action Required"
              count={totalAction}
              isActive={activeCategory === "action_required"}
              onClick={() => {
                setActiveCategory("action_required");
                setExpandedIncidents(false);
              }}
              alert={totalAction > 0}
            />
            <NavTab
              title="Leaked Passwords"
              count={leakedCount}
              isActive={activeCategory === "leaked"}
              onClick={() => {
                setActiveCategory("leaked");
                setExpandedIncidents(false);
              }}
              alert={leakedCount > 0}
            />
            <NavTab
              title="Reused Passwords"
              count={reusedCount}
              isActive={activeCategory === "reused"}
              onClick={() => {
                setActiveCategory("reused");
                setExpandedIncidents(false);
              }}
            />
            <NavTab
              title="Weak Passwords"
              count={weakCount}
              isActive={activeCategory === "weak"}
              onClick={() => {
                setActiveCategory("weak");
                setExpandedIncidents(false);
              }}
              alert={weakCount > 0}
            />
          </div>
        </div>

        {/* Divider */}
        <div className="h-px bg-border" />

        {/* Content */}
        <div className="flex-1 px-10 py-8 overflow-y-auto">
          {report && credentials.length > 0 ? (
            <div className="space-y-8">
              {/* Compromised Passwords Banner */}
              {compromisedCount > 0 && (
                <div className="bg-destructive/10 border border-destructive/30 rounded-xl p-4 flex items-center gap-4">
                  <HugeiconsIcon icon={Alert02Icon} size={24} className="text-destructive flex-shrink-0" />
                  <div>
                    <p className="text-sm font-semibold text-destructive">
                      Compromised Passwords Detected
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {compromisedCount} of your passwords were found in known data breaches. Change them immediately.
                    </p>
                  </div>
                </div>
              )}

              {/* Active Incidents */}
              <div>
                <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4">
                  Active Incidents
                </h2>
                <div className="space-y-3">
                  {displayedIncidents.length > 0 ? (
                    <>
                      {displayedIncidents.map((incident, idx) => (
                        <IncidentItem
                          key={`${incident.credential.id}-${idx}`}
                          credential={incident.credential}
                          issueType={incident.issue_type}
                          details={incident.details}
                          breachCount={incident.breachCount}
                        />
                      ))}
                      {(remainingCount > 0 || expandedIncidents) && (
                        <div className="flex justify-center pt-2">
                          <button
                            onClick={() => setExpandedIncidents(!expandedIncidents)}
                            className="px-6 py-2.5 rounded-full bg-card text-primary text-sm font-semibold border border-border hover:bg-muted transition-colors"
                          >
                            {expandedIncidents
                              ? "Show Less"
                              : `Show ${remainingCount} more incidents...`}
                          </button>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                      <div className="w-16 h-16 rounded-2xl flex items-center justify-center bg-primary/10 mb-4">
                        <HugeiconsIcon
                          icon={CheckmarkSquare01Icon}
                          size={28}
                          className="text-primary"
                        />
                      </div>
                      <p className="text-sm font-medium text-foreground mb-1">
                        No incidents found. Good job!
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Your vault is secure and well-protected
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Divider */}
              <div className="h-px bg-border" />

              {/* Health Summary */}
              <div>
                <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4">
                  System Health Summary
                </h2>
                <div className="flex gap-5">
                  {/* Security Score Card */}
                  <div className="flex-1 bg-card rounded-xl border border-border p-5 flex items-center gap-4">
                    <CircularScore score={score} />
                    <div>
                      <p className="text-sm font-semibold text-foreground">
                        Security Score
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Overall Rating: {score >= 80 ? "Excellent" : score >= 60 ? "Good" : "At Risk"}
                      </p>
                    </div>
                  </div>

                  <HealthCard
                    title="Password Age"
                    value={`${avgAge}d`}
                    progress={ageProgress}
                    progressColor={avgAge > 365 ? "bg-destructive" : avgAge > 180 ? "bg-amber-500" : "bg-green-500"}
                    icon={Clock01Icon}
                  />

                  <HealthCard
                    title="2FA Adoption"
                    value={`${twoFaCount}/${totalItems}`}
                    subtitle={`${twoFaProgress}% enabled`}
                    progress={twoFaProgress}
                    progressColor="bg-green-500"
                    icon={SecurityCheckIcon}
                  />
                </div>
              </div>

              {/* Footer */}
              <p className="text-center text-xs font-bold text-muted-foreground uppercase tracking-wider pt-4">
                WATCHTOWER SCANNING ENGINE V4.2.1 • LAST FULL AUDIT:{" "}
                {lastScanTime || "JUST NOW"}
                {!hasRunNetworkScan && " • LOCAL SCAN ONLY"}
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full gap-4">
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center bg-muted">
                <HugeiconsIcon
                  icon={ShieldUserIcon}
                  size={28}
                  className="text-muted-foreground/40"
                />
              </div>
              <div className="text-center">
                <p className="text-sm font-medium text-foreground mb-1">
                  {isScanning ? "Running security scan..." : credentials.length === 0 ? "No credentials found" : "Ready to scan"}
                </p>
                <p className="text-xs text-muted-foreground">
                  {isScanning
                    ? "Analysing your vault credentials"
                    : credentials.length === 0
                      ? "Add some credentials to see your security report"
                      : "Click Full Scan to check for compromised passwords"}
                </p>
              </div>
              {!isScanning && credentials.length > 0 && (
                <button
                  onClick={() => runSecurityCheck(true)}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-primary-foreground transition-colors bg-primary hover:opacity-90"
                >
                  <HugeiconsIcon icon={RefreshIcon} size={14} />
                  Full Scan
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
