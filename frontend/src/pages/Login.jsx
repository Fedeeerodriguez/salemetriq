import { useState } from "react";
import { useNavigate } from "react-router-dom";
import SalemetriqLogo from "../components/SalemetriqLogo";
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
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || "No se pudo iniciar sesión");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center gap-4 mb-8">
          <SalemetriqLogo size={52} />
          <div className="text-center">
            <div className="font-brand text-xl text-[#EAF2F3]">SALEMETRIQ</div>
            <div className="text-xs text-[#6C7B84] uppercase tracking-[0.24em] mt-1">
              Sales Telemetry
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="card p-6 flex flex-col gap-4">
          <div>
            <label className="text-xs text-[#6C7B84] uppercase tracking-wider">Email</label>
            <input
              type="email" className="input mt-1" value={email}
              onChange={(e) => setEmail(e.target.value)} autoFocus required
            />
          </div>
          <div>
            <label className="text-xs text-[#6C7B84] uppercase tracking-wider">Contraseña</label>
            <input
              type="password" className="input mt-1" value={password}
              onChange={(e) => setPassword(e.target.value)} required
            />
          </div>
          {error && <div className="text-sm text-down">{error}</div>}
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Entrando…" : "Entrar"}
          </button>
        </form>
      </div>
    </div>
  );
}
