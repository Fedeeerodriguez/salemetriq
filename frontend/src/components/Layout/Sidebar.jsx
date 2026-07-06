import { NavLink, useNavigate } from "react-router-dom";
import { LayoutDashboard, PhoneCall, Headphones, LogOut } from "lucide-react";
import SalemetriqLogo from "../SalemetriqLogo";
import { getUser, logout } from "../../utils/auth";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/closers", label: "Closers", icon: PhoneCall },
  { to: "/setters", label: "Setters", icon: Headphones },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const user = getUser();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <aside className="w-60 shrink-0 bg-surface-card border-r border-surface-border flex flex-col">
      <div className="px-5 py-5 border-b border-surface-border">
        <SalemetriqLogo size={30} withWord />
      </div>

      <nav className="flex-1 px-3 py-4 flex flex-col gap-1">
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-pulse-400/10 text-pulse-300"
                  : "text-[#8B949E] hover:text-white hover:bg-surface-hover"
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-3 py-4 border-t border-surface-border">
        <div className="px-3 pb-3">
          <div className="text-sm text-white truncate">{user?.nombre || user?.email}</div>
          <div className="text-xs text-[#6C7B84] uppercase tracking-wider">{user?.rol}</div>
        </div>
        <button onClick={handleLogout} className="btn-ghost w-full flex items-center gap-3">
          <LogOut size={18} />
          Salir
        </button>
      </div>
    </aside>
  );
}
