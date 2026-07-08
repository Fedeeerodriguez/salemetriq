import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Phone, Headphones, TrendingUp, CheckCircle2, XCircle, GraduationCap } from "lucide-react";
import api from "../utils/api";
import TelemetryPulse from "../components/TelemetryPulse";
import { EtapasBars, ChecklistAdopcion } from "./Coaching";

const money = (n) => "$" + Number(n || 0).toLocaleString("es-AR", { maximumFractionDigits: 0 });
const fecha = (f) =>
  f ? new Date(f).toLocaleDateString("es-AR", { day: "2-digit", month: "short" }) : "—";

const OUTCOME = {
  cerro: { label: "Cerró", cls: "pill-pos" },
  no_cerro: { label: "No cerró", cls: "pill-neg" },
  seguimiento: { label: "Seguimiento", cls: "pill text-iris-400 bg-iris-500/12" },
  no_show: { label: "No show", cls: "pill text-txt-mute bg-white/[0.05]" },
};

function Kpi({ label, value, money: isMoney, premium }) {
  const val = isMoney ? money(value) : value;
  return (
    <div className="card p-4">
      <div className="label">{label}</div>
      <div className={`font-display text-[26px] font-semibold tnum mt-2 ${premium ? "text-gold-400" : "text-txt"}`}>
        {val}
      </div>
    </div>
  );
}

function Bar({ k, v, max = 100 }) {
  return (
    <div className="flex items-center gap-3">
      <span className="w-28 shrink-0 text-[13px] text-txt-soft capitalize truncate">{k}</span>
      <div className="flex-1 h-1.5 rounded-full bg-ink-line overflow-hidden">
        <div className="h-full rounded-full bg-accent-grad" style={{ width: `${(v / max) * 100}%` }} />
      </div>
      <span className="font-display text-[13px] text-txt tnum w-8 text-right">{v}</span>
    </div>
  );
}

export default function UserProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [p, setP] = useState(null);
  const [coach, setCoach] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    setP(null);
    setCoach(null);
    api.get(`/users/${id}/profile`).then((r) => setP(r.data)).catch(() => setErr("No se pudo cargar el perfil."));
    api.get(`/coaching/closer/${id}`).then((r) => setCoach(r.data.n ? r.data : null)).catch(() => {});
  }, [id]);

  if (err) return <div className="card p-5 text-[14px] text-txt-soft">{err}</div>;
  if (!p) return <div className="card p-5 text-[14px] text-txt-mute">Cargando perfil…</div>;

  const isCloser = p.rol === "closer";
  const RolIcon = isCloser ? Phone : Headphones;
  const maxCalif = Math.max(1, ...(p.calificaciones || []).map((c) => c.v));

  return (
    <div className="flex flex-col gap-5">
      <button onClick={() => navigate(-1)} className="btn-ghost self-start flex items-center gap-2 -ml-2">
        <ArrowLeft size={16} /> Volver
      </button>

      {/* Header */}
      <div className="card liquid p-6 flex items-center gap-5">
        <div className="w-16 h-16 rounded-2xl bg-iris-500/20 text-iris-300 grid place-items-center text-[26px] font-display font-semibold shrink-0 ring-1 ring-iris-500/30">
          {(p.nombre || p.email || "?").slice(0, 1).toUpperCase()}
        </div>
        <div className="min-w-0 flex-1">
          <h1 className="font-display text-[24px] font-semibold text-txt truncate">{p.nombre || p.email}</h1>
          <div className="flex items-center gap-2 mt-1">
            <span className="pill text-iris-400 bg-iris-500/12 flex items-center gap-1">
              <RolIcon size={11} /> {p.rol}
            </span>
            <span className="text-[13px] text-txt-mute truncate">{p.email}</span>
          </div>
        </div>
        <div className="hidden md:block w-40 shrink-0 opacity-70">
          <TelemetryPulse height={38} />
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {(p.kpis || []).map((k) => <Kpi key={k.label} {...k} />)}
      </div>

      {/* Coaching contra el método (closers con llamadas analizadas) */}
      {isCloser && coach && (
        <div className="card liquid p-5 flex flex-col gap-4">
          <div className="flex items-center gap-2">
            <GraduationCap size={16} className="text-accent" />
            <span className="label text-accent">Coaching contra el método</span>
            <span className="text-[11px] text-txt-mute tnum ml-auto">{coach.n} llamada(s)</span>
          </div>
          {coach.narrativa && (
            <div className="text-[13.5px] text-txt-soft whitespace-pre-wrap leading-relaxed">{coach.narrativa}</div>
          )}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 pt-1">
            <div>
              <div className="label mb-3">Promedio por etapa</div>
              <EtapasBars etapas={coach.etapas_prom} debil={coach.etapa_debil} />
            </div>
            <div>
              <div className="label mb-3">Técnicas menos usadas</div>
              <ChecklistAdopcion checklist={(coach.checklist || []).slice(0, 6)} />
            </div>
          </div>
          {coach.ejemplos_mejora?.length > 0 && (
            <div className="pt-1">
              <div className="label mb-2">Frases a corregir</div>
              <div className="flex flex-col gap-2">
                {coach.ejemplos_mejora.map((m, i) => (
                  <div key={i} className="bg-ink-raised rounded-lg px-3 py-2 text-[12.5px]">
                    <span className="text-txt-mute capitalize">{m.etapa}:</span>{" "}
                    <span className="text-txt-soft">{m.accion}</span>
                    {m.ejemplo && <div className="text-accent mt-1 italic">“{m.ejemplo}”</div>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_1fr] gap-5">
        {/* Performance */}
        <div className="flex flex-col gap-5">
          {isCloser && (
            <>
              <div className="card p-5">
                <h3 className="font-display text-[15px] font-semibold text-txt mb-4 flex items-center gap-2">
                  <TrendingUp size={16} className="text-iris-400" /> Score por dimensión
                </h3>
                <div className="flex flex-col gap-3">
                  {(p.dimensiones || []).map((d) => <Bar key={d.k} k={d.k} v={d.v} />)}
                  {(!p.dimensiones || p.dimensiones.length === 0) && (
                    <p className="text-[13px] text-txt-mute">Sin análisis de llamadas todavía.</p>
                  )}
                </div>
              </div>

              <div className="card p-5">
                <h3 className="font-display text-[15px] font-semibold text-txt mb-4">Sentiment de llamadas</h3>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { k: "positivo", cls: "text-pos" },
                    { k: "neutral", cls: "text-iris-400" },
                    { k: "negativo", cls: "text-neg" },
                  ].map(({ k, cls }) => (
                    <div key={k} className="bg-ink-raised rounded-xl p-3 text-center">
                      <div className={`font-display text-[22px] font-semibold tnum ${cls}`}>
                        {p.sentiment?.[k] ?? 0}
                      </div>
                      <div className="text-[11px] text-txt-mute capitalize mt-0.5">{k}</div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {!isCloser && (
            <div className="card p-5">
              <h3 className="font-display text-[15px] font-semibold text-txt mb-4">Calidad de leads</h3>
              <div className="flex flex-col gap-3">
                {(p.calificaciones || []).map((c) => <Bar key={c.k} k={c.k} v={c.v} max={maxCalif} />)}
                {(!p.calificaciones || p.calificaciones.length === 0) && (
                  <p className="text-[13px] text-txt-mute">Sin resúmenes todavía.</p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Timeline */}
        <div className="card p-5">
          <h3 className="font-display text-[15px] font-semibold text-txt mb-4">Actividad reciente</h3>
          <div className="flex flex-col">
            {(p.timeline || []).map((t, i) => (
              <div key={i} className="flex items-center gap-3 py-2.5 border-b border-white/[0.05] last:border-0">
                <span className="text-[12px] text-txt-mute tnum w-12 shrink-0">{fecha(t.fecha)}</span>
                <span className="flex-1 min-w-0 text-[13.5px] text-txt truncate">{t.titulo}</span>
                {isCloser ? (
                  <>
                    <span className={OUTCOME[t.outcome]?.cls || "pill"}>{OUTCOME[t.outcome]?.label || t.outcome}</span>
                    <span className="font-display text-[13px] text-gold-400 tnum w-16 text-right">
                      {t.outcome === "cerro" ? money(t.valor) : "—"}
                    </span>
                  </>
                ) : (
                  <>
                    <span className="text-[11px] text-txt-mute">{t.calif}</span>
                    {t.agendado ? (
                      <CheckCircle2 size={16} className="text-pos shrink-0" />
                    ) : (
                      <XCircle size={16} className="text-txt-mute shrink-0" />
                    )}
                  </>
                )}
              </div>
            ))}
            {(!p.timeline || p.timeline.length === 0) && (
              <p className="text-[13px] text-txt-mute">Sin actividad todavía.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
