import { useEffect, useState } from "react";
import { UserPlus, Shield, Phone, Headphones, Check, X, Loader2 } from "lucide-react";
import api from "../utils/api";
import { getUser } from "../utils/auth";

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

export default function Usuarios() {
  const me = getUser();
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);

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
            <div className="text-right">
              {m.id !== me?.id && (
                <button onClick={() => toggleActivo(m)} className="btn-ghost text-[13px] inline-flex items-center gap-1.5">
                  {m.activo ? <><X size={14} /> Desactivar</> : <><Check size={14} /> Activar</>}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
