import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import GlassFilters from "./components/GlassFilters";
import Layout from "./components/Layout/Layout";
import Login from "./pages/Login";
import InviteAccept from "./pages/InviteAccept";
import Overview from "./pages/Overview";
import Reportes from "./pages/Reportes";
import Conexiones from "./pages/Conexiones";
import Coaching from "./pages/Coaching";
import Calls from "./pages/Calls";
import Closers from "./pages/Closers";
import Setters from "./pages/Setters";
import UserProfile from "./pages/UserProfile";
import CallAnalysis from "./pages/CallAnalysis";
import ScriptGenerator from "./pages/ScriptGenerator";
import Usuarios from "./pages/Usuarios";
import Clientes from "./pages/Clientes";
import Equipo from "./pages/Equipo";
import { isAuthenticated, isSuperadmin, isAdmin } from "./utils/auth";

function RequireAuth({ children }) {
  return isAuthenticated() ? children : <Navigate to="/login" replace />;
}

// Home según rol: superadmin → clientes; resto → overview.
function HomeRedirect() {
  return <Navigate to={isSuperadmin() ? "/clientes" : "/overview"} replace />;
}
function RequireSuperadmin({ children }) {
  return isSuperadmin() ? children : <Navigate to="/" replace />;
}
function RequireAdmin({ children }) {
  return isAdmin() ? children : <Navigate to="/" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <GlassFilters />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/invite/:token" element={<InviteAccept />} />
        <Route path="/" element={<RequireAuth><Layout /></RequireAuth>}>
          <Route index element={<HomeRedirect />} />
          <Route path="clientes" element={<RequireSuperadmin><Clientes /></RequireSuperadmin>} />
          <Route path="usuarios" element={<RequireAdmin><Usuarios /></RequireAdmin>} />
          <Route path="overview" element={<Overview />} />
          <Route path="calls" element={<Calls />} />
          <Route path="closers" element={<Closers />} />
          <Route path="setters" element={<Setters />} />
          <Route path="equipo" element={<Equipo />} />
          <Route path="reportes" element={<Reportes />} />
          <Route path="coaching" element={<Coaching />} />
          <Route path="conexiones" element={<Conexiones />} />
          <Route path="users/:id" element={<UserProfile />} />
          <Route path="call-analysis" element={<CallAnalysis />} />
          <Route path="script-generator" element={<ScriptGenerator />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
