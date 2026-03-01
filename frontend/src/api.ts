import type { DashboardResponse } from './types'

// Use empty string in dev so Vite proxy forwards /api to backend (see vite.config.ts)
const BASE_URL = import.meta.env.VITE_API_URL ?? "";

export async function fetchDashboard(city: string): Promise<DashboardResponse> {
  const url = BASE_URL ? `${BASE_URL}/api/dashboard` : "/api/dashboard";
  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ city }),
    });
  } catch (err) {
    throw new Error(
      "Impossible de joindre le serveur. Vérifiez que le backend tourne sur http://localhost:8000"
    );
  }
  if (!res.ok) {
    let detail = "Erreur inconnue";
    try {
      const err = await res.json();
      detail = err.detail ?? detail;
    } catch {
      detail = res.status === 401
        ? "Clé API Mistral invalide ou manquante. Configurez MISTRAL_API_KEY dans .env"
        : `Erreur ${res.status}`;
    }
    throw new Error(detail);
  }
  return res.json();
}