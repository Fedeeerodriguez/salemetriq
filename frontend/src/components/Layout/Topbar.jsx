import { useLocation, useNavigate } from "react-router-dom";
import { LogOut } from "lucide-react";
import { getUser, logout } from "../../utils/auth";

const TITLES = {
  "/buscar": "Buscar",
  "/perfiles": "Perfiles",
  "/nichos": "Nichos",
  "/listas": "Listas",
  "/perfil": "Mi perfil",
};

function titleFor(pathname) {
  if (pathname.startsWith("/listas/")) return "Lista";
  return TITLES[pathname] || "IG Prospector";
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
    <header className="h-[68px] shrink-0 glass-panel border-b border-white/[0.06] flex items-center justify-between px-6 sm:px-8">
      <div className="flex items-center gap-3">
        <h1 className="font-display text-[20px] sm:text-[22px] font-semibold text-txt tracking-tight">{title}</h1>
        <span className="pill text-iris-300 bg-iris-500/12 hidden sm:inline">solo lectura · no envía DMs</span>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate("/perfil")}
          title="Mi perfil"
          className="w-8 h-8 rounded-full bg-iris-500/20 text-iris-400 grid place-items-center text-[13px] font-semibold ring-1 ring-iris-500/30 hover:ring-iris-400/60 hover:text-iris-300 transition-colors"
        >
          {(user?.nombre || user?.email || "U").slice(0, 1).toUpperCase()}
        </button>
        <button onClick={handleLogout} className="icon-btn" title="Salir"><LogOut size={17} /></button>
      </div>
    </header>
  );
}
