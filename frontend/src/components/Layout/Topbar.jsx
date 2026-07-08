import { useLocation, useNavigate } from "react-router-dom";
import { Search, Bell, LogOut } from "lucide-react";
import { getUser, logout, getWorkspace, isSuperadmin } from "../../utils/auth";

const TITLES = {
  "/overview": "Overview",
  "/calls": "Calls",
  "/closers": "Closers",
  "/setters": "Setters",
  "/equipo": "Equipo",
  "/reportes": "Reportes",
  "/coaching": "Coaching",
  "/conexiones": "Conexiones",
  "/perfil": "Mi perfil",
  "/call-analysis": "Call Analysis",
  "/script-generator": "Script Generator",
  "/usuarios": "Usuarios",
  "/clientes": "Clientes",
};

function titleFor(pathname) {
  if (pathname.startsWith("/users/")) return "Perfil";
  return TITLES[pathname] || "SALEMETRIQ";
}

export default function Topbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const user = getUser();
  const title = titleFor(location.pathname);

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <header className="h-[68px] shrink-0 glass-panel border-b border-white/[0.06] flex items-center justify-between px-8">
      <div className="flex items-center gap-3">
        <h1 className="font-display text-[22px] font-semibold text-txt tracking-tight">{title}</h1>
        <span
          className="pill text-iris-300 bg-iris-500/12 flex items-center gap-1.5"
          style={user?.brand_color ? { color: user.brand_color, background: `${user.brand_color}1f` } : undefined}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-accent-grad" style={user?.brand_color ? { background: user.brand_color } : undefined} />
          {isSuperadmin() ? "Plataforma" : (getWorkspace() || "Workspace")}
        </span>
      </div>

      <div className="flex items-center gap-3">
        <button className="icon-btn" title="Buscar"><Search size={18} /></button>
        <button className="icon-btn" title="Notificaciones"><Bell size={18} /></button>

        <div className="flex items-center gap-2 pl-2 ml-1 border-l border-ink-line">
          <button
            onClick={() => navigate("/perfil")}
            title="Mi perfil"
            className="w-8 h-8 rounded-full bg-iris-500/20 text-iris-400 grid place-items-center text-[13px] font-semibold ring-1 ring-iris-500/30 hover:ring-iris-400/60 hover:text-iris-300 transition-colors"
          >
            {(user?.nombre || user?.email || "U").slice(0, 1).toUpperCase()}
          </button>
          <button onClick={handleLogout} className="icon-btn" title="Salir"><LogOut size={17} /></button>
        </div>
      </div>
    </header>
  );
}
