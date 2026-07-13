import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Download, ExternalLink, Trash2, Mail, Globe } from "lucide-react";
import api from "../../utils/api";

const ESTADOS = [
  { id: "nuevo", label: "Nuevo", cls: "text-txt-soft bg-ink-raised" },
  { id: "contactado", label: "Contactado", cls: "text-iris-300 bg-iris-500/12" },
  { id: "respondio", label: "Respondió", cls: "text-pos bg-pos/10" },
  { id: "descartado", label: "Descartado", cls: "text-neg bg-neg/10" },
];

function fmt(n) {
  if (n == null) return "—";
  if (n >= 1000) return (n / 1000).toFixed(1).replace(".0", "") + "k";
  return String(n);
}

export default function ListaDetalle() {
  const { id } = useParams();
  const [lista, setLista] = useState(null);
  const [perfiles, setPerfiles] = useState([]);

  async function cargar() {
    const { data } = await api.get(`/igp/listas/${id}`);
    setLista(data.lista); setPerfiles(data.perfiles);
  }
  useEffect(() => { cargar(); }, [id]);

  async function cambiarEstado(username, estado) {
    await api.patch(`/igp/listas/${id}/perfiles/${username}`, { estado_contacto: estado });
    setPerfiles((prev) => prev.map((p) => p.username === username ? { ...p, estado_contacto: estado } : p));
  }

  async function quitar(username) {
    await api.delete(`/igp/listas/${id}/perfiles/${username}`);
    setPerfiles((prev) => prev.filter((p) => p.username !== username));
  }

  async function exportar() {
    const res = await api.get(`/igp/listas/${id}/export`, { responseType: "blob" });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `lista_${(lista?.nombre || "export").replace(/\s+/g, "_")}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div>
      <div className="flex items-center justify-between gap-3 mb-5">
        <div className="flex items-center gap-3 min-w-0">
          <Link to="/prospeccion/listas" className="icon-btn"><ArrowLeft size={18} /></Link>
          <div className="min-w-0">
            <h2 className="font-display text-[20px] font-semibold text-txt truncate">{lista?.nombre || "…"}</h2>
            <div className="text-[12.5px] text-txt-mute">{perfiles.length} perfil(es)</div>
          </div>
        </div>
        <button onClick={exportar} className="btn-primary flex items-center gap-2" disabled={!perfiles.length}>
          <Download size={16} /> Export CSV
        </button>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-[13.5px]">
            <thead>
              <tr className="text-txt-mute text-left border-b border-ink-line">
                <th className="p-3">Perfil</th>
                <th className="p-3 text-right">Seguidores</th>
                <th className="p-3">Contacto</th>
                <th className="p-3">Estado</th>
                <th className="p-3"></th>
              </tr>
            </thead>
            <tbody>
              {perfiles.map((p) => (
                <tr key={p.username} className="border-b border-white/[0.04] hover:bg-ink-hover/50">
                  <td className="p-3">
                    <div className="font-medium text-txt">@{p.username}</div>
                    <div className="text-txt-mute text-[12px] truncate max-w-[260px]">{p.full_name || p.bio || "—"}</div>
                  </td>
                  <td className="p-3 text-right tnum text-txt-soft">{fmt(p.followers)}</td>
                  <td className="p-3">
                    <div className="flex items-center gap-2 text-txt-mute">
                      {p.email_publico && <Mail size={14} className="text-cyan-400" title={p.email_publico} />}
                      {p.external_url && <Globe size={14} className="text-cyan-400" title={p.external_url} />}
                      {!p.email_publico && !p.external_url && "—"}
                    </div>
                  </td>
                  <td className="p-3">
                    <select
                      value={p.estado_contacto || "nuevo"}
                      onChange={(e) => cambiarEstado(p.username, e.target.value)}
                      className={`pill border-0 cursor-pointer ${ESTADOS.find((e) => e.id === (p.estado_contacto || "nuevo"))?.cls}`}
                    >
                      {ESTADOS.map((e) => <option key={e.id} value={e.id} className="bg-ink text-txt">{e.label}</option>)}
                    </select>
                  </td>
                  <td className="p-3">
                    <div className="flex items-center gap-1">
                      <a href={p.ig_url || `https://www.instagram.com/${p.username}/`} target="_blank" rel="noreferrer" className="icon-btn"><ExternalLink size={15} /></a>
                      <button onClick={() => quitar(p.username)} className="icon-btn text-txt-mute hover:text-neg"><Trash2 size={15} /></button>
                    </div>
                  </td>
                </tr>
              ))}
              {perfiles.length === 0 && (
                <tr><td colSpan={5} className="p-8 text-center text-txt-mute">Lista vacía. Agregá perfiles desde <b>Perfiles</b>.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
