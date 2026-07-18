import { useState } from "react";

const CLINIC_NAME_LOGIN = import.meta.env.VITE_CLINIC_NAME || "MediRDV";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function AdminLogin({ onLoginSuccess, onBackToChat }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [logoFailed, setLogoFailed] = useState(false);

  async function handleSubmit(e) {
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

      if (!response.ok) {
        throw new Error(data.detail || "Connexion impossible.");
      }

      if (!data.patient.is_admin) {
        setError("Ce compte n'a pas les droits administrateur.");
        return;
      }

      onLoginSuccess(data.access_token);
    } catch (err) {
      setError(err.message || "Erreur de connexion.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="admin-login-page">
      <form className="admin-login-card" onSubmit={handleSubmit}>
        {!logoFailed && (
          <img
            src="/logo-akdital.png"
            alt={CLINIC_NAME_LOGIN}
            className="brand-logo-card"
            onError={() => setLogoFailed(true)}
          />
        )}
        <h1>Espace admin</h1>
        <p className="admin-login-subtitle">{CLINIC_NAME_LOGIN} - Tableau de bord</p>

        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
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

        <button type="submit" disabled={isLoading}>
          {isLoading ? "Connexion..." : "Se connecter"}
        </button>

        <button type="button" className="link-button" onClick={onBackToChat}>
          Retour au chat
        </button>
      </form>
    </div>
  );
}

export default AdminLogin;