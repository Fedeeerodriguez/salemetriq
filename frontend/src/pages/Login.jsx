import { useState } from "react";
import { useNavigate } from "react-router-dom";
import IgpLogo from "../components/IgpLogo";
import { login } from "../utils/auth";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/buscar", { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || "No se pudo iniciar sesión");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-ink px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center gap-4 mb-8">
          <IgpLogo size={48} />
          <div className="text-center">
            <div className="font-brand text-xl text-txt">IG&nbsp;PROSPECTOR</div>
            <div className="text-[11px] text-txt-mute uppercase tracking-[0.22em] mt-1">Prospección por nicho</div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="card p-6 flex flex-col gap-4">
          <div>
            <label className="label">Email</label>
            <input
              type="email" className="input mt-1.5" value={email}
              onChange={(e) => setEmail(e.target.value)} autoFocus required
            />
          </div>
          <div>
            <label className="label">Contraseña</label>
            <input
              type="password" className="input mt-1.5" value={password}
              onChange={(e) => setPassword(e.target.value)} required
            />
          </div>
          {error && <div className="text-[13.5px] text-neg">{error}</div>}
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Entrando…" : "Entrar"}
          </button>
          <p className="text-[11.5px] text-txt-mute text-center">
            Solo lista y exporta perfiles públicos. No envía mensajes ni reacciona.
          </p>
        </form>
      </div>
    </div>
  );
}
