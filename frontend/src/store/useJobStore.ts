import { create } from "zustand";

import { fetchJob, fetchProducts } from "@/lib/api";
import type { JobDetail, ProductItem } from "@/lib/types";

interface JobState {
  job: JobDetail | null;
  products: ProductItem[];
  loading: boolean;
  error: string | null;
  loadJob: (jobId: string) => Promise<void>;
  clear: () => void;
}

export const useJobStore = create<JobState>((set) => ({
  job: null,
  products: [],
  loading: false,
  error: null,
  loadJob: async (jobId: string) => {
    set({ loading: true, error: null });
    try {
      const [job, products] = await Promise.all([fetchJob(jobId), fetchProducts(jobId)]);
      set({ job, products, loading: false, error: null });
    } catch (error) {
      set({
        loading: false,
        error: error instanceof Error ? error.message : "Failed to load job data",
      });
    }
  },
  clear: () => set({ job: null, products: [], loading: false, error: null }),
}));
