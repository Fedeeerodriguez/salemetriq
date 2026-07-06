import { ArrowRight } from "lucide-react";
import { AreaChart, Area, ResponsiveContainer, YAxis } from "recharts";

/*
 * Overview — dashboard principal (visual-first).
 * Los valores son datos de diseño/demo; se reemplazan por /api/metricas/overview
 * y consultas reales en la fase de datos.
 */

const KPIS = [
  { label: "Show rate", value: "67%", delta: "+4%", up: true },
  { label: "Close rate", value: "35%", delta: "-2%", up: false },
  { label: "Llamadas agendadas", value: "142", delta: "+11", up: true },
  { label: "Facturación cerrada", value: "$48.2k", delta: "+9%", up: true },
];

const CHART = [
  { s: "S1", v: 22 }, { s: "S2", v: 25 }, { s: "S3", v: 23 }, { s: "S4", v: 30 },
  { s: "S5", v: 27 }, { s: "S6", v: 33 }, { s: "S7", v: 32 }, { s: "S8", v: 38 },
];

const ACTIVIDAD = [
  { dot: "#37D6A0", nombre: "Fede R.", texto: "cerró con Marina S. — $2.400", cuando: "Hace 24 min" },
  { dot: "#6E6E73", nombre: "Marina G.", texto: "cargó transcript de call — Lucas D.", cuando: "Hace 1 h" },
  { dot: "#F0736F", nombre: "Tomás L.", texto: "— no show, Nico F.", cuando: "Hace 2 h" },
  { dot: "#37D6A0", nombre: "Nico F.", texto: "cerró con Paula V. — $3.100", cuando: "Hace 3 h" },
];

function Kpi({ label, value, delta, up }) {
  return (
    <div className="card p-5">
      <div className="label">{label}</div>
      <div className="flex items-baseline gap-2.5 mt-3.5">
        <span className="text-[34px] leading-none font-semibold tnum text-txt">{value}</span>
        <span className={`pill ${up ? "pill-pos" : "pill-neg"}`}>{delta}</span>
      </div>
    </div>
  );
}

function FunnelBox({ titulo, valor, tint }) {
  const styles = {
    neutral: "bg-ink-raised border-ink-line",
    green: "border-pos/25",
    gold: "border-gold-500/25",
  }[tint];
  const bg = { green: "rgba(55,214,160,0.07)", gold: "rgba(227,154,52,0.07)" }[tint];
  return (
    <div className={`flex-1 rounded-xl border px-5 py-4 ${styles}`} style={bg ? { background: bg } : undefined}>
      <div className="label">{titulo}</div>
      <div className="text-[28px] font-semibold tnum text-txt mt-2">{valor}</div>
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
  return <circle cx={p.x} cy={p.y} r={4} fill="#F1AC43" stroke="#0B0B0D" strokeWidth={2} />;
}

export default function Overview() {
  return (
    <div className="grid grid-cols-1 xl:grid-cols-[1fr_330px] gap-6">
      {/* ── Columna principal ── */}
      <div className="flex flex-col gap-5 min-w-0">
        {/* KPIs */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {KPIS.map((k) => <Kpi key={k.label} {...k} />)}
        </div>

        {/* Pipeline de la semana */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-[15px] font-semibold text-txt">Pipeline de la semana</h2>
            <span className="text-[13px] text-txt-mute">29 jun — 5 jul</span>
          </div>
          <div className="flex items-stretch gap-2">
            <FunnelBox titulo="Agendadas" valor="142" tint="neutral" />
            <Step pct="67%" sub="show" />
            <FunnelBox titulo="Se presentaron" valor="96" tint="green" />
            <Step pct="35%" sub="cierre" />
            <FunnelBox titulo="Cerradas" valor="34" tint="gold" />
          </div>
        </div>

        {/* Close rate chart */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-[15px] font-semibold text-txt">Close rate — últimas 8 semanas</h2>
            <button className="text-[13px] text-txt-mute hover:text-gold-400 transition-colors">Ver detalle</button>
          </div>
          <div className="h-[200px] -mx-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={CHART} margin={{ top: 8, right: 12, bottom: 0, left: 12 }}>
                <defs>
                  <linearGradient id="goldFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#E39A34" stopOpacity={0.28} />
                    <stop offset="100%" stopColor="#E39A34" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <YAxis hide domain={["dataMin - 6", "dataMax + 4"]} />
                <Area
                  type="monotone" dataKey="v" stroke="#F1AC43" strokeWidth={2.5}
                  fill="url(#goldFill)" dot={<LastDot />} activeDot={false} isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ── Panel derecho ── */}
      <div className="flex flex-col gap-5">
        {/* Foco de la semana */}
        <div
          className="rounded-2xl border border-gold-500/20 p-5"
          style={{ background: "linear-gradient(180deg, rgba(227,154,52,0.06), rgba(21,20,23,0.4))" }}
        >
          <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-gold-400">Foco de la semana</div>
          <h3 className="text-[18px] font-semibold text-txt mt-2">Manejo de objeción de precio</h3>
          <p className="text-[13.5px] text-txt-soft leading-relaxed mt-2">
            En 6 de las últimas 12 calls perdidas, la objeción de precio apareció después del
            minuto 20 sin un manejo claro. Trabajen esto antes de sumar nada más.
          </p>
          <div className="flex items-center gap-3 mt-4">
            <div className="flex-1 h-1.5 rounded-full bg-ink-line overflow-hidden">
              <div className="h-full rounded-full bg-gold-500" style={{ width: "78%" }} />
            </div>
            <span className="text-[13px] font-semibold text-gold-400 tnum">78/100</span>
          </div>
          <button className="btn-gold w-full mt-4 text-[14px]">Ver plan de la semana</button>
        </div>

        {/* Actividad reciente */}
        <div className="card p-5">
          <h3 className="text-[15px] font-semibold text-txt mb-4">Actividad reciente</h3>
          <div className="flex flex-col gap-4">
            {ACTIVIDAD.map((a, i) => (
              <div key={i} className="flex gap-3">
                <span className="mt-1.5 w-2 h-2 rounded-full shrink-0" style={{ background: a.dot }} />
                <div className="min-w-0">
                  <p className="text-[13.5px] text-txt leading-snug">
                    <span className="font-semibold">{a.nombre}</span> {a.texto}
                  </p>
                  <p className="text-[12px] text-txt-mute mt-0.5">{a.cuando}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
