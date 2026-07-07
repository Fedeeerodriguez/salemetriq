import { useEffect, useState } from "react";
import { Download, TrendingUp, Phone, Headphones, Gauge, AlertTriangle, Flame, ArrowDown, Clock } from "lucide-react";
import api from "../utils/api";

const money = (n) => "$" + (n || 0).toLocaleString("es-AR");

function Kpi({ icon: Icon, label, value, sub, tint }) {
  return (
    <div className="card p-4 flex flex-col gap-1.5">
      <div className="flex items-center gap-2 text-txt-mute">
        <Icon size={15} className={tint} />
        <span className="text-[11px] uppercase tracking-[0.14em]">{label}</span>
      </div>
      <div className="font-display text-[26px] font-semibold text-txt tnum leading-none">{value}</div>
      {sub && <div className="text-[12px] text-txt-mute">{sub}</div>}
    </div>
  );
}

const ALERT_ICON = { lead_caliente_sin_agendar: Flame, closer_score_bajo: ArrowDown, grabaciones_sin_analizar: Clock };
const SEV = {
  alta: "text-neg bg-neg/12 ring-neg/25",
  media: "text-gold-400 bg-gold-400/12 ring-gold-400/25",
  baja: "text-txt-soft bg-white/[0.06] ring-white/10",
};

export default function Reportes() {
  const [rep, setRep] = useState(null);
  const [alertas, setAlertas] = useState([]);
  const [err, setErr] = useState("");
  const [bajando, setBajando] = useState(false);

  useEffect(() => {
    Promise.all([api.get("/reportes/semanal"), api.get("/reportes/alertas")])
      .then(([r, a]) => { setRep(r.data); setAlertas(a.data); })
      .catch(() => setErr("No se pudieron cargar los reportes."));
  }, []);

  async function exportar() {
    setBajando(true);
    try {
      const r = await api.get("/reportes/export.csv", { responseType: "blob" });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement("a");
      a.href = url; a.download = "salemetriq_llamadas.csv";
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setBajando(false);
    }
  }

  if (err) return <div className="card p-5 text-[14px] text-neg">{err}</div>;
  if (!rep) return <div className="card p-5 text-[14px] text-txt-mute">Cargando reportes…</div>;
  if (rep.vacio) return <div className="card p-5 text-[14px] text-txt-mute">Todavía no hay datos en tu workspace.</div>;

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between gap-4">
        <p className="text-[14px] text-txt-soft">Resumen de los últimos 7 días de tu workspace.</p>
        <button onClick={exportar} disabled={bajando} className="btn-ghost flex items-center gap-2 text-[13.5px]">
          <Download size={15} /> {bajando ? "Generando…" : "Exportar CSV"}
        </button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Kpi icon={Phone} label="Llamadas" value={rep.llamadas.total} sub={`${rep.llamadas.cerradas} cerradas`} tint="text-gold-400" />
        <Kpi icon={TrendingUp} label="Close rate" value={`${rep.llamadas.close_rate}%`} sub={money(rep.llamadas.facturado) + " facturado"} tint="text-pos" />
        <Kpi icon={Headphones} label="Set rate" value={`${rep.setting.set_rate}%`} sub={`${rep.setting.agendados}/${rep.setting.resumenes} agendados`} tint="text-cyan-400" />
        <Kpi icon={Gauge} label="Score prom" value={rep.calidad.score_prom ?? "—"} sub={`${rep.calidad.analizadas} analizadas`} tint="text-iris-400" />
      </div>

      {/* Alertas */}
      <div className="card overflow-hidden">
        <div className="px-5 py-3 border-b border-white/[0.06] flex items-center gap-2">
          <AlertTriangle size={15} className="text-gold-400" />
          <span className="label">Alertas</span>
          <span className="text-[11px] text-txt-mute tnum">{alertas.length}</span>
        </div>
        {alertas.length === 0 ? (
          <div className="px-5 py-8 text-center text-[13.5px] text-txt-mute">Todo en orden. Sin alertas 🎉</div>
        ) : alertas.map((a, i) => {
          const Icon = ALERT_ICON[a.tipo] || AlertTriangle;
          return (
            <div key={i} className="flex items-start gap-3 px-5 py-3.5 border-b border-white/[0.05] last:border-0">
              <div className={`w-7 h-7 rounded-lg grid place-items-center ring-1 shrink-0 ${SEV[a.severidad]}`}><Icon size={14} /></div>
              <div className="min-w-0 flex-1">
                <div className="text-[13.5px] text-txt">{a.titulo}{a.quien && <span className="text-txt-mute"> · {a.quien}</span>}</div>
                {a.detalle && <div className="text-[12.5px] text-txt-mute truncate">{a.detalle}</div>}
              </div>
              <span className={`pill ${SEV[a.severidad]} ring-1 shrink-0`}>{a.severidad}</span>
            </div>
          );
        })}
      </div>

      {/* Ranking de closers */}
      <div className="card overflow-hidden">
        <div className="px-5 py-3 border-b border-white/[0.06] label">Ranking de closers (7 días)</div>
        {rep.ranking_closers.length === 0 ? (
          <div className="px-5 py-8 text-center text-[13.5px] text-txt-mute">Sin llamadas en el período.</div>
        ) : rep.ranking_closers.map((c, i) => (
          <div key={c.closer_id} className="grid grid-cols-[auto_1fr_auto_auto] gap-4 items-center px-5 py-3 border-b border-white/[0.05] last:border-0">
            <span className="text-[13px] text-txt-mute tnum w-5">{i + 1}</span>
            <span className="text-[14px] text-txt truncate">{c.nombre}</span>
            <span className="text-[13px] text-txt-mute tnum">{c.cerradas}/{c.llamadas}</span>
            <span className="font-display text-[15px] font-semibold text-pos tnum w-12 text-right">{c.close_rate}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
