import { create } from "zustand";

const STORAGE_KEY = "evg_credentials";

export interface Credentials {
  arkApiKey: string;
  byteplusAk: string;
  byteplasSk: string;
}

function load(): Credentials | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Credentials) : null;
  } catch {
    return null;
  }
}

interface CredentialsState {
  credentials: Credentials | null;
  setCredentials: (creds: Credentials) => void;
  clear: () => void;
}

export const useCredentials = create<CredentialsState>((set) => ({
  credentials: load(),
  setCredentials: (creds) => {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(creds));
    set({ credentials: creds });
  },
  clear: () => {
    sessionStorage.removeItem(STORAGE_KEY);
    set({ credentials: null });
  },
}));
