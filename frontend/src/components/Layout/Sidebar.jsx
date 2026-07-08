import { NavLink } from "react-router-dom";
import { LayoutGrid, Phone, Users, Headphones, Mic, FileText, UserCog, Building2, Network, BarChart3, Plug, GraduationCap } from "lucide-react";
import SalemetriqLogo from "../SalemetriqLogo";
import TelemetryPulse from "../TelemetryPulse";
import { isSuperadmin, isAdmin } from "../../utils/auth";

const DASHBOARD = [
  { to: "/overview", label: "Overview", icon: LayoutGrid },
  { to: "/calls", label: "Calls", icon: Phone },
  { to: "/closers", label: "Closers", icon: Users },
  { to: "/setters", label: "Setters", icon: Headphones },
  { to: "/equipo", label: "Equipo", icon: Network },
  { to: "/reportes", label: "Reportes", icon: BarChart3 },
  { to: "/conexiones", label: "Conexiones", icon: Plug },
  { to: "/coaching", label: "Coaching", icon: GraduationCap },
  { to: "/call-analysis", label: "Call Analysis", icon: Mic },
  { to: "/script-generator", label: "Script Generator", icon: FileText },
];

export default function Sidebar() {
  // Superadmin (plataforma) solo ve "Clientes"; el resto ve el dashboard del workspace.
  const superadmin = isSuperadmin();
  const NAV = superadmin
    ? [{ to: "/clientes", label: "Clientes", icon: Building2 }]
    : isAdmin()
      ? [...DASHBOARD, { to: "/usuarios", label: "Usuarios", icon: UserCog }]
      : DASHBOARD;

  return (
    <aside className="w-[248px] shrink-0 glass-panel border-r border-white/[0.06] flex flex-col">
      <div className="px-6 h-[68px] flex items-center border-b border-ink-line">
        <SalemetriqLogo size={26} withWord />
      </div>

      <nav className="flex-1 px-3 py-5 flex flex-col gap-0.5">
        <div className="label px-3 pb-2">General</div>
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-[14px] font-medium transition-colors ${
                isActive
                  ? "text-txt bg-iris-500/[0.10]"
                  : "text-txt-soft hover:text-txt hover:bg-ink-hover"
              }`
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-[3px] rounded-full bg-accent-grad shadow-glow" />
                )}
                <Icon size={18} strokeWidth={1.9} />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Firma — telemetría en vivo */}
      <div className="px-5 py-4 border-t border-ink-line">
        <div className="flex items-center gap-2 mb-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-60 animate-ping" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-cyan-400" />
          </span>
          <span className="text-[10px] uppercase tracking-[0.18em] text-txt-mute font-medium">Señal en vivo</span>
        </div>
        <TelemetryPulse height={34} />
      </div>
    </aside>
  );
}
