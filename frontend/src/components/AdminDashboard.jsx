import { useEffect, useState } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler);

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function friendlyErrorMessage(err) {
  if (err instanceof TypeError) {
    return "Connexion au serveur impossible. Veuillez reessayer.";
  }
  return err.message || "Une erreur est survenue.";
}

function AdminDashboard({ token, onLogout }) {
  const [stats, setStats] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      setError(null);

      try {
        const headers = { Authorization: `Bearer ${token}` };

        const [statsRes, appointmentsRes] = await Promise.all([
          fetch(`${API_URL}/admin/stats`, { headers }),
          fetch(`${API_URL}/admin/appointments`, { headers }),
        ]);

        if (statsRes.status === 401 || appointmentsRes.status === 401) {
          onLogout();
          return;
        }

        if (!statsRes.ok || !appointmentsRes.ok) {
          throw new Error("Impossible de charger les donnees du dashboard.");
        }

        setStats(await statsRes.json());
        setAppointments(await appointmentsRes.json());
      } catch (err) {
        setError(friendlyErrorMessage(err));
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, [token, onLogout]);

  async function handleExport(format) {
    try {
      const response = await fetch(`${API_URL}/admin/export/${format}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) {
        throw new Error("Echec de l'export.");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `rendezvous_medirdv.${format}`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(friendlyErrorMessage(err));
      console.error(err);
    }
  }

  if (isLoading) {
    return <div className="admin-dashboard-loading">Chargement du dashboard...</div>;
  }

  const chartData = stats && {
    labels: stats.appointments_last_7_days.map((d) => d.date.slice(5)),
    datasets: [
      {
        label: "Rendez-vous",
        data: stats.appointments_last_7_days.map((d) => d.count),
        borderColor: "#0f75c2",
        backgroundColor: "rgba(15, 117, 194, 0.12)",
        pointBackgroundColor: "#0f75c2",
        pointBorderColor: "#ffffff",
        pointBorderWidth: 1.5,
        pointRadius: 4,
        pointHoverRadius: 6,
        borderWidth: 2,
        tension: 0.35,
        fill: true,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "#06467d",
        padding: 10,
        titleFont: { family: "IBM Plex Mono", size: 11 },
        bodyFont: { family: "Inter", size: 12 },
        callbacks: {
          label: (ctx) => `${ctx.parsed.y} rendez-vous`,
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { font: { family: "IBM Plex Mono", size: 10.5 }, color: "#4a6178" },
      },
      y: {
        beginAtZero: true,
        ticks: { precision: 0, font: { family: "Inter", size: 11 }, color: "#4a6178" },
        grid: { color: "#eaf3fb" },
      },
    },
  };

  return (
    <div className="admin-dashboard">
      <header className="admin-dashboard-header">
        <h1>Dashboard MediRDV</h1>
        <button className="link-button" onClick={onLogout}>
          Deconnexion
        </button>
      </header>
      <div className="scallop-divider" />

      {error && <div className="error-banner">{error}</div>}

      {stats && (
        <>
          <section className="stat-cards">
            <div className="stat-card">
              <span className="stat-value">{stats.total_appointments}</span>
              <span className="stat-label">Rendez-vous total</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{stats.confirmed_appointments}</span>
              <span className="stat-label">Confirmes</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{stats.cancelled_appointments}</span>
              <span className="stat-label">Annules</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">
                {Math.round(stats.cancellation_rate * 100)}%
              </span>
              <span className="stat-label">Taux d'annulation</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{stats.total_practitioners}</span>
              <span className="stat-label">Praticiens</span>
            </div>
          </section>

          <section className="chart-section">
            <h2>Rendez-vous des 7 derniers jours</h2>
            {stats.appointments_last_7_days.length === 0 ? (
              <p className="empty-state">Aucune donnee sur cette periode.</p>
            ) : (
              <div style={{ height: "220px" }}>
                <Line data={chartData} options={chartOptions} />
              </div>
            )}
          </section>
        </>
      )}

      <section className="appointments-table-section">
        <div className="table-section-header">
          <h2>Tous les rendez-vous</h2>
          <div className="export-buttons">
            <button className="export-button" onClick={() => handleExport("csv")}>
              Exporter CSV
            </button>
            <button className="export-button" onClick={() => handleExport("pdf")}>
              Exporter PDF
            </button>
          </div>
        </div>
        {appointments.length === 0 ? (
          <p className="empty-state">Aucun rendez-vous enregistre.</p>
        ) : (
          <table className="appointments-table">
            <thead>
              <tr>
                <th>Patient</th>
                <th>Praticien</th>
                <th>Specialite</th>
                <th>Date</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              {appointments.map((a) => (
                <tr key={a.id}>
                  <td>{a.patient_name}</td>
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

export default AdminDashboard;