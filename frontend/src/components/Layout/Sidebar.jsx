import { useState } from "react";
import { NavLink } from "react-router-dom";
import { Search, Users, Target, ListChecks, Menu } from "lucide-react";
import IgpLogo from "../IgpLogo";

const ITEMS = [
  { to: "/buscar", label: "Buscar", icon: Search },
  { to: "/perfiles", label: "Perfiles", icon: Users },
  { to: "/nichos", label: "Nichos", icon: Target },
  { to: "/listas", label: "Listas", icon: ListChecks },
];

const LS_COLLAPSED = "igp_sidebar_collapsed";

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
  const [collapsed, setCollapsed] = useState(() => leer(LS_COLLAPSED, false));

  function toggleCollapse() {
    setCollapsed((c) => {
      const next = !c;
      try { localStorage.setItem(LS_COLLAPSED, JSON.stringify(next)); } catch {}
      return next;
    });
  }

  return (
    <aside
      className={`shrink-0 glass-panel border-r border-white/[0.06] flex flex-col transition-[width] duration-200 ${
        collapsed ? "w-[76px]" : "w-[240px]"
      }`}
    >
      <div className={`h-[68px] flex items-center border-b border-ink-line ${collapsed ? "justify-center px-0" : "justify-between px-4"}`}>
        {!collapsed && <IgpLogo size={26} withWord />}
        <button onClick={toggleCollapse} title={collapsed ? "Expandir" : "Contraer"} className="icon-btn shrink-0">
          <Menu size={20} />
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4 flex flex-col gap-1">
        {ITEMS.map((it) => <Item key={it.to} {...it} collapsed={collapsed} />)}
      </nav>

      {!collapsed && (
        <div className="px-5 py-4 border-t border-ink-line">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-60 animate-ping" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-cyan-400" />
            </span>
            <span className="text-[10px] uppercase tracking-[0.18em] text-txt-mute font-medium">Prospección activa</span>
          </div>
        </div>
      )}
    </aside>
  );
}
