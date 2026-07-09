import axios from "axios";

/**
 * Cliente para endpoints PÚBLICOS (lead magnet / landing).
 * No adjunta el token de la app ni redirige a /login en errores — la prueba
 * gratuita vive fuera de la sesión autenticada.
 */
const publicApi = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "/api",
  headers: { "Content-Type": "application/json" },
});

export default publicApi;
