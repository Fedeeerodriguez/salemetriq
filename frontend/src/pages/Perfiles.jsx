import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { ExternalLink, Mail, Globe, Plus, RefreshCw } from "lucide-react";
import api from "../utils/api";

function fmt(n) {
  if (n == null) return "—";
  if (n >= 1000) return (n / 1000).toFixed(1).replace(".0", "") + "k";
  return String(n);
}
function scoreColor(s) {
  if (s >= 70) return "text-pos bg-pos/10";
  if (s >= 40) return "text-gold-400 bg-gold-500/10";
  return "text-txt-mute bg-ink-raised";
}
const IA = {
  si: { label: "IA: sí", cls: "text-pos bg-pos/10" },
  dudoso: { label: "IA: dudoso", cls: "text-gold-400 bg-gold-500/10" },
  no: { label: "IA: no", cls: "text-neg bg-neg/10" },
};

export default function Perfiles() {
  const [sp] = useSearchParams();
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [sel, setSel] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const [nichos, setNichos] = useState([]);
  const [listas, setListas] = useState([]);
  const [listaSel, setListaSel] = useState("");
  const [f, setF] = useState({
    nicho_id: sp.get("nicho") || "", buscar: "", min_followers: "", max_followers: "",
    solo_business: false, con_contacto: false, min_score: "", orden: "score",
  });

  async function cargar() {
    setLoading(true);
    try {
      const params = { orden: f.orden, limit: 200 };
      if (f.nicho_id) params.nicho_id = f.nicho_id;
      if (f.buscar) params.buscar = f.buscar;
      if (f.min_followers) params.min_followers = f.min_followers;
      if (f.max_followers) params.max_followers = f.max_followers;
      if (f.min_score) params.min_score = f.min_score;
      if (f.solo_business) params.solo_business = true;
      if (f.con_contacto) params.con_contacto = true;
      const { data } = await api.get("/perfiles", { params });
      setItems(data.items); setTotal(data.total); setSel(new Set());
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    api.get("/nichos").then(({ data }) => setNichos(data)).catch(() => {});
    api.get("/listas").then(({ data }) => setListas(data)).catch(() => {});
    cargar();
  }, []); // eslint-disable-line

  function toggle(u) {
    setSel((prev) => {
      const n = new Set(prev);
      n.has(u) ? n.delete(u) : n.add(u);
      return n;
    });
  }
  function toggleAll() {
    setSel((prev) => prev.size === items.length ? new Set() : new Set(items.map((x) => x.username)));
  }

  async function agregarALista() {
    if (!listaSel || sel.size === 0) return;
    await api.post(`/listas/${listaSel}/perfiles`, { usernames: [...sel] });
    alert(`${sel.size} perfil(es) agregados a la lista.`);
    setSel(new Set());
  }

  return (
    <div>
      {/* Filtros */}
      <div className="card p-4 mb-4 flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-[160px]">
          <label className="label">Buscar</label>
          <input className="input mt-1.5" placeholder="username, nombre o bio"
            value={f.buscar} onChange={(e) => setF({ ...f, buscar: e.target.value })}
            onKeyDown={(e) => e.key === "Enter" && cargar()} />
        </div>
        <div className="min-w-[150px]">
          <label className="label">Nicho</label>
          <select className="input mt-1.5" value={f.nicho_id} onChange={(e) => setF({ ...f, nicho_id: e.target.value })}>
            <option value="">Todos</option>
            {nichos.map((n) => <option key={n.id} value={n.id}>{n.nombre}</option>)}
          </select>
        </div>
        <div className="w-[110px]">
          <label className="label">Score mín</label>
          <input type="number" className="input mt-1.5" value={f.min_score}
            onChange={(e) => setF({ ...f, min_score: e.target.value })} />
        </div>
        <div className="min-w-[130px]">
          <label className="label">Orden</label>
          <select className="input mt-1.5" value={f.orden} onChange={(e) => setF({ ...f, orden: e.target.value })}>
            <option value="score">Score</option>
            <option value="followers">Seguidores</option>
            <option value="recientes">Recientes</option>
          </select>
        </div>
        <label className="flex items-center gap-2 text-[13px] text-txt-soft cursor-pointer pb-2.5">
          <input type="checkbox" checked={f.con_contacto} onChange={(e) => setF({ ...f, con_contacto: e.target.checked })} /> Con contacto
        </label>
        <button onClick={cargar} className="btn-primary flex items-center gap-2" disabled={loading}>
          <RefreshCw size={15} className={loading ? "animate-spin" : ""} /> Aplicar
        </button>
      </div>

      {/* Barra de acción de selección */}
      {sel.size > 0 && (
        <div className="card p-3 mb-3 flex flex-wrap items-center gap-3 border-iris-500/40">
          <span className="text-[13px] text-txt">{sel.size} seleccionado(s)</span>
          <select className="input max-w-[220px] py-2" value={listaSel} onChange={(e) => setListaSel(e.target.value)}>
            <option value="">Elegí una lista…</option>
            {listas.map((l) => <option key={l.id} value={l.id}>{l.nombre}</option>)}
          </select>
          <button onClick={agregarALista} className="btn-primary flex items-center gap-2 py-2" disabled={!listaSel}>
            <Plus size={15} /> Agregar a lista
          </button>
        </div>
      )}

      {/* Tabla */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-[13.5px]">
            <thead>
              <tr className="text-txt-mute text-left border-b border-ink-line">
                <th className="p-3 w-8"><input type="checkbox" checked={sel.size === items.length && items.length > 0} onChange={toggleAll} /></th>
                <th className="p-3">Perfil</th>
                <th className="p-3 text-right">Seguidores</th>
                <th className="p-3 text-center">Score</th>
                <th className="p-3">Contacto</th>
                <th className="p-3"></th>
              </tr>
            </thead>
            <tbody>
              {items.map((p) => (
                <tr key={p.username} className="border-b border-white/[0.04] hover:bg-ink-hover/50">
                  <td className="p-3"><input type="checkbox" checked={sel.has(p.username)} onChange={() => toggle(p.username)} /></td>
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-txt">@{p.username}</span>
                      {p.ia_veredicto && IA[p.ia_veredicto] && (
                        <span className={`pill ${IA[p.ia_veredicto].cls}`} title={p.ia_motivo || ""}>{IA[p.ia_veredicto].label}</span>
                      )}
                    </div>
                    <div className="text-txt-mute text-[12px] truncate max-w-[280px]">{p.full_name || p.bio || "—"}</div>
                  </td>
                  <td className="p-3 text-right tnum text-txt-soft">{fmt(p.followers)}</td>
                  <td className="p-3 text-center">
                    <span className={`pill justify-center ${scoreColor(p.score_nicho)}`}>{p.score_nicho}</span>
                  </td>
                  <td className="p-3">
                    <div className="flex items-center gap-2 text-txt-mute">
                      {p.email_publico && <Mail size={14} className="text-cyan-400" title={p.email_publico} />}
                      {p.external_url && <Globe size={14} className="text-cyan-400" title={p.external_url} />}
                      {!p.email_publico && !p.external_url && "—"}
                    </div>
                  </td>
                  <td className="p-3">
                    <a href={p.ig_url || `https://www.instagram.com/${p.username}/`} target="_blank" rel="noreferrer"
                      className="icon-btn inline-grid"><ExternalLink size={15} /></a>
                  </td>
                </tr>
              ))}
              {items.length === 0 && !loading && (
                <tr><td colSpan={6} className="p-8 text-center text-txt-mute">Sin perfiles. Lanzá una búsqueda desde <b>Buscar</b>.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      <div className="text-[12px] text-txt-mute mt-2">{total} perfil(es) en total</div>
    </div>
  );
}
