import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import GlassFilters from "./components/GlassFilters";
import Layout from "./components/Layout/Layout";
import Login from "./pages/Login";
import Buscar from "./pages/Buscar";
import Perfiles from "./pages/Perfiles";
import Nichos from "./pages/Nichos";
import Listas from "./pages/Listas";
import ListaDetalle from "./pages/ListaDetalle";
import MiPerfil from "./pages/MiPerfil";
import { isAuthenticated } from "./utils/auth";

function RequireAuth({ children }) {
  return isAuthenticated() ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <GlassFilters />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<RequireAuth><Layout /></RequireAuth>}>
          <Route index element={<Navigate to="/buscar" replace />} />
          <Route path="buscar" element={<Buscar />} />
          <Route path="perfiles" element={<Perfiles />} />
          <Route path="nichos" element={<Nichos />} />
          <Route path="listas" element={<Listas />} />
          <Route path="listas/:id" element={<ListaDetalle />} />
          <Route path="perfil" element={<MiPerfil />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
