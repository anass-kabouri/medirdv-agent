import { useState } from "react";
import ChatView from "./components/ChatView.jsx";
import AdminLogin from "./components/AdminLogin.jsx";
import AdminDashboard from "./components/AdminDashboard.jsx";

const ADMIN_TOKEN_KEY = "medirdv_admin_token";

function App() {
  const [view, setView] = useState("chat");
  const [adminToken, setAdminToken] = useState(
    () => localStorage.getItem(ADMIN_TOKEN_KEY) || null
  );

  function handleGoToAdmin() {
    if (adminToken) {
      setView("adminDashboard");
    } else {
      setView("adminLogin");
    }
  }

  function handleLoginSuccess(token) {
    localStorage.setItem(ADMIN_TOKEN_KEY, token);
    setAdminToken(token);
    setView("adminDashboard");
  }

  function handleLogout() {
    localStorage.removeItem(ADMIN_TOKEN_KEY);
    setAdminToken(null);
    setView("chat");
  }

  if (view === "adminLogin") {
    return (
      <AdminLogin
        onLoginSuccess={handleLoginSuccess}
        onBackToChat={() => setView("chat")}
      />
    );
  }

  if (view === "adminDashboard" && adminToken) {
    return <AdminDashboard token={adminToken} onLogout={handleLogout} />;
  }

  return <ChatView onGoToAdmin={handleGoToAdmin} />;
}

export default App;
