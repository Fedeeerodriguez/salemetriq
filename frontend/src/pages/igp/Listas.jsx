import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Trash2, ListChecks, ChevronRight } from "lucide-react";
import api from "../../utils/api";

export default function Listas() {
  const [listas, setListas] = useState([]);
  const [nombre, setNombre] = useState("");

  async function cargar() {
    const { data } = await api.get("/igp/listas");
    setListas(data);
  }
  useEffect(() => { cargar(); }, []);

  async function crear(e) {
    e.preventDefault();
    if (!nombre.trim()) return;
    await api.post("/igp/listas", { nombre });
    setNombre("");
    cargar();
  }

  async function eliminar(id) {
    if (!confirm("¿Eliminar esta lista? (no borra los perfiles)")) return;
    await api.delete(`/igp/listas/${id}`);
    cargar();
  }

  return (
    <div className="max-w-3xl">
      <form onSubmit={crear} className="card p-4 mb-5 flex items-end gap-3">
        <div className="flex-1">
          <label className="label">Nueva lista</label>
          <input className="input mt-1.5" placeholder="Médicos Santa Rosa" value={nombre}
            onChange={(e) => setNombre(e.target.value)} />
        </div>
        <button className="btn-primary flex items-center gap-2"><Plus size={16} /> Crear</button>
      </form>

      <div className="flex flex-col gap-3">
        {listas.length === 0 && <div className="card p-6 text-txt-mute text-sm">No hay listas todavía.</div>}
        {listas.map((l) => (
          <div key={l.id} className="card p-4 flex items-center justify-between gap-3">
            <Link to={`/prospeccion/listas/${l.id}`} className="flex items-center gap-3 min-w-0 flex-1 group">
              <span className="w-9 h-9 rounded-lg bg-iris-500/15 text-iris-400 grid place-items-center shrink-0">
                <ListChecks size={18} />
              </span>
              <div className="min-w-0">
                <div className="font-medium text-txt group-hover:text-accent transition-colors">{l.nombre}</div>
                <div className="text-[12.5px] text-txt-mute">{l.total} perfil(es)</div>
              </div>
            </Link>
            <div className="flex items-center gap-1">
              <button onClick={() => eliminar(l.id)} className="icon-btn text-txt-mute hover:text-neg"><Trash2 size={16} /></button>
              <Link to={`/prospeccion/listas/${l.id}`} className="icon-btn"><ChevronRight size={18} /></Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
