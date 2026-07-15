import { useState } from "react";
import ChatView from "./components/ChatView.jsx";
import AdminLogin from "./components/AdminLogin.jsx";
import AdminDashboard from "./components/AdminDashboard.jsx";
import PatientAuth from "./components/PatientAuth.jsx";
import PatientDashboard from "./components/PatientDashboard.jsx";

const ADMIN_TOKEN_KEY = "medirdv_admin_token";
const PATIENT_TOKEN_KEY = "medirdv_patient_token";

function App() {
  const [view, setView] = useState("chat");
  const [adminToken, setAdminToken] = useState(
    () => localStorage.getItem(ADMIN_TOKEN_KEY) || null
  );
  const [patientToken, setPatientToken] = useState(
    () => localStorage.getItem(PATIENT_TOKEN_KEY) || null
  );

  function handleGoToAdmin() {
    setView(adminToken ? "adminDashboard" : "adminLogin");
  }

  function handleGoToPatientAccount() {
    setView(patientToken ? "patientDashboard" : "patientAuth");
  }

  function handleAdminLoginSuccess(token) {
    localStorage.setItem(ADMIN_TOKEN_KEY, token);
    setAdminToken(token);
    setView("adminDashboard");
  }

  function handleAdminLogout() {
    localStorage.removeItem(ADMIN_TOKEN_KEY);
    setAdminToken(null);
    setView("chat");
  }

  function handlePatientLoginSuccess(token) {
    localStorage.setItem(PATIENT_TOKEN_KEY, token);
    setPatientToken(token);
    setView("patientDashboard");
  }

  function handlePatientLogout() {
    localStorage.removeItem(PATIENT_TOKEN_KEY);
    setPatientToken(null);
    setView("chat");
  }

  if (view === "adminLogin") {
    return (
      <AdminLogin onLoginSuccess={handleAdminLoginSuccess} onBackToChat={() => setView("chat")} />
    );
  }

  if (view === "adminDashboard" && adminToken) {
    return <AdminDashboard token={adminToken} onLogout={handleAdminLogout} />;
  }

  if (view === "patientAuth") {
    return (
      <PatientAuth
        onLoginSuccess={handlePatientLoginSuccess}
        onBackToChat={() => setView("chat")}
      />
    );
  }

  if (view === "patientDashboard" && patientToken) {
    return (
      <PatientDashboard
        token={patientToken}
        onLogout={handlePatientLogout}
        onBackToChat={() => setView("chat")}
      />
    );
  }

  return <ChatView onGoToAdmin={handleGoToAdmin} onGoToPatientAccount={handleGoToPatientAccount} />;
}

export default App;