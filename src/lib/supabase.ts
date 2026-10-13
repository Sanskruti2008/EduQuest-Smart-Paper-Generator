import { createClient, type SupabaseClient } from '@supabase/supabase-js';

let client: SupabaseClient | null = null;

export function getSupabaseClient(): SupabaseClient {
  if (client) return client;

  const url = import.meta.env.VITE_SUPABASE_URL?.trim();
  const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY?.trim();
  if (!url || !anonKey) {
    throw new Error(
      'Supabase frontend configuration is missing. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.'
    );
  }

  client = createClient(url, anonKey, {
    auth: {
      autoRefreshToken: true,
      detectSessionInUrl: true,
      persistSession: true,
    },
  });
  return client;
}

export async function getFacultyAccessToken(): Promise<string | null> {
  const { data, error } = await getSupabaseClient().auth.getSession();
  if (error) throw error;
  const token = data.session?.access_token ?? null;
  if (token) {
    sessionStorage.setItem('authToken', token);
  } else {
    sessionStorage.removeItem('authToken');
  }
  return token;
}
