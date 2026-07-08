import { useEffect, useState } from "react";
import { Send, Video, Check, Copy, Loader2, X, ExternalLink, Plug } from "lucide-react";
import api from "../utils/api";
import { getUser } from "../utils/auth";

const BOT_USER = import.meta.env.VITE_TELEGRAM_BOT || "";

function Card({ icon: Icon, tint, ring, title, subtitle, children }) {
  return (
    <div className="card p-5 flex flex-col gap-4">
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-xl grid place-items-center ring-1 ${tint} ${ring}`}><Icon size={19} /></div>
        <div className="min-w-0">
          <div className="font-display text-[16px] font-semibold text-txt">{title}</div>
          <div className="text-[12.5px] text-txt-mute">{subtitle}</div>
        </div>
      </div>
      {children}
    </div>
  );
}

/* ── Telegram (setters) ── */
function TelegramCard({ estado, reload }) {
  const [code, setCode] = useState(estado.codigo);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);

  async function generar() {
    setBusy(true);
    try {
      const r = await api.post("/conexiones/telegram/code");
      setCode(r.data.codigo);
    } finally { setBusy(false); }
  }
  async function desvincular() {
    setBusy(true);
    try { await api.delete("/conexiones/telegram"); setCode(null); reload(); }
    finally { setBusy(false); }
  }
  function copiar() {
    navigator.clipboard?.writeText(`/link ${code}`);
    setCopied(true); setTimeout(() => setCopied(false), 1500);
  }

  return (
    <Card icon={Send} tint="bg-cyan-500/15 text-cyan-400" ring="ring-cyan-500/25"
          title="Telegram" subtitle="Mandá tus resúmenes de setting al bot.">
      {estado.vinculado ? (
        <div className="flex items-center justify-between gap-3">
          <span className="pill pill-pos flex items-center gap-1.5"><Check size={12} /> Vinculado</span>
          <button onClick={desvincular} disabled={busy} className="btn-ghost text-[13px] flex items-center gap-1.5">
            {busy ? <Loader2 size={14} className="animate-spin" /> : <X size={14} />} Desvincular
          </button>
        </div>
      ) : code ? (
        <div className="flex flex-col gap-3">
          <p className="text-[13px] text-txt-soft">Abrí el bot y enviá <code className="text-cyan-400">/link {code}</code>:</p>
          <div className="flex items-center gap-2">
            <code className="flex-1 text-center font-mono text-[17px] tracking-wider text-txt bg-ink-raised rounded-lg py-2.5 ring-1 ring-ink-line">{code}</code>
            <button onClick={copiar} className="btn-ghost px-3 py-2.5" title="Copiar /link código">
              {copied ? <Check size={16} className="text-pos" /> : <Copy size={16} />}
            </button>
          </div>
          {BOT_USER && (
            <a href={`https://t.me/${BOT_USER}`} target="_blank" rel="noreferrer" className="text-[12.5px] text-cyan-400 hover:underline flex items-center gap-1">
              Abrir @{BOT_USER} <ExternalLink size={12} />
            </a>
          )}
        </div>
      ) : (
        <button onClick={generar} disabled={busy} className="btn-primary self-start flex items-center gap-2">
          {busy ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />} Generar código
        </button>
      )}
    </Card>
  );
}

/* ── Fathom (closers) ── */
function FathomCard({ estado, reload }) {
  const [apiKey, setApiKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function conectar() {
    setError(""); setBusy(true);
    try {
      await api.post("/conexiones/fathom", { api_key: apiKey.trim() });
      setApiKey(""); reload();
    } catch (e) {
      setError(e.response?.data?.detail || "No se pudo conectar Fathom.");
    } finally { setBusy(false); }
  }
  async function desconectar() {
    setBusy(true);
    try { await api.delete("/conexiones/fathom"); reload(); }
    finally { setBusy(false); }
  }

  return (
    <Card icon={Video} tint="bg-gold-400/15 text-gold-400" ring="ring-gold-400/25"
          title="Fathom" subtitle="Tus llamadas entran solas al terminar.">
      {estado.conectado ? (
        <div className="flex items-center justify-between gap-3">
          <span className="pill pill-pos flex items-center gap-1.5"><Check size={12} /> Conectado</span>
          <button onClick={desconectar} disabled={busy} className="btn-ghost text-[13px] flex items-center gap-1.5">
            {busy ? <Loader2 size={14} className="animate-spin" /> : <X size={14} />} Desconectar
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          <p className="text-[13px] text-txt-soft">
            Pegá tu <span className="text-txt">API key de Fathom</span> (Fathom → Settings → Integrations → API):
          </p>
          <input className="input font-mono text-[13px]" type="password" placeholder="fathom_..."
                 value={apiKey} onChange={(e) => setApiKey(e.target.value)} />
          {error && <div className="text-[12.5px] text-neg">{error}</div>}
          <button onClick={conectar} disabled={busy || !apiKey.trim()} className="btn-primary self-start flex items-center gap-2">
            {busy ? <Loader2 size={16} className="animate-spin" /> : <Plug size={16} />} Conectar Fathom
          </button>
          <a href="https://developers.fathom.ai" target="_blank" rel="noreferrer" className="text-[12px] text-txt-mute hover:text-txt flex items-center gap-1">
            ¿Dónde consigo mi API key? <ExternalLink size={11} />
          </a>
        </div>
      )}
    </Card>
  );
}

export default function Conexiones() {
  const me = getUser();
  const [estado, setEstado] = useState(null);
  const [err, setErr] = useState("");

  function load() {
    api.get("/conexiones").then((r) => setEstado(r.data)).catch(() => setErr("No se pudieron cargar tus conexiones."));
  }
  useEffect(load, []);

  if (err) return <div className="card p-5 text-[14px] text-neg">{err}</div>;
  if (!estado) return <div className="card p-5 text-[14px] text-txt-mute">Cargando conexiones…</div>;

  // Mostrar la tarjeta según el rol, pero permitir ambas si el rol no encaja claro.
  const rol = estado.rol || me?.rol;
  const verTelegram = rol === "setter" || rol === "admin";
  const verFathom = rol === "closer" || rol === "admin";

  return (
    <div className="flex flex-col gap-5">
      <p className="text-[14px] text-txt-soft">
        Conectá tus herramientas. Cada uno gestiona las suyas — nadie más ve tus credenciales.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {verTelegram && <TelegramCard estado={estado.telegram} reload={load} />}
        {verFathom && <FathomCard estado={estado.fathom} reload={load} />}
        {!verTelegram && !verFathom && (
          <div className="card p-5 text-[13.5px] text-txt-mute">Tu rol no tiene integraciones para conectar.</div>
        )}
      </div>
    </div>
  );
}
