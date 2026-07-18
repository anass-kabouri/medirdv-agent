import { useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const CLINIC_NAME_PATIENT = import.meta.env.VITE_CLINIC_NAME || "MediRDV";

function PatientAuth({ onLoginSuccess, onBackToChat }) {
  const [mode, setMode] = useState("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState(null);
  const [info, setInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [logoFailed, setLogoFailed] = useState(false);

  async function handleLogin(e) {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Connexion impossible.");
      onLoginSuccess(data.access_token);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleRegister(e) {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Inscription impossible.");
      setInfo("Un code de verification a ete envoye a votre adresse email.");
      setMode("verify");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleVerify(e) {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/auth/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, code }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Code invalide.");
      setInfo("Email verifie ! Vous pouvez maintenant vous connecter.");
      setMode("login");
      setCode("");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleResendCode() {
    setError(null);
    setInfo(null);
    try {
      const response = await fetch(`${API_URL}/auth/resend-code`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Impossible de renvoyer le code.");
      setInfo("Nouveau code envoye.");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="admin-login-page">
      <div className="admin-login-card">
        {!logoFailed && (
          <img
            src="/logo-akdital.png"
            alt={CLINIC_NAME_PATIENT}
            className="brand-logo-card"
            onError={() => setLogoFailed(true)}
          />
        )}
        <h1>{mode === "verify" ? "Verification" : "Mon compte"}</h1>
        <p className="admin-login-subtitle">{CLINIC_NAME_PATIENT} - Espace patient</p>

        {mode !== "verify" && (
          <div className="auth-tabs">
            <button
              type="button"
              className={mode === "login" ? "auth-tab active" : "auth-tab"}
              onClick={() => {
                setMode("login");
                setError(null);
                setInfo(null);
              }}
            >
              Se connecter
            </button>
            <button
              type="button"
              className={mode === "register" ? "auth-tab active" : "auth-tab"}
              onClick={() => {
                setMode("register");
                setError(null);
                setInfo(null);
              }}
            >
              S'inscrire
            </button>
          </div>
        )}

        {mode === "login" && (
          <form onSubmit={handleLogin}>
            <label>
              Email
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </label>
            <label>
              Mot de passe
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </label>
            {error && <div className="error-banner">{error}</div>}
            {info && <div className="info-banner">{info}</div>}
            <button type="submit" disabled={isLoading}>
              {isLoading ? "Connexion..." : "Se connecter"}
            </button>
          </form>
        )}

        {mode === "register" && (
          <form onSubmit={handleRegister}>
            <label>
              Nom complet
              <input type="text" value={name} onChange={(e) => setName(e.target.value)} required />
            </label>
            <label>
              Email
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </label>
            <label>
              Mot de passe
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
              />
            </label>
            {error && <div className="error-banner">{error}</div>}
            <button type="submit" disabled={isLoading}>
              {isLoading ? "Inscription..." : "S'inscrire"}
            </button>
          </form>
        )}

        {mode === "verify" && (
          <form onSubmit={handleVerify}>
            <p className="verify-instructions">
              Entrez le code a 6 chiffres envoye a <strong>{email}</strong>
            </p>
            <label>
              Code de verification
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                maxLength={6}
                required
              />
            </label>
            {error && <div className="error-banner">{error}</div>}
            {info && <div className="info-banner">{info}</div>}
            <button type="submit" disabled={isLoading}>
              {isLoading ? "Verification..." : "Verifier"}
            </button>
            <button type="button" className="link-button" onClick={handleResendCode}>
              Renvoyer le code
            </button>
          </form>
        )}

        <button type="button" className="link-button" onClick={onBackToChat}>
          Retour au chat
        </button>
      </div>
    </div>
  );
}

export default PatientAuth;