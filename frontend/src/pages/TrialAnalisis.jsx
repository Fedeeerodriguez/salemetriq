import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Loader2, Wand2, FileText, Sparkles, TrendingUp, MessageSquareQuote, CheckCircle2,
  ArrowRight, GraduationCap, AlertTriangle,
} from "lucide-react";
import SalemetriqLogo from "../components/SalemetriqLogo";
import publicApi from "../utils/publicApi";
import { SAMPLE_CALL } from "../data/sampleCall";

const AGENDA_URL = "mailto:hola@salemetriq.com?subject=Quiero%20la%20mentor%C3%ADa%20de%20ventas";

const ETAPA_LABEL = {
  cualificacion: "Cualificación", visualizacion: "Visualización", consecuencia: "Consecuencia (Miedo)",
  pitch: "Pitch", objeciones: "Objeciones", cierre: "Cierre",
};
const ORDEN = ["cualificacion", "visualizacion", "consecuencia", "pitch", "objeciones", "cierre"];

const CHECK_LABELS = {
  uso_especificamente: "Preguntó el outcome 'específicamente'",
  outcome_definido: "Definió el resultado deseado",
  urgencia_tiempo: "Construyó urgencia con el tiempo",
  motivo_emocional_profundo: "Llegó al motivo emocional profundo",
  tres_creencias: "Chequeó las 3 creencias",
  lenguaje_cuando_yo_te_lleve: "Lenguaje 'cuando YO te lleve'",
  profundizo_visualizacion: "Profundizó la visualización",
  reality_check: "Hizo el Reality Check antes del miedo",
  como_te_harias_sentir: "Usó '¿cómo te harías sentir?'",
  pregunta_del_control: "Pregunta del control (→ 'yo')",
  micro_compromiso_pre_pitch: "Micro-compromiso antes del pitch",
  pitch_que_porque_como: "Pitch con QUÉ / POR QUÉ / CÓMO",
  objeciones_orden_correcto: "Objeciones en orden correcto",
  asumio_cierre: "Asumió el cierre",
  tie_down: "Usó tie-downs de compromiso",
};

const barColor = (v) => (v == null ? "bg-ink-line" : v < 40 ? "bg-neg" : v < 65 ? "bg-gold-400" : "bg-pos");
const PRIO = { alta: "pill-neg", media: "text-gold-400 bg-gold-400/12", baja: "text-txt-mute bg-white/[0.05]" };

function Diagnostico({ a }) {
  const score = a.score_global ?? "—";
  const faltaron = Object.entries(a.checklist || {}).filter(([, v]) => !v).map(([k]) => CHECK_LABELS[k] || k).slice(0, 6);
  return (
    <div className="flex flex-col gap-5">
      {/* Score + resumen */}
      <div className="card liquid p-6 flex flex-col sm:flex-row gap-6 items-center">
        <div className="text-center shrink-0">
          <div className="label">Score del método</div>
          <div className="font-display text-[56px] leading-none font-semibold text-gold-400 tnum">{score}<span className="text-[22px] text-txt-mute">/100</span></div>
        </div>
        <div className="flex-1">
          {a.resumen && <p className="text-[14px] text-txt-soft leading-relaxed">{a.resumen}</p>}
          {a.sentiment && <span className="pill text-iris-300 bg-iris-500/12 mt-3 inline-block capitalize">Sentiment: {a.sentiment}</span>}
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-5">
        {/* Score por etapa */}
        <div className="card p-5">
          <h3 className="font-display text-[15px] font-semibold text-txt mb-4 flex items-center gap-2"><TrendingUp size={16} className="text-iris-400" /> Score por etapa</h3>
          <div className="flex flex-col gap-2.5">
            {ORDEN.map((e) => {
              const v = a.dimensiones?.[e];
              return (
                <div key={e} className="flex items-center gap-3">
                  <span className="text-[12.5px] w-36 shrink-0 text-txt-soft">{ETAPA_LABEL[e]}</span>
                  <div className="flex-1 h-2 rounded-full bg-ink-raised overflow-hidden">
                    <div className={`h-full ${barColor(v)}`} style={{ width: `${v ?? 0}%` }} />
                  </div>
                  <span className="text-[12.5px] tnum w-8 text-right text-txt">{v ?? "—"}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Técnicas que faltaron */}
        <div className="card p-5">
          <h3 className="font-display text-[15px] font-semibold text-txt mb-4 flex items-center gap-2"><AlertTriangle size={16} className="text-gold-400" /> Técnicas que faltaron</h3>
          {faltaron.length ? (
            <div className="flex flex-col gap-2">
              {faltaron.map((f, i) => (
                <div key={i} className="flex items-center gap-2 text-[13px] text-txt-soft">
                  <span className="w-1.5 h-1.5 rounded-full bg-neg shrink-0" /> {f}
                </div>
              ))}
            </div>
          ) : <p className="text-[13px] text-txt-mute">Ejecutó bien las técnicas del método. 👏</p>}
        </div>
      </div>

      {/* Mejoras con frases */}
      {a.mejoras?.length > 0 && (
        <div className="card p-5">
          <h3 className="font-display text-[15px] font-semibold text-txt mb-4 flex items-center gap-2"><MessageSquareQuote size={16} className="text-cyan-400" /> Cómo mejorar (frases concretas)</h3>
          <div className="flex flex-col gap-3">
            {a.mejoras.slice(0, 5).map((m, i) => (
              <div key={i} className="bg-ink-raised rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  {m.etapa && <span className="text-[11px] text-txt-mute capitalize">{ETAPA_LABEL[m.etapa] || m.etapa}</span>}
                  {m.prioridad && <span className={`pill ${PRIO[m.prioridad] || ""} text-[10px]`}>{m.prioridad}</span>}
                </div>
                <p className="text-[13.5px] text-txt-soft">{m.accion}</p>
                {m.ejemplo && <p className="text-[13px] text-cyan-300 italic mt-1.5">“{m.ejemplo}”</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Próxima acción */}
      {a.proxima_accion && (
        <div className="card liquid p-5 ring-1 ring-iris-500/25">
          <div className="label text-accent mb-1.5">La UNA cosa a trabajar</div>
          <p className="text-[14.5px] text-txt">{a.proxima_accion}</p>
        </div>
      )}
    </div>
  );
}

export default function TrialAnalisis() {
  const navigate = useNavigate();
  const [token] = useState(() => localStorage.getItem("smq_trial"));
  const [email, setEmail] = useState("");
  const [restantes, setRestantes] = useState(1);
  const [transcript, setTranscript] = useState("");
  const [analisis, setAnalisis] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!token) { navigate("/prueba", { replace: true }); return; }
    publicApi.get(`/leadmagnet/estado?token=${encodeURIComponent(token)}`)
      .then((r) => {
        setEmail(r.data.email);
        setRestantes(r.data.analisis_restantes);
        if (r.data.ultimo_analisis) setAnalisis(r.data.ultimo_analisis);
      })
      .catch(() => navigate("/prueba", { replace: true }));
  }, [token, navigate]);

  async function analizar() {
    setErr(""); setBusy(true); setAnalisis(null);
    try {
      const r = await publicApi.post("/leadmagnet/analizar", { token, transcript });
      setAnalisis(r.data.analisis);
      setRestantes(r.data.analisis_restantes);
    } catch (e) {
      setErr(e.response?.data?.detail || "No se pudo analizar. Probá de nuevo.");
    } finally { setBusy(false); }
  }

  const sinCupo = restantes <= 0;

  return (
    <div className="min-h-screen">
      {/* Top bar */}
      <header className="glass-panel border-b border-white/[0.06]">
        <div className="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
          <a href="/prueba"><SalemetriqLogo size={24} withWord /></a>
          <div className="flex items-center gap-3 text-[12.5px] text-txt-mute">
            {email && <span className="hidden sm:inline">{email}</span>}
            <span className="pill text-iris-300 bg-iris-500/12">{restantes} análisis restante(s)</span>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-10 flex flex-col gap-6">
        <div>
          <h1 className="font-display text-[28px] font-semibold text-txt">Tu análisis de prueba</h1>
          <p className="text-[14px] text-txt-soft mt-1">Pegá la transcripción de una llamada de ventas y la analizamos contra el método. ¿No tenés una a mano? Usá el ejemplo.</p>
        </div>

        {/* Input */}
        {!sinCupo && (
          <div className="card p-5 flex flex-col gap-3">
            <textarea
              className="input h-52 resize-none font-mono text-[12.5px] leading-relaxed"
              placeholder="Pegá acá la transcripción (Closer: ... / Prospecto: ...)"
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
            />
            {err && <div className="text-[12.5px] text-neg">{err}</div>}
            <div className="flex flex-wrap items-center gap-3">
              <button onClick={analizar} disabled={busy || transcript.trim().length < 200} className="btn-primary flex items-center gap-2 text-[14px]">
                {busy ? <Loader2 size={16} className="animate-spin" /> : <Wand2 size={16} />}
                {busy ? "Analizando…" : "Analizar mi llamada"}
              </button>
              <button onClick={() => setTranscript(SAMPLE_CALL)} className="btn-ghost flex items-center gap-2 text-[13px]">
                <FileText size={15} /> Usar llamada de ejemplo
              </button>
              <span className="text-[12px] text-txt-mute ml-auto">{transcript.trim().length} caracteres</span>
            </div>
          </div>
        )}

        {/* Loading */}
        {busy && (
          <div className="card p-10 flex flex-col items-center text-center gap-3">
            <Loader2 size={28} className="text-iris-400 animate-spin" />
            <p className="text-[14px] text-txt-soft">Evaluando la llamada etapa por etapa…</p>
          </div>
        )}

        {/* Resultado */}
        {analisis && !busy && (
          <>
            <div className="flex items-center gap-2">
              <Sparkles size={16} className="text-iris-400" />
              <span className="text-[13px] font-semibold uppercase tracking-[0.12em] text-accent">Diagnóstico</span>
            </div>
            <Diagnostico a={analisis} />
          </>
        )}

        {/* Upsell / cierre del funnel */}
        {(analisis || sinCupo) && !busy && (
          <div className="card liquid p-6 sm:p-8 ring-1 ring-gold-400/25 text-center flex flex-col items-center gap-4 mt-2">
            <GraduationCap size={26} className="text-gold-400" />
            <h2 className="font-display text-[24px] font-semibold text-txt">Esto es una sola llamada. Imaginá todo tu equipo.</h2>
            <p className="text-[14px] text-txt-soft max-w-xl">
              Con SALEMETRIQ + la mentoría de ventas, cada closer conecta sus llamadas, ves dónde falla el equipo entero
              y entrenamos el método hasta que cierren más. Analizar → corregir → volver a medir.
            </p>
            <a href={AGENDA_URL} className="btn-primary flex items-center gap-2 text-[15px] py-3 px-6">
              Agendar mi diagnóstico <ArrowRight size={16} />
            </a>
            {sinCupo && <p className="text-[12px] text-txt-mute">Ya usaste tu análisis gratuito.</p>}
          </div>
        )}
      </main>
    </div>
  );
}
