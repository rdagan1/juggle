import { useEffect, useState } from "react";
import { emailsApi, type EmailItem } from "../api/client";
import { he } from "../i18n/he";

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  parsed: "bg-green-100 text-green-700",
  unreadable: "bg-red-100 text-red-700",
  no_events: "bg-navy-100 text-slate-500",
  failed: "bg-red-100 text-red-700",
};

function EmailRow({ email }: { email: EmailItem }) {
  const receivedFmt = new Date(email.received_at).toLocaleDateString("he-IL", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });

  const statusLabel =
    he.emails.statuses[email.parse_status as keyof typeof he.emails.statuses] ??
    email.parse_status;
  const badgeColor = STATUS_COLORS[email.parse_status] ?? "bg-navy-100 text-slate-500";
  const hasAlert = email.parse_status === "unreadable" || email.parse_status === "failed";

  return (
    <div
      className={`bg-white rounded-xl border px-4 py-3 flex flex-col gap-1 ${
        hasAlert ? "border-red-200" : "border-navy-100"
      }`}
      dir="rtl"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-col gap-0.5 flex-1 min-w-0">
          <p className="font-medium text-sm text-gray-800 truncate">
            {email.subject ?? "(ללא נושא)"}
          </p>
          <p className="text-[10px] text-slate-400 truncate">{email.sender ?? ""}</p>
        </div>
        <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium shrink-0 ${badgeColor}`}>
          {statusLabel}
        </span>
      </div>

      <div className="flex items-center justify-between text-[10px] text-slate-400 mt-1">
        <span>{receivedFmt}</span>
        {email.attachment_count > 0 && (
          <span>
            {he.emails.attachments.replace("{count}", String(email.attachment_count))}
          </span>
        )}
      </div>

      {email.forwarded_at && (
        <p className="text-[10px] text-green-600">
          {he.emails.forwarded.replace(
            "{time}",
            new Date(email.forwarded_at).toLocaleTimeString("he-IL", {
              hour: "2-digit",
              minute: "2-digit",
            }),
          )}
        </p>
      )}
    </div>
  );
}

export function EmailsTab() {
  const [emails, setEmails] = useState<EmailItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = (pageNum: number) => {
    emailsApi
      .get(pageNum)
      .then(({ data }) => {
        const newEmails = data.emails;
        setEmails((prev) => (pageNum === 1 ? newEmails : [...prev, ...newEmails]));
        setHasMore(newEmails.length === 20);
      })
      .catch(() => setError(he.errors.generic))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    load(1);
  }, []);

  const loadMore = () => {
    const next = page + 1;
    setPage(next);
    load(next);
  };

  return (
    <div
      id="panel-emails"
      role="tabpanel"
      aria-label={he.tabs.emails}
      className="flex flex-col h-full bg-navy-50 overflow-y-auto"
      dir="rtl"
    >
      <header className="px-4 pt-5 pb-3">
        <h1 className="text-xl font-bold text-gray-800">{he.emails.title}</h1>
      </header>

      {isLoading && (
        <div className="flex-1 flex items-center justify-center text-slate-400">טוען...</div>
      )}

      {error && (
        <div className="mx-4 p-3 rounded-xl bg-red-50 text-red-600 text-sm">{error}</div>
      )}

      {!isLoading && !error && emails.length === 0 && (
        <div className="flex-1 flex items-center justify-center text-slate-400 text-sm">
          {he.emails.noEmails}
        </div>
      )}

      <div className="flex flex-col gap-2 px-4 pb-4">
        {emails.map((e) => (
          <EmailRow key={e.id} email={e} />
        ))}
      </div>

      {hasMore && !isLoading && (
        <button
          onClick={loadMore}
          className="self-center text-sm text-gio-500 hover:underline py-4 min-h-[44px]"
        >
          טען עוד
        </button>
      )}
    </div>
  );
}
