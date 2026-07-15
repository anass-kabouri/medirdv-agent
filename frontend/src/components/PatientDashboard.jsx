import { useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function PatientDashboard({ token, onLogout, onBackToChat }) {
  const [appointments, setAppointments] = useState([]);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadAppointments() {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_URL}/appointments/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (response.status === 401) {
          onLogout();
          return;
        }

        if (!response.ok) throw new Error("Impossible de charger vos rendez-vous.");
        setAppointments(await response.json());
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    }

    loadAppointments();
  }, [token, onLogout]);

  return (
    <div className="admin-dashboard">
      <header className="admin-dashboard-header">
        <h1>Mes rendez-vous</h1>
        <div className="export-buttons">
          <button className="link-button" onClick={onBackToChat}>
            Retour au chat
          </button>
          <button className="link-button" onClick={onLogout}>
            Deconnexion
          </button>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <section className="appointments-table-section">
        {isLoading ? (
          <p className="empty-state">Chargement...</p>
        ) : appointments.length === 0 ? (
          <p className="empty-state">Vous n'avez aucun rendez-vous enregistre.</p>
        ) : (
          <table className="appointments-table">
            <thead>
              <tr>
                <th>Praticien</th>
                <th>Specialite</th>
                <th>Date</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              {appointments.map((a) => (
                <tr key={a.id}>
                  <td>{a.practitioner_name}</td>
                  <td>{a.specialty}</td>
                  <td>{new Date(a.start_time).toLocaleString("fr-FR")}</td>
                  <td>
                    <span className={`status-badge status-${a.status}`}>{a.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

export default PatientDashboard;