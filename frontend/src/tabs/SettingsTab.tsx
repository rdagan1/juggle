import { useEffect, useState } from "react";
import { settingsApi, type UserSettings } from "../api/client";
import { useAuth } from "../hooks/useAuth";
import { he } from "../i18n/he";

function SettingsSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="bg-white rounded-xl border border-navy-100 overflow-hidden">
      <div className="px-4 py-3 border-b border-navy-100 bg-navy-50">
        <h2 className="text-sm font-bold text-slate-700">{title}</h2>
      </div>
      <div className="p-4 flex flex-col gap-3">{children}</div>
    </section>
  );
}

export function SettingsTab() {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [saved, setSaved] = useState(false);
  const [manualUpdates, setManualUpdates] = useState<unknown[]>([]);
  const { logout } = useAuth();

  useEffect(() => {
    settingsApi.get().then(({ data }) => setSettings(data)).finally(() => setIsLoading(false));
    settingsApi.getManualUpdates().then(({ data }) => setManualUpdates(data.logs ?? []));
  }, []);

  const copyVirtualEmail = () => {
    if (!settings?.virtual_email) return;
    navigator.clipboard.writeText(settings.virtual_email);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const updatePref = async (key: string, value: unknown) => {
    if (!settings) return;
    const updated = { ...settings.preferences, [key]: value };
    setSettings({ ...settings, preferences: updated });
    await settingsApi.update({ [key]: value });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleDeleteAccount = async () => {
    if (!window.confirm(he.settings.deleteConfirm)) return;
    await settingsApi.deleteAccount();
    logout();
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center text-slate-400">טוען...</div>
    );
  }

  const prefs = settings?.preferences ?? {};

  return (
    <div
      id="panel-settings"
      role="tabpanel"
      aria-label={he.tabs.settings}
      className="flex flex-col h-full bg-navy-50 overflow-y-auto pb-8"
      dir="rtl"
    >
      <header className="px-4 pt-5 pb-3 flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-800">{he.settings.title}</h1>
        {saved && <span className="text-xs text-green-600">{he.settings.saved}</span>}
      </header>

      <div className="flex flex-col gap-4 px-4">
        {/* ─── Account ─────────────────────────────────────────────────────────── */}
        <SettingsSection title={he.settings.sections.account}>
          {settings?.name && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">{he.auth.nameLabel}</span>
              <span className="text-sm text-slate-700 font-medium">{settings.name}</span>
            </div>
          )}
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500">{he.auth.emailLabel}</span>
            <span className="text-sm text-slate-700 font-medium" dir="ltr">{settings?.email ?? "—"}</span>
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-xs text-slate-500">{he.settings.virtualEmail}</span>
            <div className="flex items-center gap-2">
              <p className="flex-1 font-mono text-sm text-gray-800 truncate" dir="ltr">
                {settings?.virtual_email ?? "—"}
              </p>
              <button
                onClick={copyVirtualEmail}
                className="text-xs text-gio-500 font-medium min-h-[36px] px-3 border border-gio-500 rounded-lg hover:bg-gio-50 transition-colors"
                aria-label={he.settings.copyEmail}
              >
                {copied ? he.settings.copied : he.settings.copyEmail}
              </button>
            </div>
          </div>
          <div className="flex flex-col gap-2 pt-1">
            <button
              onClick={logout}
              className="w-full py-3 border border-navy-200 rounded-xl text-sm text-slate-600 hover:bg-navy-50 min-h-[44px] transition-colors"
              aria-label={he.settings.logout}
            >
              {he.settings.logout}
            </button>
            <button
              onClick={handleDeleteAccount}
              className="w-full py-3 border border-red-300 rounded-xl text-sm text-red-600 hover:bg-red-50 min-h-[44px] transition-colors"
              aria-label={he.settings.deleteAccount}
            >
              {he.settings.deleteAccount}
            </button>
          </div>
        </SettingsSection>

        {/* ─── Notifications ───────────────────────────────────────────────────── */}
        <SettingsSection title={he.settings.sections.notifications}>
          <div className="flex flex-col gap-1">
            <p className="text-sm font-medium text-slate-700">{he.settings.quietHours}</p>
            <div className="flex items-center gap-3">
              <div className="flex flex-col gap-1 flex-1">
                <label className="text-xs text-slate-500" htmlFor="quiet-start">{he.settings.quietStart}</label>
                <input
                  id="quiet-start"
                  type="time"
                  defaultValue={(prefs.quiet_hours_start as string) ?? "23:00"}
                  onChange={(e) => updatePref("quiet_hours_start", e.target.value)}
                  className="border border-navy-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-gio-500"
                />
              </div>
              <div className="flex flex-col gap-1 flex-1">
                <label className="text-xs text-slate-500" htmlFor="quiet-end">{he.settings.quietEnd}</label>
                <input
                  id="quiet-end"
                  type="time"
                  defaultValue={(prefs.quiet_hours_end as string) ?? "07:00"}
                  onChange={(e) => updatePref("quiet_hours_end", e.target.value)}
                  className="border border-navy-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-gio-500"
                />
              </div>
            </div>
          </div>
          <div className="-mx-4 px-4 pb-1">
            <label htmlFor="grade-threshold" className="text-sm font-medium text-slate-700 mb-2 block">
              {he.settings.gradeThreshold}: {prefs.grade_alert_threshold ?? 70}
            </label>
            <input
              id="grade-threshold"
              type="range"
              min={50}
              max={100}
              step={5}
              defaultValue={Number(prefs.grade_alert_threshold ?? 70)}
              onChange={(e) => updatePref("grade_alert_threshold", Number(e.target.value))}
              className="w-full accent-gio-500"
              aria-label={he.settings.gradeThreshold}
            />
          </div>
        </SettingsSection>

        {/* ─── Calendar ────────────────────────────────────────────────────────── */}
        <SettingsSection title={he.settings.sections.calendar}>
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-600">{he.settings.personalCalendar}</span>
            {settings?.has_calendar ? (
              <span className="text-xs text-green-600 font-medium">{he.settings.calendar.connected}</span>
            ) : (
              <a
                href="/auth/google-calendar"
                className="text-xs text-gio-500 font-medium min-h-[36px] px-3 border border-gio-500 rounded-lg hover:bg-gio-50 flex items-center"
              >
                {he.settings.calendar.connect}
              </a>
            )}
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-600">{he.settings.workCalendar}</span>
            {settings?.has_work_calendar ? (
              <span className="text-xs text-green-600 font-medium">{he.settings.calendar.connected}</span>
            ) : (
              <a
                href="/auth/google-calendar?calendar_type=work"
                className="text-xs text-gio-500 font-medium min-h-[36px] px-3 border border-gio-500 rounded-lg hover:bg-gio-50 flex items-center"
              >
                {he.settings.calendar.connectWork}
              </a>
            )}
          </div>
          {(settings?.has_calendar || settings?.has_work_calendar) && (
            <div className="divide-y divide-navy-50 -mx-4 -mb-4 rounded-b-xl overflow-hidden border-t border-navy-100 mt-1">
              <ToggleRow
                label={he.settings.calendar.gcalAutoSync}
                checked={prefs.gcal_auto_sync === true}
                onChange={(v) => updatePref("gcal_auto_sync", v || null)}
                ariaLabel={he.settings.calendar.gcalAutoSync}
              />
              {prefs.gcal_auto_sync === true && (
                <p className="px-4 pb-3 text-xs text-slate-400">{he.settings.calendar.gcalAutoSyncHint}</p>
              )}
            </div>
          )}
        </SettingsSection>

        {/* ─── Study Profile ───────────────────────────────────────────────────── */}
        <SettingsSection title={he.settings.sections.studyProfile}>
          <div className="divide-y divide-navy-50 -mx-4 -mt-4 rounded-t-none overflow-hidden">
            <ToggleRow
              label={he.settings.effortOptOut}
              checked={Boolean(prefs.effort_contribution_opt_out ?? false)}
              onChange={(v) => updatePref("effort_contribution_opt_out", v)}
              ariaLabel={he.settings.effortOptOut}
            />
          </div>
          <div className="-mx-4 px-4 -mt-3">
            <label htmlFor="min-study" className="text-sm font-medium text-slate-700 mb-2 block">
              {he.settings.minStudySession}: {prefs.min_study_session_minutes ?? 30} דקות
            </label>
            <input
              id="min-study"
              type="range"
              min={15}
              max={120}
              step={15}
              defaultValue={Number(prefs.min_study_session_minutes ?? 30)}
              onChange={(e) => updatePref("min_study_session_minutes", Number(e.target.value))}
              className="w-full accent-gio-500"
              aria-label={he.settings.minStudySession}
            />
          </div>
        </SettingsSection>

        {/* ─── Manual Updates ──────────────────────────────────────────────────── */}
        {manualUpdates.length > 0 && (
          <SettingsSection title={he.settings.sections.manualUpdates}>
            <div className="flex flex-col gap-2 max-h-48 overflow-y-auto -mx-4 -mt-4 -mb-4 px-4 py-3">
              {(manualUpdates as Array<{
                id: string;
                target_type: string;
                field_changed: string;
                old_value: string;
                new_value: string;
                changed_at: string;
              }>).map((log) => (
                <div key={log.id} className="text-xs text-slate-500 border-b border-navy-50 pb-2">
                  <span className="font-medium">{log.target_type}</span> · {log.field_changed}: {log.old_value} → {log.new_value}
                  <span className="block text-slate-400">{new Date(log.changed_at).toLocaleDateString("he-IL")}</span>
                </div>
              ))}
            </div>
          </SettingsSection>
        )}
      </div>
    </div>
  );
}

function ToggleRow({
  label,
  checked,
  onChange,
  ariaLabel,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  ariaLabel: string;
}) {
  return (
    <div className="flex items-center justify-between px-4 py-3">
      <span className="text-sm text-slate-700">{label}</span>
      <button
        role="switch"
        aria-checked={checked}
        aria-label={ariaLabel}
        onClick={() => onChange(!checked)}
        className={`relative w-11 h-6 rounded-full transition-colors ${
          checked ? "bg-gio-500" : "bg-navy-200"
        }`}
      >
        <span
          className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
            checked ? "translate-x-0.5" : "translate-x-5"
          }`}
        />
      </button>
    </div>
  );
}
