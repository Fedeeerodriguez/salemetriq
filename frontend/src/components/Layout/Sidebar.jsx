import { NavLink } from "react-router-dom";
import { LayoutGrid, Phone, Users, Mic, FileText } from "lucide-react";
import SalemetriqLogo from "../SalemetriqLogo";

const NAV = [
  { to: "/overview", label: "Overview", icon: LayoutGrid },
  { to: "/calls", label: "Calls", icon: Phone },
  { to: "/closers", label: "Closers", icon: Users },
  { to: "/call-analysis", label: "Call Analysis", icon: Mic },
  { to: "/script-generator", label: "Script Generator", icon: FileText },
];

export default function Sidebar() {
  return (
    <aside className="w-[248px] shrink-0 bg-ink border-r border-ink-line flex flex-col">
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
                  ? "text-gold-400 bg-gold-500/[0.08]"
                  : "text-txt-soft hover:text-txt hover:bg-ink-hover"
              }`
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-[3px] rounded-full bg-gold-500" />
                )}
                <Icon size={18} strokeWidth={1.9} />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
