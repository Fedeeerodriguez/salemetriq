import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Search, Bell, LogOut } from "lucide-react";
import { getUser, logout } from "../../utils/auth";

const TITLES = {
  "/overview": "Overview",
  "/calls": "Calls",
  "/closers": "Closers",
  "/call-analysis": "Call Analysis",
  "/script-generator": "Script Generator",
};

export default function Topbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const [vista, setVista] = useState("owner");
  const user = getUser();
  const title = TITLES[location.pathname] || "SALEMETRIQ";

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <header className="h-[68px] shrink-0 border-b border-ink-line flex items-center justify-between px-8">
      <h1 className="text-[22px] font-semibold text-txt tracking-tight">{title}</h1>

      <div className="flex items-center gap-3">
        {/* Toggle Vista Owner / Closer */}
        <div className="flex items-center bg-ink-card border border-ink-line rounded-full p-1">
          {["owner", "closer"].map((v) => (
            <button
              key={v}
              onClick={() => setVista(v)}
              className={`px-3.5 py-1.5 rounded-full text-[13px] font-medium transition-colors ${
                vista === v ? "bg-gold-500 text-ink" : "text-txt-soft hover:text-txt"
              }`}
            >
              Vista {v === "owner" ? "Owner" : "Closer"}
            </button>
          ))}
        </div>

        <button className="icon-btn" title="Buscar"><Search size={18} /></button>
        <button className="icon-btn" title="Notificaciones"><Bell size={18} /></button>

        <div className="flex items-center gap-2 pl-2 ml-1 border-l border-ink-line">
          <div className="w-8 h-8 rounded-full bg-gold-500/15 text-gold-400 grid place-items-center text-[13px] font-semibold">
            {(user?.nombre || user?.email || "U").slice(0, 1).toUpperCase()}
          </div>
          <button onClick={handleLogout} className="icon-btn" title="Salir"><LogOut size={17} /></button>
        </div>
      </div>
    </header>
  );
}
