import { useState } from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutGrid, Phone, Users, Headphones, Mic, FileText, UserCog, Building2,
  Network, BarChart3, Plug, GraduationCap, Menu, ChevronDown,
} from "lucide-react";
import SalemetriqLogo from "../SalemetriqLogo";
import TelemetryPulse from "../TelemetryPulse";
import { isSuperadmin, isAdmin } from "../../utils/auth";

/* Grupos lógicos del dashboard del workspace. */
const GRUPOS = [
  {
    label: "Vista general",
    items: [
      { to: "/overview", label: "Overview", icon: LayoutGrid },
      { to: "/reportes", label: "Reportes", icon: BarChart3 },
    ],
  },
  {
    label: "Equipo",
    items: [
      { to: "/closers", label: "Closers", icon: Users },
      { to: "/setters", label: "Setters", icon: Headphones },
      { to: "/equipo", label: "Equipo", icon: Network },
      { to: "/coaching", label: "Coaching", icon: GraduationCap },
    ],
  },
  {
    label: "Llamadas",
    items: [
      { to: "/calls", label: "Calls", icon: Phone },
      { to: "/call-analysis", label: "Call Analysis", icon: Mic },
      { to: "/script-generator", label: "Script Generator", icon: FileText },
    ],
  },
  {
    label: "Configuración",
    items: [
      { to: "/conexiones", label: "Conexiones", icon: Plug },
    ],
  },
];

const LS_COLLAPSED = "smq_sidebar_collapsed";
const LS_GRUPOS = "smq_sidebar_groups";

function leer(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

const linkClass = (collapsed) => ({ isActive }) =>
  `relative flex items-center gap-3 rounded-lg text-[14px] font-medium transition-colors ${
    collapsed ? "justify-center px-0 py-2.5" : "px-3 py-2.5"
  } ${isActive ? "text-txt bg-iris-500/[0.10]" : "text-txt-soft hover:text-txt hover:bg-ink-hover"}`;

function Item({ to, label, icon: Icon, collapsed }) {
  return (
    <NavLink to={to} title={collapsed ? label : undefined} className={linkClass(collapsed)}>
      {({ isActive }) => (
        <>
          {isActive && (
            <span className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-[3px] rounded-full bg-accent-grad shadow-glow" />
          )}
          <Icon size={18} strokeWidth={1.9} className="shrink-0" />
          {!collapsed && label}
        </>
      )}
    </NavLink>
  );
}

export default function Sidebar() {
  const superadmin = isSuperadmin();
  const [collapsed, setCollapsed] = useState(() => leer(LS_COLLAPSED, false));
  const [abiertos, setAbiertos] = useState(() => leer(LS_GRUPOS, {})); // { [label]: false } = cerrado

  // Grupos según rol.
  const grupos = superadmin
    ? [{ label: "Plataforma", items: [{ to: "/clientes", label: "Clientes", icon: Building2 }] }]
    : GRUPOS.map((g) =>
        g.label === "Configuración" && isAdmin()
          ? { ...g, items: [...g.items, { to: "/usuarios", label: "Usuarios", icon: UserCog }] }
          : g
      );

  function toggleCollapse() {
    setCollapsed((c) => {
      const next = !c;
      try { localStorage.setItem(LS_COLLAPSED, JSON.stringify(next)); } catch {}
      return next;
    });
  }

  function toggleGrupo(label) {
    setAbiertos((prev) => {
      const next = { ...prev, [label]: prev[label] === false ? true : false };
      try { localStorage.setItem(LS_GRUPOS, JSON.stringify(next)); } catch {}
      return next;
    });
  }

  return (
    <aside
      className={`shrink-0 glass-panel border-r border-white/[0.06] flex flex-col transition-[width] duration-200 ${
        collapsed ? "w-[76px]" : "w-[248px]"
      }`}
    >
      {/* Header: logo + hamburguesa */}
      <div className={`h-[68px] flex items-center border-b border-ink-line ${collapsed ? "justify-center px-0" : "justify-between px-4"}`}>
        {!collapsed && <SalemetriqLogo size={26} withWord />}
        <button
          onClick={toggleCollapse}
          title={collapsed ? "Expandir menú" : "Contraer menú"}
          className="icon-btn shrink-0"
        >
          <Menu size={20} />
        </button>
      </div>

      {/* Navegación */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 flex flex-col gap-1">
        {grupos.map((g) => {
          const open = abiertos[g.label] !== false; // por defecto abierto
          if (collapsed) {
            // Modo riel: solo íconos, sin encabezados de grupo.
            return (
              <div key={g.label} className="flex flex-col gap-0.5 pb-2 mb-1 border-b border-white/[0.05] last:border-0">
                {g.items.map((it) => <Item key={it.to} {...it} collapsed />)}
              </div>
            );
          }
          return (
            <div key={g.label} className="flex flex-col">
              <button
                onClick={() => toggleGrupo(g.label)}
                className="flex items-center justify-between px-3 py-1.5 group"
              >
                <span className="label group-hover:text-txt-soft transition-colors">{g.label}</span>
                <ChevronDown
                  size={14}
                  className={`text-txt-mute transition-transform duration-200 ${open ? "" : "-rotate-90"}`}
                />
              </button>
              {open && (
                <div className="flex flex-col gap-0.5 pb-1">
                  {g.items.map((it) => <Item key={it.to} {...it} collapsed={false} />)}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      {/* Firma — telemetría en vivo */}
      {!collapsed && (
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
      )}
    </aside>
  );
}
