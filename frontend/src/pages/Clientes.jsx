import { useEffect, useState } from "react";
import { Building2, Plus, Check, Loader2, Shield, Phone, Headphones, Copy } from "lucide-react";
import api from "../utils/api";

const EMPTY = { nombre: "", plan: "standard", admin_email: "", admin_nombre: "", admin_password: "" };

export default function Clientes() {
  const [ws, setWs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [creado, setCreado] = useState(null);

  function load() {
    api.get("/admin/workspaces").then((r) => setWs(r.data)).catch(() => setErr("No se pudieron cargar los clientes.")).finally(() => setLoading(false));
  }
  useEffect(load, []);

  async function crear(e) {
    e.preventDefault();
    setSaving(true);
    setErr("");
    try {
      const { data } = await api.post("/admin/workspaces", form);
      setCreado({ ...data.admin, workspace: data.workspace.nombre, password: form.admin_password });
      setForm(EMPTY);
      setShowForm(false);
      load();
    } catch (e) {
      setErr(e.response?.data?.detail || "No se pudo crear el cliente.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between gap-4">
        <p className="text-[14px] text-txt-soft">Clientes de la plataforma. Cada uno tiene su propio workspace aislado.</p>
        <button onClick={() => { setShowForm((s) => !s); setCreado(null); }} className="btn-primary flex items-center gap-2 text-[14px]">
          <Plus size={16} /> Nuevo cliente
        </button>
      </div>

      {err && <div className="card p-4 text-[13.5px] text-neg">{err}</div>}

      {creado && (
        <div className="card liquid p-5 ring-1 ring-pos/30">
          <div className="text-[11px] font-semibold uppercase tracking-[0.12em] text-pos mb-2">Cliente creado ✓</div>
          <p className="text-[13.5px] text-txt-soft">
            Workspace <span className="text-txt font-medium">{creado.workspace}</span>. Pasale estas credenciales al cliente:
          </p>
          <div className="mt-3 bg-ink-raised rounded-xl p-3 font-mono text-[13px] text-txt flex items-center justify-between gap-3">
            <span>{creado.email} · {creado.password}</span>
            <button onClick={() => navigator.clipboard?.writeText(`${creado.email} / ${creado.password}`)} className="icon-btn" title="Copiar"><Copy size={15} /></button>
          </div>
        </div>
      )}

      {showForm && (
        <form onSubmit={crear} className="card liquid p-5 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Nombre del cliente / workspace</label>
            <input className="input mt-1.5" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} required />
          </div>
          <div>
            <label className="label">Plan</label>
            <select className="input mt-1.5" value={form.plan} onChange={(e) => setForm({ ...form, plan: e.target.value })}>
              <option value="standard">Standard</option>
              <option value="pro">Pro</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>
          <div>
            <label className="label">Nombre del admin</label>
            <input className="input mt-1.5" value={form.admin_nombre} onChange={(e) => setForm({ ...form, admin_nombre: e.target.value })} required />
          </div>
          <div>
            <label className="label">Email del admin</label>
            <input type="email" className="input mt-1.5" value={form.admin_email} onChange={(e) => setForm({ ...form, admin_email: e.target.value })} required />
          </div>
          <div className="md:col-span-2">
            <label className="label">Contraseña inicial del admin</label>
            <input type="text" className="input mt-1.5" value={form.admin_password} onChange={(e) => setForm({ ...form, admin_password: e.target.value })} placeholder="mín. 6 caracteres" required />
          </div>
          <div className="md:col-span-2 flex items-center gap-2">
            <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
              {saving ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />} Crear cliente
            </button>
            <button type="button" onClick={() => { setShowForm(false); setForm(EMPTY); }} className="btn-ghost">Cancelar</button>
          </div>
        </form>
      )}

      {loading && <div className="card p-8 text-[13.5px] text-txt-mute">Cargando…</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {ws.map((w) => (
          <div key={w.id} className="card p-5 flex flex-col gap-3">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-9 h-9 rounded-xl bg-iris-500/20 text-iris-400 grid place-items-center shrink-0 ring-1 ring-iris-500/30">
                  <Building2 size={17} />
                </div>
                <div className="min-w-0">
                  <div className="font-display text-[15px] font-semibold text-txt truncate">{w.nombre}</div>
                  <div className="text-[12px] text-txt-mute truncate">{w.owner_email || "sin dueño"}</div>
                </div>
              </div>
              {w.is_demo
                ? <span className="pill text-cyan-400 bg-cyan-500/12">demo</span>
                : <span className="pill text-txt-soft bg-white/[0.06]">{w.plan}</span>}
            </div>
            <div className="flex items-center gap-4 text-[13px] text-txt-soft border-t border-white/[0.05] pt-3">
              <span className="flex items-center gap-1"><Shield size={13} className="text-iris-400" /> {w.counts.admin}</span>
              <span className="flex items-center gap-1"><Phone size={13} className="text-gold-400" /> {w.counts.closer}</span>
              <span className="flex items-center gap-1"><Headphones size={13} className="text-cyan-400" /> {w.counts.setter}</span>
              <span className="ml-auto text-txt-mute">{w.total_miembros} usuarios</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
