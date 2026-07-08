import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { AreaChart, Area, ResponsiveContainer, YAxis } from "recharts";
import api from "../utils/api";

/*
 * Overview — dashboard principal.
 * KPIs y pipeline salen de /api/metricas/overview.
 * El foco de la semana sale de /api/metricas/foco (análisis del método) y la
 * actividad reciente de /api/metricas/actividad (datos reales del workspace).
 * El chart de tendencia sigue siendo visual de diseño por ahora.
 */

const money = (n) => "$" + Number(n || 0).toLocaleString("es-AR", { maximumFractionDigits: 0 });
const pct = (a, b) => (b ? Math.round((a / b) * 100) : 0);

const CHART = [
  { s: "S1", v: 22 }, { s: "S2", v: 25 }, { s: "S3", v: 23 }, { s: "S4", v: 30 },
  { s: "S5", v: 27 }, { s: "S6", v: 33 }, { s: "S7", v: 32 }, { s: "S8", v: 38 },
];

// Color del punto según el tipo de evento de actividad.
const DOT = {
  cerro: "#34D399", cyan: "#22D3EE", neg: "#FB7185", neutral: "#6B6B80", info: "#6B6B80",
};

function Kpi({ label, value, delta, up, premium }) {
  return (
    <div className="card p-5">
      <div className="label">{label}</div>
      <div className="flex items-baseline gap-2.5 mt-3.5">
        <span className={`font-display text-[34px] leading-none font-semibold tnum ${premium ? "text-gold-400" : "text-txt"}`}>
          {value}
        </span>
        {delta && <span className={`pill ${up ? "pill-pos" : "pill-neg"}`}>{delta}</span>}
      </div>
    </div>
  );
}

function FunnelBox({ titulo, valor, tint }) {
  const styles = {
    neutral: "bg-ink-raised border-ink-line",
    green: "border-pos/25",
    gold: "border-gold-400/30",
  }[tint];
  const bg = { green: "rgba(52,211,153,0.07)", gold: "rgba(212,175,122,0.08)" }[tint];
  const valColor = tint === "gold" ? "text-gold-400" : "text-txt";
  return (
    <div className={`flex-1 rounded-xl border px-5 py-4 ${styles}`} style={bg ? { background: bg } : undefined}>
      <div className="label">{titulo}</div>
      <div className={`font-display text-[28px] font-semibold tnum mt-2 ${valColor}`}>{valor}</div>
    </div>
  );
}

function Step({ pct, sub }) {
  return (
    <div className="flex flex-col items-center justify-center px-1 shrink-0">
      <ArrowRight size={16} className="text-txt-mute" />
      <div className="text-[13px] font-semibold text-txt mt-1 tnum">{pct}</div>
      <div className="text-[11px] text-txt-mute">{sub}</div>
    </div>
  );
}

function LastDot({ points }) {
  if (!points?.length) return null;
  const p = points[points.length - 1];
  return <circle cx={p.x} cy={p.y} r={4} fill="#22D3EE" stroke="#0A0A0F" strokeWidth={2} />;
}

export default function Overview() {
  const navigate = useNavigate();
  const [m, setM] = useState(null);
  const [foco, setFoco] = useState(null);
  const [actividad, setActividad] = useState(null);

  useEffect(() => {
    api.get("/metricas/overview").then((r) => setM(r.data)).catch(() => setM(null));
    api.get("/metricas/foco").then((r) => setFoco(r.data)).catch(() => setFoco(null));
    api.get("/metricas/actividad").then((r) => setActividad(r.data)).catch(() => setActividad([]));
  }, []);

  const kpis = [
    { label: "Close rate", value: m ? `${m.close_rate}%` : "—" },
    { label: "Facturación cerrada", value: m ? money(m.revenue) : "—", premium: true },
    { label: "Llamadas", value: m ? String(m.total_calls) : "—" },
    { label: "Set rate", value: m ? `${m.set_rate}%` : "—" },
  ];

  return (
    <div className="grid grid-cols-1 xl:grid-cols-[1fr_330px] gap-6">
      {/* ── Columna principal ── */}
      <div className="flex flex-col gap-5 min-w-0">
        {/* KPIs */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {kpis.map((k) => <Kpi key={k.label} {...k} />)}
        </div>

        {/* Pipeline */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="font-display text-[15px] font-semibold text-txt">Pipeline</h2>
            <span className="text-[13px] text-txt-mute">Acumulado</span>
          </div>
          <div className="flex items-stretch gap-2">
            <FunnelBox titulo="Llamadas" valor={m ? String(m.total_calls) : "—"} tint="neutral" />
            <Step pct={m ? `${pct(m.presentaron, m.total_calls)}%` : "—"} sub="show" />
            <FunnelBox titulo="Se presentaron" valor={m ? String(m.presentaron) : "—"} tint="green" />
            <Step pct={m ? `${pct(m.cerradas, m.presentaron)}%` : "—"} sub="cierre" />
            <FunnelBox titulo="Cerradas" valor={m ? String(m.cerradas) : "—"} tint="gold" />
          </div>
        </div>

        {/* Close rate chart */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display text-[15px] font-semibold text-txt">Close rate — últimas 8 semanas</h2>
            <button className="text-[13px] text-txt-mute hover:text-iris-400 transition-colors">Ver detalle</button>
          </div>
          <div className="h-[200px] -mx-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={CHART} margin={{ top: 8, right: 12, bottom: 0, left: 12 }}>
                <defs>
                  <linearGradient id="accentStroke" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#7C3AED" />
                    <stop offset="100%" stopColor="#22D3EE" />
                  </linearGradient>
                  <linearGradient id="accentFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#7C3AED" stopOpacity={0.28} />
                    <stop offset="100%" stopColor="#22D3EE" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <YAxis hide domain={["dataMin - 6", "dataMax + 4"]} />
                <Area
                  type="monotone" dataKey="v" stroke="url(#accentStroke)" strokeWidth={2.5}
                  fill="url(#accentFill)" dot={<LastDot />} activeDot={false} isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ── Panel derecho ── */}
      <div className="flex flex-col gap-5">
        {/* Foco de la semana — análisis del equipo contra el método (pulso violeta→cian) */}
        <div className="card liquid p-5 ring-1 ring-iris-500/25">
          <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-accent">Foco de la semana</div>
          {foco === null ? (
            <p className="text-[13.5px] text-txt-mute mt-3">Cargando…</p>
          ) : (
            <>
              <h3 className="font-display text-[18px] font-semibold text-txt mt-2">{foco.titulo}</h3>
              <p className="text-[13.5px] text-txt-soft leading-relaxed mt-2">{foco.texto}</p>
              {foco.disponible && foco.score != null && (
                <div className="flex items-center gap-3 mt-4">
                  <div className="flex-1 h-1.5 rounded-full bg-ink-line overflow-hidden">
                    <div className="h-full rounded-full bg-accent-grad" style={{ width: `${foco.score}%` }} />
                  </div>
                  <span className="text-[13px] font-semibold text-iris-400 tnum">{foco.score}/100</span>
                </div>
              )}
              <button
                onClick={() => navigate(foco.disponible ? "/coaching" : "/conexiones")}
                className="btn-primary w-full mt-4 text-[14px]"
              >
                {foco.disponible ? "Ver plan de la semana" : "Conectar mis llamadas"}
              </button>
            </>
          )}
        </div>

        {/* Actividad reciente */}
        <div className="card p-5">
          <h3 className="font-display text-[15px] font-semibold text-txt mb-4">Actividad reciente</h3>
          {actividad === null ? (
            <p className="text-[13px] text-txt-mute">Cargando…</p>
          ) : actividad.length === 0 ? (
            <p className="text-[13px] text-txt-mute">Todavía no hay actividad. Cuando entren llamadas y resúmenes, van a aparecer acá.</p>
          ) : (
            <div className="flex flex-col gap-4">
              {actividad.map((a, i) => (
                <div key={i} className="flex gap-3">
                  <span className="mt-1.5 w-2 h-2 rounded-full shrink-0" style={{ background: DOT[a.tipo] || DOT.neutral }} />
                  <div className="min-w-0">
                    <p className="text-[13.5px] text-txt leading-snug">
                      <span className="font-semibold">{a.nombre}</span> {a.texto}
                    </p>
                    <p className="text-[12px] text-txt-mute mt-0.5">{a.hace}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
