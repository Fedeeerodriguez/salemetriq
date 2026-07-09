import { useEffect, useState } from "react";
import { FileText, Sparkles, Wand2, Loader2, Copy, Check, ShieldQuestion, ListChecks } from "lucide-react";
import api from "../utils/api";

/*
 * Script Generator — genera guiones de venta a medida del método de closing.
 * Elegís tipo + contexto → el backend (/api/scripts/generar) devuelve un guion
 * estructurado anclado al mismo método que usa el analista.
 */

// Fallback de tipos por si /tipos no responde (mismos values que el backend).
const TIPOS_FALLBACK = [
  { value: "llamada_completa", descripcion: "Llamada de cierre completa" },
  { value: "cualificacion", descripcion: "Descubrimiento / cualificación" },
  { value: "visualizacion", descripcion: "Visualización (deseo)" },
  { value: "consecuencia", descripcion: "Consecuencia / miedo" },
  { value: "pitch", descripcion: "Pitch de la oferta" },
  { value: "objeciones", descripcion: "Manejo de objeciones" },
  { value: "objecion_precio", descripcion: "Objeción de precio" },
  { value: "cierre_urgencia", descripcion: "Cierre por urgencia" },
  { value: "apertura_frio", descripcion: "Apertura en frío" },
  { value: "no_show", descripcion: "Recuperación de no-show" },
];

// Etiqueta corta y linda para el chip.
const LABEL = {
  llamada_completa: "Llamada completa", cualificacion: "Cualificación", visualizacion: "Visualización",
  consecuencia: "Consecuencia / miedo", pitch: "Pitch", objeciones: "Objeciones",
  objecion_precio: "Objeción de precio", cierre_urgencia: "Cierre por urgencia",
  apertura_frio: "Apertura en frío", no_show: "No-show",
};

function CopyBtn({ text, className = "" }) {
  const [ok, setOk] = useState(false);
  return (
    <button
      onClick={() => { navigator.clipboard?.writeText(text); setOk(true); setTimeout(() => setOk(false), 1400); }}
      className={`btn-ghost px-2 py-1 ${className}`}
      title="Copiar"
    >
      {ok ? <Check size={14} className="text-pos" /> : <Copy size={14} />}
    </button>
  );
}

// Aplana el guion a texto plano para "copiar todo".
function scriptATexto(s) {
  const out = [s.titulo, s.objetivo ? `Objetivo: ${s.objetivo}` : "", ""];
  (s.secciones || []).forEach((sec) => {
    out.push(`## ${sec.etapa}${sec.objetivo ? ` — ${sec.objetivo}` : ""}`);
    (sec.lineas || []).forEach((l) => out.push(`• ${l}`));
    (sec.tips || []).forEach((t) => out.push(`  ↳ ${t}`));
    out.push("");
  });
  if (s.objeciones?.length) {
    out.push("## Objeciones");
    s.objeciones.forEach((o) => out.push(`• [${o.tipo || "obj"}] ${o.objecion}\n  → ${o.respuesta}`));
    out.push("");
  }
  if (s.checklist?.length) out.push(`Checklist: ${s.checklist.join(" · ")}`);
  if (s.notas) out.push(`\nNotas: ${s.notas}`);
  return out.filter((l) => l !== undefined).join("\n");
}

export default function ScriptGenerator() {
  const [tipos, setTipos] = useState(TIPOS_FALLBACK);
  const [tipo, setTipo] = useState("llamada_completa");
  const [contexto, setContexto] = useState("");
  const [busy, setBusy] = useState(false);
  const [script, setScript] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get("/scripts/tipos").then((r) => { if (r.data?.length) setTipos(r.data); }).catch(() => {});
  }, []);

  async function generar() {
    setErr(""); setBusy(true); setScript(null);
    try {
      const r = await api.post("/scripts/generar", { tipo, contexto: contexto.trim() || null });
      setScript(r.data);
    } catch (e) {
      setErr(e.response?.data?.detail || "No se pudo generar el script.");
    } finally { setBusy(false); }
  }

  return (
    <div className="flex flex-col gap-5">
      <p className="text-[14px] text-txt-soft">
        Generá guiones a medida, anclados al mismo método que usa el analista. Elegí el tipo, agregá el
        contexto de tu oferta y prospecto, y generá.
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-5">
        {/* Formulario */}
        <div className="card p-5 flex flex-col gap-4 self-start">
          <div>
            <label className="label">Tipo de script</label>
            <div className="flex flex-wrap gap-2 mt-2">
              {tipos.map((t) => (
                <button
                  key={t.value}
                  onClick={() => setTipo(t.value)}
                  title={t.descripcion}
                  className={`text-[12.5px] px-3 py-1.5 rounded-full border transition-colors ${
                    tipo === t.value
                      ? "border-iris-500/60 text-iris-300 bg-iris-500/10"
                      : "border-ink-line text-txt-soft hover:text-iris-400 hover:border-iris-500/40"
                  }`}
                >
                  {LABEL[t.value] || t.descripcion}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="label">Contexto (opcional)</label>
            <textarea
              className="input mt-2 h-36 resize-none"
              placeholder="Ej: SaaS de $2.500/mes para dueños de agencia. Outcome: escalar a $50k/mes sin trabajar más horas. Objeción típica: precio y falta de tiempo."
              value={contexto}
              onChange={(e) => setContexto(e.target.value)}
            />
            <p className="text-[11.5px] text-txt-mute mt-1.5">
              Cuanto más contexto (oferta, precio, dolor, outcome), más a medida sale el guion. Sin contexto usa placeholders [ASÍ].
            </p>
          </div>
          {err && <div className="text-[12.5px] text-neg">{err}</div>}
          <button onClick={generar} disabled={busy} className="btn-primary flex items-center justify-center gap-2 text-[14px]">
            {busy ? <Loader2 size={16} className="animate-spin" /> : <Wand2 size={16} />}
            {busy ? "Generando…" : "Generar script"}
          </button>
        </div>

        {/* Salida */}
        <div className="card p-6 min-h-[400px]">
          <div className="flex items-center gap-2 mb-5">
            <Sparkles size={16} className="text-iris-400" />
            <span className="text-[13px] font-semibold uppercase tracking-[0.12em] text-accent">Script generado</span>
            {script && <CopyBtn text={scriptATexto(script)} className="ml-auto !px-3 text-[12.5px] flex items-center gap-1.5" />}
          </div>

          {busy ? (
            <div className="flex flex-col items-center justify-center text-center py-24">
              <Loader2 size={26} className="text-iris-400 animate-spin mb-3" />
              <p className="text-[13.5px] text-txt-mute">Armando el guion contra el método…</p>
            </div>
          ) : !script ? (
            <div className="flex flex-col items-center justify-center text-center py-24 px-6">
              <div className="w-12 h-12 rounded-xl bg-ink-raised grid place-items-center mb-4">
                <FileText size={22} className="text-txt-mute" />
              </div>
              <p className="text-txt font-medium">Tu guion va a aparecer acá</p>
              <p className="text-[13.5px] text-txt-mute mt-1 max-w-sm">
                Elegí un tipo, agregá el contexto y generá. El guion sale con las frases listas para leer,
                los pasos del método y las objeciones.
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-5">
              {/* Encabezado del guion */}
              <div>
                <h2 className="font-display text-[20px] font-semibold text-txt">{script.titulo}</h2>
                {script.objetivo && <p className="text-[13.5px] text-txt-soft mt-1">{script.objetivo}</p>}
              </div>

              {/* Secciones */}
              <div className="flex flex-col gap-4">
                {(script.secciones || []).map((sec, i) => (
                  <div key={i} className="border-l-2 border-iris-500/30 pl-4">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-iris-500/15 text-iris-300 grid place-items-center text-[11px] font-semibold shrink-0">{i + 1}</span>
                      <h3 className="font-display text-[15px] font-semibold text-txt">{sec.etapa}</h3>
                    </div>
                    {sec.objetivo && <p className="text-[12.5px] text-txt-mute mt-1 ml-7">{sec.objetivo}</p>}
                    <div className="flex flex-col gap-2 mt-2.5 ml-7">
                      {(sec.lineas || []).map((l, j) => (
                        <div key={j} className="group flex items-start gap-2 bg-ink-raised rounded-lg px-3 py-2">
                          <p className="text-[13.5px] text-txt leading-relaxed flex-1">{l}</p>
                          <CopyBtn text={l} className="opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                        </div>
                      ))}
                    </div>
                    {sec.tips?.length > 0 && (
                      <ul className="mt-2 ml-7 flex flex-col gap-1">
                        {sec.tips.map((t, k) => (
                          <li key={k} className="text-[12px] text-txt-mute flex gap-1.5"><span className="text-iris-400">↳</span> {t}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>

              {/* Objeciones */}
              {script.objeciones?.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-2.5">
                    <ShieldQuestion size={15} className="text-gold-400" />
                    <span className="label">Objeciones y respuestas</span>
                  </div>
                  <div className="flex flex-col gap-2">
                    {script.objeciones.map((o, i) => (
                      <div key={i} className="bg-ink-raised rounded-lg px-3 py-2.5">
                        <div className="flex items-center gap-2">
                          {o.tipo && <span className="pill text-gold-400 bg-gold-400/12 text-[11px]">{o.tipo}</span>}
                          <span className="text-[13px] font-medium text-txt">{o.objecion}</span>
                        </div>
                        <p className="text-[13px] text-txt-soft mt-1.5">→ {o.respuesta}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Checklist */}
              {script.checklist?.length > 0 && (
                <div className="flex items-center gap-2 flex-wrap">
                  <ListChecks size={15} className="text-pos" />
                  {script.checklist.map((c, i) => (
                    <span key={i} className="pill pill-pos text-[11.5px]">{c}</span>
                  ))}
                </div>
              )}

              {/* Notas */}
              {script.notas && (
                <p className="text-[12.5px] text-txt-mute border-t border-white/[0.06] pt-3">{script.notas}</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
