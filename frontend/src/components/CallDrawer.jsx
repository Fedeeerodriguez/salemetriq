import { useEffect, useState } from "react";
import {
  X, Maximize2, Minimize2, Sparkles, CheckCircle2, AlertTriangle,
  Target, TrendingUp, Clock, User, Loader2,
} from "lucide-react";
import api from "../utils/api";

const dur = (s) => (s ? `${Math.round(s / 60)} min` : "—");
const fecha = (f) =>
  f ? new Date(f).toLocaleDateString("es-AR", { day: "2-digit", month: "long", year: "numeric" }) : "—";

const PRIO = {
  alta: "text-neg bg-neg/12",
  media: "text-gold-400 bg-gold-400/12",
  baja: "text-txt-mute bg-white/[0.06]",
};
const SENT = { positivo: "pill-pos", neutral: "pill text-iris-400 bg-iris-500/12", negativo: "pill-neg" };
const scoreColor = (n) => (n >= 75 ? "text-pos" : n >= 60 ? "text-gold-400" : "text-neg");

function Section({ icon: Icon, title, children, accent = "text-iris-400" }) {
  return (
    <div className="flex flex-col gap-3">
      <h3 className="flex items-center gap-2 text-[13px] font-semibold uppercase tracking-[0.1em] text-txt-soft">
        <Icon size={14} className={accent} /> {title}
      </h3>
      {children}
    </div>
  );
}

function Bar({ k, v }) {
  return (
    <div className="flex items-center gap-3">
      <span className="w-28 shrink-0 text-[13px] text-txt-soft capitalize truncate">{k}</span>
      <div className="flex-1 h-1.5 rounded-full bg-ink-line overflow-hidden">
        <div className="h-full rounded-full bg-accent-grad" style={{ width: `${v}%` }} />
      </div>
      <span className="font-display text-[13px] text-txt tnum w-8 text-right">{v}</span>
    </div>
  );
}

export default function CallDrawer({ recId, onClose }) {
  const [rec, setRec] = useState(null);
  const [err, setErr] = useState("");
  const [full, setFull] = useState(false);
  const [analizando, setAnalizando] = useState(false);

  useEffect(() => {
    setRec(null);
    setErr("");
    api.get(`/recordings/${recId}`).then((r) => setRec(r.data)).catch(() => setErr("No se pudo cargar la grabación."));
  }, [recId]);

  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function analizar() {
    setAnalizando(true);
    setErr("");
    try {
      await api.post(`/recordings/${recId}/analyze`);
      const r = await api.get(`/recordings/${recId}`);
      setRec(r.data);
    } catch (e) {
      setErr(e.response?.data?.detail || "No se pudo analizar (¿falta ANTHROPIC_API_KEY?).");
    } finally {
      setAnalizando(false);
    }
  }

  const a = rec?.analisis;
  const raw = a?.raw || {};
  const dims = raw.dimensiones || {};
  const mejoras = raw.mejoras || [];
  const fortalezas = raw.fortalezas || [];
  const objeciones = a?.objeciones || raw.objeciones || [];
  const closer = (rec?.participants || []).find((p) => p.rol === "closer");

  return (
    <div className="fixed inset-0 z-40">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <aside
        className={`absolute top-0 h-full glass-panel border-l border-white/[0.08] flex flex-col shadow-glow transition-all ${
          full ? "left-0 right-0" : "right-0 w-full max-w-[580px]"
        }`}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-3 px-6 py-4 border-b border-white/[0.06]">
          <div className="min-w-0">
            <h2 className="font-display text-[18px] font-semibold text-txt truncate">
              {rec?.title || "Grabación"}
            </h2>
            <div className="flex items-center flex-wrap gap-x-3 gap-y-1 mt-1 text-[12px] text-txt-mute">
              <span className="flex items-center gap-1"><User size={12} /> {closer?.nombre || "—"}</span>
              <span className="flex items-center gap-1"><Clock size={12} /> {dur(rec?.duration_seg)} · {fecha(rec?.recorded_at)}</span>
            </div>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <button onClick={() => setFull((f) => !f)} className="icon-btn" title={full ? "Restaurar" : "Pantalla completa"}>
              {full ? <Minimize2 size={17} /> : <Maximize2 size={17} />}
            </button>
            <button onClick={onClose} className="icon-btn" title="Cerrar (Esc)"><X size={18} /></button>
          </div>
        </div>

        {/* Body */}
        <div className={`flex-1 overflow-y-auto px-6 py-5 ${full ? "max-w-3xl mx-auto w-full" : ""}`}>
          {!rec && !err && <div className="text-[13px] text-txt-mute">Cargando…</div>}
          {err && <div className="card p-4 text-[13px] text-neg mb-4">{err}</div>}

          {rec && !a && (
            <div className="card p-6 text-center flex flex-col items-center gap-3">
              <Sparkles size={22} className="text-iris-400" />
              <p className="text-txt font-medium">Esta grabación todavía no se analizó</p>
              <p className="text-[13px] text-txt-mute max-w-sm">
                Corré el análisis IA para obtener score, fortalezas y mejoras accionables.
              </p>
              <button onClick={analizar} disabled={analizando} className="btn-primary flex items-center gap-2 mt-1">
                {analizando ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
                {analizando ? "Analizando…" : "Analizar con IA"}
              </button>
            </div>
          )}

          {rec && a && (
            <div className="flex flex-col gap-6">
              {/* Score + sentiment */}
              <div className="flex items-center gap-5">
                <div className="text-center">
                  <div className={`font-display text-[40px] font-semibold leading-none tnum ${scoreColor(a.score ?? 0)}`}>
                    {a.score != null ? Math.round(a.score) : "—"}
                  </div>
                  <div className="text-[10px] uppercase tracking-wider text-txt-mute mt-1">score</div>
                </div>
                <div className="flex-1">
                  {a.sentiment && <span className={SENT[a.sentiment] || "pill"}>{a.sentiment}</span>}
                  {a.resumen && <p className="text-[13.5px] text-txt-soft leading-relaxed mt-2">{a.resumen}</p>}
                </div>
              </div>

              {/* Próxima acción */}
              {raw.proxima_accion && (
                <div className="card liquid p-4 ring-1 ring-iris-500/25">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.12em] text-accent mb-1.5">
                    Próxima acción
                  </div>
                  <p className="text-[14px] text-txt leading-snug">{raw.proxima_accion}</p>
                </div>
              )}

              {/* Dimensiones */}
              {Object.keys(dims).length > 0 && (
                <Section icon={TrendingUp} title="Score por dimensión">
                  <div className="flex flex-col gap-2.5">
                    {Object.entries(dims).map(([k, v]) => <Bar key={k} k={k} v={v} />)}
                  </div>
                </Section>
              )}

              {/* Fortalezas */}
              {fortalezas.length > 0 && (
                <Section icon={CheckCircle2} title="Fortalezas" accent="text-pos">
                  <ul className="flex flex-col gap-2">
                    {fortalezas.map((f, i) => (
                      <li key={i} className="flex gap-2 text-[13.5px] text-txt-soft">
                        <CheckCircle2 size={15} className="text-pos shrink-0 mt-0.5" /> {f}
                      </li>
                    ))}
                  </ul>
                </Section>
              )}

              {/* Mejoras */}
              {mejoras.length > 0 && (
                <Section icon={Target} title="Mejoras accionables">
                  <div className="flex flex-col gap-3">
                    {mejoras.map((m, i) => (
                      <div key={i} className="bg-ink-raised rounded-xl p-3.5">
                        <div className="flex items-start justify-between gap-3">
                          <p className="text-[13.5px] text-txt font-medium leading-snug">{m.accion}</p>
                          {m.prioridad && (
                            <span className={`pill shrink-0 ${PRIO[m.prioridad] || ""}`}>{m.prioridad}</span>
                          )}
                        </div>
                        {m.ejemplo && (
                          <p className="text-[12.5px] text-txt-soft leading-relaxed mt-2 pl-3 border-l-2 border-iris-500/40 italic">
                            {m.ejemplo}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </Section>
              )}

              {/* Objeciones */}
              {objeciones.length > 0 && (
                <Section icon={AlertTriangle} title="Objeciones" accent="text-gold-400">
                  <div className="flex flex-col gap-2">
                    {objeciones.map((o, i) => (
                      <div key={i} className="flex items-start gap-2 text-[13px]">
                        <span className={`pill shrink-0 ${o.manejada ? "pill-pos" : "pill-neg"}`}>
                          {o.tipo}
                        </span>
                        <span className="text-txt-soft">
                          {o.nota || o.momento || (o.manejada ? "manejada" : "sin resolver")}
                        </span>
                      </div>
                    ))}
                  </div>
                </Section>
              )}

              {/* Transcript */}
              {rec.transcript && (
                <Section icon={Sparkles} title="Transcript">
                  <pre className="text-[12.5px] text-txt-soft whitespace-pre-wrap font-sans leading-relaxed bg-ink-raised rounded-xl p-4 max-h-72 overflow-y-auto">
                    {rec.transcript}
                  </pre>
                </Section>
              )}

              <button onClick={analizar} disabled={analizando} className="btn-ghost self-start flex items-center gap-2 border border-ink-line">
                {analizando ? <Loader2 size={15} className="animate-spin" /> : <Sparkles size={15} />}
                {analizando ? "Analizando…" : "Volver a analizar"}
              </button>
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
