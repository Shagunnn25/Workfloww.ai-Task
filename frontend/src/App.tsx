import { AuthProvider, useAuth } from "./context/AuthContext";
import { EmployeeView } from "./components/EmployeeView";
import { LoginView } from "./components/LoginView";
import { ManagerView } from "./components/ManagerView";

function AppContent() {
  const { session, logout } = useAuth();

  if (!session) {
    return <LoginView />;
  }

  return (
    <div className="app">
      <header className="app-header">
        <span>
          {session.fullName} &middot; {session.role}
        </span>
        <button onClick={logout}>Log out</button>
      </header>
      {session.role === "manager" ? <ManagerView /> : <EmployeeView />}
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
