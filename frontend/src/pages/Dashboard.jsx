import { useEffect, useState } from "react";
import { TrendingUp, PhoneCall, DollarSign, CalendarCheck } from "lucide-react";
import api from "../utils/api";

function StatCard({ icon: Icon, label, value, accent = "pulse" }) {
  const color = accent === "champ" ? "text-champ" : "text-pulse-300";
  return (
    <div className="card p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-xs text-[#6C7B84] uppercase tracking-[0.18em]">{label}</span>
        <Icon size={18} className="text-[#6C7B84]" />
      </div>
      <div className={`font-data text-3xl font-bold ${color}`}>{value}</div>
    </div>
  );
}

export default function Dashboard() {
  const [m, setM] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get("/metricas/overview")
      .then((r) => setM(r.data))
      .catch(() => setErr("Aún no hay datos — conectá Supabase y cargá llamadas."));
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-[#EAF2F3]">Dashboard</h1>
        <p className="text-sm text-[#6C7B84]">Telemetría del equipo de ventas — visión general.</p>
      </div>

      {err && <div className="card p-4 text-sm text-[#8B949E]">{err}</div>}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={TrendingUp} label="Close rate" value={m ? `${m.close_rate}%` : "—"} accent="champ" />
        <StatCard icon={DollarSign} label="Revenue" value={m ? `$${m.revenue.toLocaleString("en-US")}` : "—"} />
        <StatCard icon={PhoneCall} label="Llamadas" value={m ? m.total_calls : "—"} />
        <StatCard icon={CalendarCheck} label="Set rate" value={m ? `${m.set_rate}%` : "—"} />
      </div>
    </div>
  );
}
