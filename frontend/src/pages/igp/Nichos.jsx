import { useEffect, useState } from "react";
import { Plus, Trash2, Target, Sparkles } from "lucide-react";
import api from "../../utils/api";

const VACIO = { nombre: "", descripcion: "", keywords: "", hashtags: "", cuentas_semilla: "", usa_ia: false };

function toArr(s) {
  return (s || "").split(",").map((x) => x.trim()).filter(Boolean);
}

export default function Nichos() {
  const [nichos, setNichos] = useState([]);
  const [form, setForm] = useState(VACIO);
  const [loading, setLoading] = useState(false);

  async function cargar() {
    const { data } = await api.get("/igp/nichos");
    setNichos(data);
  }
  useEffect(() => { cargar(); }, []);

  async function crear(e) {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/igp/nichos", {
        nombre: form.nombre,
        descripcion: form.descripcion || null,
        keywords: toArr(form.keywords),
        hashtags: toArr(form.hashtags),
        cuentas_semilla: toArr(form.cuentas_semilla),
        usa_ia: form.usa_ia,
      });
      setForm(VACIO);
      cargar();
    } finally {
      setLoading(false);
    }
  }

  async function eliminar(id) {
    if (!confirm("¿Eliminar este nicho?")) return;
    await api.delete(`/igp/nichos/${id}`);
    cargar();
  }

  return (
    <div className="max-w-5xl">
      <p className="text-txt-soft text-sm mb-6">
        Un <b className="text-txt">nicho</b> define qué buscás: sus <b>keywords</b> (esperadas en la bio),
        <b> hashtags</b> y <b>cuentas semilla</b> (para buscar entre sus seguidores). Orienta la búsqueda y el
        puntaje de afinidad.
      </p>

      <div className="grid lg:grid-cols-[380px_1fr] gap-6">
        {/* Form */}
        <form onSubmit={crear} className="card p-5 flex flex-col gap-3 h-fit">
          <div className="flex items-center gap-2 mb-1">
            <Target size={18} className="text-iris-400" />
            <h2 className="font-display text-[16px] font-semibold">Nuevo nicho</h2>
          </div>
          <div>
            <label className="label">Nombre</label>
            <input className="input mt-1.5" placeholder="Médicos" required
              value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
          </div>
          <div>
            <label className="label">Descripción</label>
            <input className="input mt-1.5" placeholder="Profesionales de la salud"
              value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} />
          </div>
          <div>
            <label className="label">Keywords (coma)</label>
            <input className="input mt-1.5" placeholder="medico, dr, clínica, MP, MN, cardiólogo"
              value={form.keywords} onChange={(e) => setForm({ ...form, keywords: e.target.value })} />
          </div>
          <div>
            <label className="label">Hashtags (coma, sin #)</label>
            <input className="input mt-1.5" placeholder="medicos, medicina, cardiologia"
              value={form.hashtags} onChange={(e) => setForm({ ...form, hashtags: e.target.value })} />
          </div>
          <div>
            <label className="label">Cuentas semilla (coma, @)</label>
            <input className="input mt-1.5" placeholder="sociedadcardiologia, undec"
              value={form.cuentas_semilla} onChange={(e) => setForm({ ...form, cuentas_semilla: e.target.value })} />
          </div>
          <label className="flex items-center gap-2 text-[13px] text-txt-soft cursor-pointer">
            <input type="checkbox" checked={form.usa_ia}
              onChange={(e) => setForm({ ...form, usa_ia: e.target.checked })} />
            <Sparkles size={14} className="text-cyan-400" /> Usar clasificador IA
          </label>
          <button className="btn-primary mt-1 flex items-center justify-center gap-2" disabled={loading}>
            <Plus size={16} /> {loading ? "Guardando…" : "Crear nicho"}
          </button>
        </form>

        {/* Lista */}
        <div className="flex flex-col gap-3">
          {nichos.length === 0 && <div className="card p-6 text-txt-mute text-sm">Todavía no hay nichos. Creá el primero.</div>}
          {nichos.map((n) => (
            <div key={n.id} className="card p-4 flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="font-display font-semibold text-txt">{n.nombre}</h3>
                  {n.usa_ia && <span className="pill text-cyan-400 bg-cyan-500/10">IA</span>}
                </div>
                {n.descripcion && <p className="text-[13px] text-txt-soft mt-0.5">{n.descripcion}</p>}
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {(n.hashtags || []).map((h) => <span key={h} className="pill bg-iris-500/10 text-iris-300">#{h}</span>)}
                  {(n.keywords || []).slice(0, 6).map((k) => <span key={k} className="pill bg-ink-raised text-txt-soft">{k}</span>)}
                </div>
              </div>
              <button onClick={() => eliminar(n.id)} className="icon-btn text-txt-mute hover:text-neg shrink-0">
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
