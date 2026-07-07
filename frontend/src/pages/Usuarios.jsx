import { useEffect, useState } from "react";
import { UserPlus, Shield, Phone, Headphones, Check, X, Loader2, Send, Copy, RefreshCw, Video, Webhook } from "lucide-react";
import api from "../utils/api";
import { getUser } from "../utils/auth";

// Link directo al bot si se configuró VITE_TELEGRAM_BOT (ej: "SalemetriqBot").
const BOT_USER = import.meta.env.VITE_TELEGRAM_BOT || "";

const ROL = {
  admin: { label: "Admin", icon: Shield, cls: "text-iris-400 bg-iris-500/12" },
  closer: { label: "Closer", icon: Phone, cls: "text-gold-400 bg-gold-400/12" },
  setter: { label: "Setter", icon: Headphones, cls: "text-cyan-400 bg-cyan-500/12" },
};

function RolPill({ rol }) {
  const r = ROL[rol] || { label: rol, icon: Shield, cls: "text-txt-mute bg-white/[0.06]" };
  const Icon = r.icon;
  return <span className={`pill ${r.cls} flex items-center gap-1`}><Icon size={11} /> {r.label}</span>;
}

const EMPTY = { email: "", nombre: "", rol: "closer", password: "" };

/* Panel para el admin: URL del webhook de Fathom del workspace. */
function FathomPanel() {
  const [open, setOpen] = useState(false);
  const [url, setUrl] = useState("");
  const [copied, setCopied] = useState(false);

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (next && !url) {
      const r = await api.get("/workspace/fathom");
      setUrl(`${window.location.origin}${r.data.webhook_path}`);
    }
  }
  function copiar() {
    navigator.clipboard?.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="card p-4">
      <button onClick={toggle} className="w-full flex items-center gap-2.5 text-left">
        <div className="w-8 h-8 rounded-lg bg-gold-400/15 text-gold-400 grid place-items-center ring-1 ring-gold-400/25 shrink-0"><Video size={16} /></div>
        <div className="flex-1 min-w-0">
          <div className="text-[14px] font-medium text-txt">Conectar Fathom</div>
          <div className="text-[12px] text-txt-mute">Las llamadas de tus closers entran solas al terminar. Configuralo una vez.</div>
        </div>
        <Webhook size={16} className="text-txt-mute shrink-0" />
      </button>

      {open && (
        <div className="mt-4 pt-4 border-t border-white/[0.06] flex flex-col gap-3">
          <ol className="text-[13px] text-txt-soft list-decimal ml-4 space-y-1.5">
            <li>En Fathom → <span className="text-txt">Settings → Integrations → Webhooks</span>, creá un webhook.</li>
            <li>Pegá esta URL (incluí <span className="text-txt">transcript</span> en el payload):</li>
          </ol>
          <div className="flex items-center gap-2">
            <code className="flex-1 text-[12px] font-mono text-txt bg-ink-raised rounded-lg px-3 py-2.5 ring-1 ring-ink-line break-all">{url || "…"}</code>
            <button onClick={copiar} disabled={!url} className="btn-ghost px-3 py-2.5 shrink-0" title="Copiar URL">
              {copied ? <Check size={16} className="text-pos" /> : <Copy size={16} />}
            </button>
          </div>
          <p className="text-[12px] text-txt-mute">
            Cada llamada se atribuye al closer cuyo email coincide con el de Fathom. Si difiere,
            seteá el override con el botón <span className="text-gold-400">Fathom</span> de cada closer.
          </p>
        </div>
      )}
    </div>
  );
}

/* Modal para setear el email de Fathom de un closer. */
function FathomModal({ member, onClose, onSaved }) {
  const [value, setValue] = useState(member.fathom_email || "");
  const [saving, setSaving] = useState(false);

  async function guardar() {
    setSaving(true);
    try {
      const r = await api.patch(`/workspace/members/${member.id}/fathom-email`, { fathom_email: value.trim() || null });
      onSaved(member.id, r.data.fathom_email);
      onClose();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/60 backdrop-blur-sm p-4" onClick={onClose}>
      <div className="card liquid w-full max-w-md p-6 flex flex-col gap-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gold-400/15 text-gold-400 grid place-items-center ring-1 ring-gold-400/25"><Video size={17} /></div>
          <div>
            <div className="font-display text-[16px] font-semibold text-txt">Email de Fathom</div>
            <div className="text-[12px] text-txt-mute">{member.nombre || member.email}</div>
          </div>
        </div>
        <p className="text-[13.5px] text-txt-soft">
          Por defecto las llamadas se atribuyen con el email de login
          (<span className="text-txt">{member.email}</span>). Si este closer graba en Fathom con
          otro email, ponelo acá. Dejalo vacío para usar el de login.
        </p>
        <input className="input" type="email" placeholder={member.email}
               value={value} onChange={(e) => setValue(e.target.value)} />
        <div className="flex items-center gap-2 justify-end">
          <button onClick={onClose} className="btn-ghost text-[13px]">Cancelar</button>
          <button onClick={guardar} disabled={saving} className="btn-primary flex items-center gap-2 text-[13px]">
            {saving ? <Loader2 size={15} className="animate-spin" /> : <Check size={15} />} Guardar
          </button>
        </div>
      </div>
    </div>
  );
}

/* Modal de vinculación de un setter con el bot de Telegram. */
function TelegramModal({ member, onClose }) {
  const [estado, setEstado] = useState(null);
  const [code, setCode] = useState(null);
  const [loading, setLoading] = useState(true);
  const [gen, setGen] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api.get(`/workspace/members/${member.id}/telegram`)
      .then((r) => { setEstado(r.data); setCode(r.data.telegram_link_code); })
      .catch(() => setEstado({ vinculado: false }))
      .finally(() => setLoading(false));
  }, [member.id]);

  async function generar() {
    setGen(true);
    try {
      const r = await api.post(`/workspace/members/${member.id}/telegram-code`);
      setCode(r.data.telegram_link_code);
      setEstado({ vinculado: false, telegram_link_code: r.data.telegram_link_code });
    } finally {
      setGen(false);
    }
  }

  function copiar() {
    navigator.clipboard?.writeText(`/link ${code}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/60 backdrop-blur-sm p-4" onClick={onClose}>
      <div className="card liquid w-full max-w-md p-6 flex flex-col gap-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-cyan-500/15 text-cyan-400 grid place-items-center ring-1 ring-cyan-500/25"><Send size={17} /></div>
          <div>
            <div className="font-display text-[16px] font-semibold text-txt">Vincular Telegram</div>
            <div className="text-[12px] text-txt-mute">{member.nombre || member.email}</div>
          </div>
        </div>

        {loading ? (
          <div className="text-[13.5px] text-txt-mute py-4">Cargando…</div>
        ) : estado?.vinculado ? (
          <div className="flex flex-col gap-3">
            <div className="pill pill-pos self-start flex items-center gap-1.5"><Check size={12} /> Ya vinculado</div>
            <p className="text-[13.5px] text-txt-soft">
              Este setter ya conectó su Telegram y puede enviar resúmenes al bot.
              Si cambió de teléfono, regenerá el código (se desvincula el anterior).
            </p>
            <button onClick={generar} disabled={gen} className="btn-ghost self-start flex items-center gap-2 text-[13px]">
              {gen ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />} Regenerar código
            </button>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <p className="text-[13.5px] text-txt-soft">
              Generá un código y pasáselo al setter. Tiene que abrir el bot y enviar
              <code className="text-cyan-400"> /link CÓDIGO</code>.
            </p>
            {code ? (
              <>
                <div className="flex items-center gap-2">
                  <code className="flex-1 text-center font-mono text-[18px] tracking-wider text-txt bg-ink-raised rounded-lg py-2.5 ring-1 ring-ink-line">{code}</code>
                  <button onClick={copiar} className="btn-ghost px-3 py-2.5" title="Copiar /link CÓDIGO">
                    {copied ? <Check size={16} className="text-pos" /> : <Copy size={16} />}
                  </button>
                </div>
                {BOT_USER && (
                  <a href={`https://t.me/${BOT_USER}?start=${code.replace(/^SMQ-/, "")}`} target="_blank" rel="noreferrer"
                     className="text-[12.5px] text-cyan-400 hover:underline">Abrir el bot en Telegram →</a>
                )}
                <button onClick={generar} disabled={gen} className="btn-ghost self-start flex items-center gap-2 text-[12.5px] text-txt-mute">
                  {gen ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />} Generar otro
                </button>
              </>
            ) : (
              <button onClick={generar} disabled={gen} className="btn-primary self-start flex items-center gap-2">
                {gen ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />} Generar código
              </button>
            )}
          </div>
        )}

        <button onClick={onClose} className="btn-ghost self-end text-[13px]">Cerrar</button>
      </div>
    </div>
  );
}

export default function Usuarios() {
  const me = getUser();
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [tgSetter, setTgSetter] = useState(null);
  const [fathomCloser, setFathomCloser] = useState(null);

  function load() {
    api.get("/workspace/members").then((r) => setMembers(r.data)).catch(() => setErr("No se pudieron cargar los usuarios.")).finally(() => setLoading(false));
  }
  useEffect(load, []);

  async function crear(e) {
    e.preventDefault();
    setSaving(true);
    setErr("");
    try {
      await api.post("/workspace/members", form);
      setForm(EMPTY);
      setShowForm(false);
      load();
    } catch (e) {
      setErr(e.response?.data?.detail || "No se pudo crear el usuario.");
    } finally {
      setSaving(false);
    }
  }

  async function toggleActivo(m) {
    try {
      await api.patch(`/workspace/members/${m.id}`, { activo: !m.activo });
      setMembers((prev) => prev.map((x) => (x.id === m.id ? { ...x, activo: !m.activo } : x)));
    } catch (e) {
      setErr(e.response?.data?.detail || "No se pudo actualizar.");
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between gap-4">
        <p className="text-[14px] text-txt-soft">
          Usuarios internos de tu workspace. Solo vos (admin) los gestionás.
        </p>
        <button onClick={() => setShowForm((s) => !s)} className="btn-primary flex items-center gap-2 text-[14px]">
          <UserPlus size={16} /> Agregar usuario
        </button>
      </div>

      {err && <div className="card p-4 text-[13.5px] text-neg">{err}</div>}

      <FathomPanel />

      {showForm && (
        <form onSubmit={crear} className="card liquid p-5 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Nombre</label>
            <input className="input mt-1.5" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} required />
          </div>
          <div>
            <label className="label">Email</label>
            <input type="email" className="input mt-1.5" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          </div>
          <div>
            <label className="label">Rol</label>
            <select className="input mt-1.5" value={form.rol} onChange={(e) => setForm({ ...form, rol: e.target.value })}>
              <option value="closer">Closer</option>
              <option value="setter">Setter</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div>
            <label className="label">Contraseña</label>
            <input type="text" className="input mt-1.5" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="mín. 6 caracteres" required />
          </div>
          <div className="md:col-span-2 flex items-center gap-2">
            <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
              {saving ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />} Crear usuario
            </button>
            <button type="button" onClick={() => { setShowForm(false); setForm(EMPTY); }} className="btn-ghost">Cancelar</button>
          </div>
        </form>
      )}

      <div className="card overflow-hidden">
        <div className="grid grid-cols-[1.4fr_1fr_auto_auto] gap-4 px-5 py-3 border-b border-white/[0.06]">
          <span className="label">Usuario</span>
          <span className="label">Rol</span>
          <span className="label">Estado</span>
          <span className="label text-right">Acción</span>
        </div>

        {loading && <div className="px-5 py-8 text-[13.5px] text-txt-mute">Cargando…</div>}
        {!loading && members.length === 0 && (
          <div className="px-5 py-10 text-center text-[13.5px] text-txt-mute">Todavía no hay usuarios. Agregá el primero.</div>
        )}

        {members.map((m) => (
          <div key={m.id} className="grid grid-cols-[1.4fr_1fr_auto_auto] gap-4 items-center px-5 py-3.5 border-b border-white/[0.05] last:border-0">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-8 h-8 rounded-full bg-iris-500/20 text-iris-400 grid place-items-center text-[12px] font-semibold shrink-0 ring-1 ring-iris-500/30">
                {(m.nombre || m.email || "?").slice(0, 1).toUpperCase()}
              </div>
              <div className="min-w-0">
                <div className="text-[14px] text-txt truncate">
                  {m.nombre || m.email} {m.id === me?.id && <span className="text-[11px] text-txt-mute">(vos)</span>}
                </div>
                <div className="text-[12px] text-txt-mute truncate">{m.email}</div>
              </div>
            </div>
            <div><RolPill rol={m.rol} /></div>
            <div>
              {m.activo
                ? <span className="pill pill-pos">Activo</span>
                : <span className="pill text-txt-mute bg-white/[0.06]">Inactivo</span>}
            </div>
            <div className="text-right flex items-center justify-end gap-1.5">
              {m.rol === "setter" && (
                <button onClick={() => setTgSetter(m)} className="btn-ghost text-[13px] inline-flex items-center gap-1.5" title="Vincular con Telegram">
                  <Send size={14} /> Telegram
                </button>
              )}
              {m.rol === "closer" && (
                <button onClick={() => setFathomCloser(m)} className="btn-ghost text-[13px] inline-flex items-center gap-1.5" title="Email de Fathom">
                  <Video size={14} /> Fathom
                </button>
              )}
              {m.id !== me?.id && (
                <button onClick={() => toggleActivo(m)} className="btn-ghost text-[13px] inline-flex items-center gap-1.5">
                  {m.activo ? <><X size={14} /> Desactivar</> : <><Check size={14} /> Activar</>}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {tgSetter && <TelegramModal member={tgSetter} onClose={() => setTgSetter(null)} />}
      {fathomCloser && (
        <FathomModal
          member={fathomCloser}
          onClose={() => setFathomCloser(null)}
          onSaved={(id, val) => setMembers((prev) => prev.map((x) => (x.id === id ? { ...x, fathom_email: val } : x)))}
        />
      )}
    </div>
  );
}
