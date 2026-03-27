import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import { useAuth } from "../hooks/useAuth";
import { he } from "../i18n/he";

type AuthView = "login" | "register" | "verify";

export function AuthScreen() {
  const [view, setView] = useState<AuthView>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [googleEnabled, setGoogleEnabled] = useState(false);
  const { login, register, verify, isLoading, error, pendingEmail } = useAuth();

  useEffect(() => {
    apiClient
      .get<{ google_enabled: boolean }>("/auth/config")
      .then(({ data }) => setGoogleEnabled(data.google_enabled))
      .catch(() => setGoogleEnabled(false));
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    await login(email, password);
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = await register(email, name);
    // In dev: show code; in prod: switch to verify view
    if (result?.dev_code) {
      setCode(result.dev_code);
    }
    setView("verify");
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    await verify(pendingEmail ?? email, code, password);
  };

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-4"
      dir="rtl"
      lang="he"
    >
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gio-600">Juggle</h1>
          <p className="text-gray-500 mt-1 text-sm">{he.auth.subtitle}</p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          {view === "verify" ? (
            <form onSubmit={handleVerify} className="flex flex-col gap-4">
              <div className="text-center">
                <h2 className="text-lg font-semibold">{he.auth.verifyTitle}</h2>
                <p className="text-sm text-gray-500 mt-1">{he.auth.verifySubtitle}</p>
              </div>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder={he.auth.codePlaceholder}
                maxLength={6}
                required
                className="w-full border border-gray-300 rounded-xl px-4 py-3 text-center text-xl tracking-widest focus:outline-none focus:border-gio-500"
                aria-label="קוד אימות"
                inputMode="numeric"
              />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={he.auth.newPasswordLabel}
                required
                minLength={8}
                className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:border-gio-500"
                aria-label={he.auth.newPasswordLabel}
              />
              {error && <p className="text-red-500 text-sm text-center">{error}</p>}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-gio-500 text-white rounded-xl py-3 font-medium hover:bg-gio-600 disabled:opacity-50 transition-colors min-h-[44px]"
                aria-label={he.auth.verifyButton}
              >
                {isLoading ? "..." : he.auth.verifyButton}
              </button>
            </form>
          ) : (
            <>
              {/* Tab switcher */}
              <div className="flex border-b border-gray-100 mb-5">
                {(["login", "register"] as const).map((v) => (
                  <button
                    key={v}
                    onClick={() => setView(v)}
                    className={`flex-1 py-2 text-sm font-medium border-b-2 transition-colors ${
                      view === v ? "border-gio-500 text-gio-600" : "border-transparent text-gray-400"
                    }`}
                    aria-selected={view === v}
                  >
                    {v === "login" ? he.auth.loginTab : he.auth.registerTab}
                  </button>
                ))}
              </div>

              <form
                onSubmit={view === "login" ? handleLogin : handleRegister}
                className="flex flex-col gap-4"
              >
                {view === "register" && (
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder={he.auth.nameLabel}
                    required
                    className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:border-gio-500"
                    aria-label={he.auth.nameLabel}
                  />
                )}
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={he.auth.emailLabel}
                  required
                  className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:border-gio-500"
                  aria-label={he.auth.emailLabel}
                />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={he.auth.passwordLabel}
                  required={view === "login"}
                  minLength={view === "login" ? undefined : 8}
                  className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:border-gio-500"
                  aria-label={he.auth.passwordLabel}
                />
                {error && <p className="text-red-500 text-sm text-center">{error}</p>}
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-gio-500 text-white rounded-xl py-3 font-medium hover:bg-gio-600 disabled:opacity-50 transition-colors min-h-[44px]"
                >
                  {isLoading ? "..." : view === "login" ? he.auth.loginButton : he.auth.registerButton}
                </button>
              </form>

              {/* Divider */}
              <div className="flex items-center gap-3 my-4">
                <div className="flex-1 h-px bg-gray-200" />
                <span className="text-xs text-gray-400">או</span>
                <div className="flex-1 h-px bg-gray-200" />
              </div>

              {/* Google OAuth — only shown when credentials are configured */}
              {googleEnabled ? (
                <button
                  onClick={() => (window.location.href = "/auth/google")}
                  className="w-full flex items-center justify-center gap-2 border border-gray-300 rounded-xl py-3 text-sm font-medium
                             hover:bg-gray-50 transition-colors min-h-[44px]"
                  aria-label={he.auth.googleButton}
                >
                  <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
                    <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
                    <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
                    <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
                    <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
                  </svg>
                  {he.auth.googleButton}
                </button>
              ) : (
                <p className="text-center text-xs text-gray-400">
                  כניסה עם Google דורשת הגדרת{" "}
                  <code className="bg-gray-100 px-1 rounded">GOOGLE_CLIENT_ID</code>{" "}
                  ב-<code className="bg-gray-100 px-1 rounded">.env</code>
                </p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
