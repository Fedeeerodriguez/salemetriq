import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight, Loader2, CheckCircle2, Sparkles, Gauge, ClipboardList, MessageSquareQuote,
  Zap, ShieldCheck, GraduationCap, Phone, Mail, Star,
} from "lucide-react";
import SalemetriqLogo from "../components/SalemetriqLogo";
import publicApi from "../utils/publicApi";

const AGENDA_URL = "mailto:hola@salemetriq.com?subject=Quiero%20la%20mentor%C3%ADa%20de%20ventas";

/* ─── Formulario de captura (email + teléfono) ─── */
function LeadForm({ variante = "hero" }) {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [tel, setTel] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function enviar(e) {
    e.preventDefault();
    setErr("");
    if (!email.trim() || !tel.trim()) return setErr("Completá tu email y teléfono.");
    setBusy(true);
    try {
      const r = await publicApi.post("/leadmagnet/registro", { email: email.trim(), telefono: tel.trim() });
      localStorage.setItem("smq_trial", r.data.token);
      navigate("/prueba/analisis");
    } catch (e) {
      setErr(e.response?.data?.detail?.[0]?.msg || e.response?.data?.detail || "No se pudo registrar. Revisá los datos.");
    } finally { setBusy(false); }
  }

  return (
    <form onSubmit={enviar} className={`flex flex-col gap-3 ${variante === "hero" ? "" : "max-w-md mx-auto"}`}>
      <div className="relative">
        <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-txt-mute" />
        <input className="input pl-9" type="email" placeholder="tu@email.com" value={email} onChange={(e) => setEmail(e.target.value)} />
      </div>
      <div className="relative">
        <Phone size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-txt-mute" />
        <input className="input pl-9" type="tel" placeholder="+54 9 11 ..." value={tel} onChange={(e) => setTel(e.target.value)} />
      </div>
      {err && <div className="text-[12.5px] text-neg">{err}</div>}
      <button type="submit" disabled={busy} className="btn-primary flex items-center justify-center gap-2 text-[15px] py-3">
        {busy ? <Loader2 size={18} className="animate-spin" /> : <Sparkles size={18} />}
        {busy ? "Preparando tu prueba…" : "Analizar mi llamada gratis"}
      </button>
      <p className="text-[11.5px] text-txt-mute text-center flex items-center justify-center gap-1.5">
        <ShieldCheck size={12} /> Sin tarjeta. 1 análisis gratis con IA en 60 segundos.
      </p>
    </form>
  );
}

/* ─── Mockup del análisis (visual de marca) ─── */
function AnalisisMock() {
  const dims = [
    { k: "Cualificación", v: 78 }, { k: "Visualización", v: 41 },
    { k: "Consecuencia", v: 35 }, { k: "Pitch", v: 72 },
    { k: "Objeciones", v: 38 }, { k: "Cierre", v: 44 },
  ];
  const col = (v) => (v < 40 ? "bg-neg" : v < 65 ? "bg-gold-400" : "bg-pos");
  return (
    <div className="card liquid p-5 w-full">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <SalemetriqLogo size={20} />
          <span className="text-[12px] text-txt-mute">Análisis de llamada</span>
        </div>
        <span className="pill pill-pos flex items-center gap-1"><CheckCircle2 size={11} /> Listo</span>
      </div>
      <div className="flex items-end gap-4 mb-4">
        <div>
          <div className="label">Score del método</div>
          <div className="font-display text-[42px] leading-none font-semibold text-gold-400 tnum">61<span className="text-[20px] text-txt-mute">/100</span></div>
        </div>
        <div className="flex-1 flex flex-col gap-1.5 pb-1">
          {dims.slice(0, 3).map((d) => (
            <div key={d.k} className="flex items-center gap-2">
              <span className="text-[11px] text-txt-soft w-24 shrink-0 truncate">{d.k}</span>
              <div className="flex-1 h-1.5 rounded-full bg-ink-raised overflow-hidden">
                <div className={`h-full ${col(d.v)}`} style={{ width: `${d.v}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="bg-ink-raised rounded-lg p-3 border-l-2 border-neg/50">
        <div className="text-[10px] uppercase tracking-wider text-neg font-medium mb-1">Fuga principal</div>
        <p className="text-[12.5px] text-txt-soft leading-snug">
          No construiste la visualización ni pasaste por el <span className="text-txt">reality check</span> antes del miedo.
          La objeción de precio se manejó con lógica, no con emoción.
        </p>
      </div>
    </div>
  );
}

function Paso({ n, icon: Icon, titulo, texto }) {
  return (
    <div className="card p-6 flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-iris-500/15 grid place-items-center ring-1 ring-iris-500/25">
          <Icon size={18} className="text-iris-300" />
        </div>
        <span className="font-display text-[13px] text-txt-mute">Paso {n}</span>
      </div>
      <h3 className="font-display text-[17px] font-semibold text-txt">{titulo}</h3>
      <p className="text-[13.5px] text-txt-soft leading-relaxed">{texto}</p>
    </div>
  );
}

function Feature({ icon: Icon, titulo, texto }) {
  return (
    <div className="flex gap-3">
      <div className="w-9 h-9 rounded-lg bg-ink-raised grid place-items-center shrink-0 ring-1 ring-ink-line">
        <Icon size={17} className="text-cyan-400" />
      </div>
      <div>
        <h4 className="font-display text-[15px] font-semibold text-txt">{titulo}</h4>
        <p className="text-[13px] text-txt-soft leading-relaxed mt-0.5">{texto}</p>
      </div>
    </div>
  );
}

export default function Landing() {
  return (
    <div className="min-h-screen">
      {/* Nav */}
      <header className="sticky top-0 z-20 glass-panel border-b border-white/[0.06]">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <SalemetriqLogo size={26} withWord />
          <div className="flex items-center gap-4">
            <a href="/login" className="text-[13.5px] text-txt-soft hover:text-txt transition-colors">Iniciar sesión</a>
            <a href="#probar" className="btn-primary text-[13.5px] hidden sm:inline-flex">Probar gratis</a>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section id="probar" className="max-w-6xl mx-auto px-6 pt-16 pb-20 grid lg:grid-cols-2 gap-12 items-center">
        <div className="flex flex-col gap-6">
          <span className="pill text-iris-300 bg-iris-500/12 self-start flex items-center gap-1.5">
            <Zap size={12} /> Conversation Intelligence + Mentoría de ventas
          </span>
          <h1 className="font-display text-[40px] sm:text-[52px] leading-[1.05] font-semibold text-txt">
            Descubrí por qué tus closers <span className="text-accent">no cierran</span> — en 60 segundos.
          </h1>
          <p className="text-[16px] text-txt-soft leading-relaxed max-w-lg">
            Pegá una llamada de ventas y nuestra IA la analiza contra un método de closing probado:
            te da <span className="text-txt">KPIs por etapa</span>, las <span className="text-txt">técnicas que faltaron</span> y
            las <span className="text-txt">frases exactas</span> para cerrar más. Gratis, sin tarjeta.
          </p>
          <div className="card p-5 max-w-md">
            <LeadForm variante="hero" />
          </div>
          <div className="flex items-center gap-2 text-[12.5px] text-txt-mute">
            <div className="flex -space-x-1.5">
              {["#7C3AED", "#22D3EE", "#D4AF7A"].map((c) => (
                <span key={c} className="w-6 h-6 rounded-full ring-2 ring-ink" style={{ background: c }} />
              ))}
            </div>
            Equipos de ventas que ya afilan sus llamadas con SALEMETRIQ
          </div>
        </div>
        <div className="relative">
          <div className="absolute -inset-6 bg-accent-grad opacity-20 blur-3xl rounded-full" />
          <div className="relative"><AnalisisMock /></div>
        </div>
      </section>

      {/* Cómo funciona */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-10">
          <div className="label text-accent mb-2">Cómo funciona</div>
          <h2 className="font-display text-[30px] font-semibold text-txt">De una llamada a un plan de mejora</h2>
        </div>
        <div className="grid md:grid-cols-3 gap-5">
          <Paso n={1} icon={ClipboardList} titulo="Pegás tu llamada" texto="Copiás la transcripción de una llamada de ventas (o probás con nuestro ejemplo). Sin instalar nada." />
          <Paso n={2} icon={Gauge} titulo="La IA la analiza" texto="La evaluamos etapa por etapa contra un método de closing real: cualificación, visualización, miedo, pitch, objeciones y cierre." />
          <Paso n={3} icon={Sparkles} titulo="Recibís tu diagnóstico" texto="KPIs, la fuga principal, las técnicas que faltaron y frases concretas para mejorar. Todo en segundos." />
        </div>
      </section>

      {/* Producto / qué recibís */}
      <section className="max-w-6xl mx-auto px-6 py-16 grid lg:grid-cols-2 gap-12 items-center">
        <div className="order-2 lg:order-1"><AnalisisMock /></div>
        <div className="order-1 lg:order-2 flex flex-col gap-6">
          <div>
            <div className="label text-accent mb-2">Qué vas a recibir</div>
            <h2 className="font-display text-[30px] font-semibold text-txt">El diagnóstico que ningún manager tiene tiempo de hacer</h2>
          </div>
          <div className="flex flex-col gap-5">
            <Feature icon={Gauge} titulo="Score por etapa del método" texto="Un puntaje 0-100 en cada fase del cierre para saber exactamente dónde se cae la venta." />
            <Feature icon={ClipboardList} titulo="Técnicas que faltaron" texto="Detectamos qué wordtracks del método se usaron y cuáles se saltaron (reality check, orden de objeciones, tie-downs...)." />
            <Feature icon={MessageSquareQuote} titulo="Frases mejores, listas para usar" texto="Para cada fuga, la frase concreta que tendría que haber dicho el closer, en el estilo del método." />
            <Feature icon={CheckCircle2} titulo="Resumen ejecutivo" texto="Qué pasó en la llamada y la única cosa a trabajar antes de la próxima. Directo, sin vueltas." />
          </div>
        </div>
      </section>

      {/* Mentoría (upsell) */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="card liquid p-8 sm:p-10 ring-1 ring-iris-500/25 relative overflow-hidden">
          <div className="absolute -top-16 -right-16 w-64 h-64 bg-accent-grad opacity-10 blur-3xl rounded-full" />
          <div className="relative grid lg:grid-cols-[1.4fr_1fr] gap-8 items-center">
            <div className="flex flex-col gap-4">
              <span className="pill text-gold-400 bg-gold-400/12 self-start flex items-center gap-1.5">
                <GraduationCap size={12} /> Plataforma + Mentoría 1 a 1
              </span>
              <h2 className="font-display text-[30px] font-semibold text-txt leading-tight">
                El software te muestra el problema. La mentoría te enseña a resolverlo.
              </h2>
              <p className="text-[14.5px] text-txt-soft leading-relaxed">
                Sumá SALEMETRIQ para todo tu equipo (cada closer conecta sus llamadas y ves dónde falla el equipo entero)
                más una <span className="text-txt">mentoría de ventas</span> donde entrenamos el método llamada por llamada.
                Analizar + corregir + volver a medir.
              </p>
              <div className="flex flex-col gap-2 mt-1">
                {["Análisis ilimitado para todo el equipo", "Coaching del equipo y ranking de closers", "Generador de guiones a medida de tu oferta", "Sesiones de mentoría en vivo sobre tus llamadas reales"].map((x) => (
                  <div key={x} className="flex items-center gap-2 text-[13.5px] text-txt-soft">
                    <CheckCircle2 size={15} className="text-pos shrink-0" /> {x}
                  </div>
                ))}
              </div>
            </div>
            <div className="card p-6 flex flex-col gap-4 text-center">
              <div className="flex justify-center gap-0.5">{[...Array(5)].map((_, i) => <Star key={i} size={15} className="text-gold-400 fill-gold-400" />)}</div>
              <p className="text-[13.5px] text-txt-soft italic">"Pasamos de improvisar a tener un método. En un mes subimos el close rate 11 puntos."</p>
              <a href={AGENDA_URL} className="btn-primary flex items-center justify-center gap-2 text-[14px] py-3">
                Agendar diagnóstico <ArrowRight size={16} />
              </a>
              <span className="text-[11.5px] text-txt-mute">Cupos limitados por mes</span>
            </div>
          </div>
        </div>
      </section>

      {/* CTA final */}
      <section className="max-w-3xl mx-auto px-6 py-20 text-center">
        <h2 className="font-display text-[32px] font-semibold text-txt mb-3">Probá tu primera llamada, gratis</h2>
        <p className="text-[15px] text-txt-soft mb-8">Dejá tu email y teléfono, pegá una llamada y mirá el diagnóstico. Toma menos de un minuto.</p>
        <div className="card p-6"><LeadForm variante="cta" /></div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/[0.06]">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <SalemetriqLogo size={22} withWord />
          <span className="text-[12px] text-txt-mute">© 2026 SALEMETRIQ · Conversation Intelligence para equipos de ventas</span>
        </div>
      </footer>
    </div>
  );
}
