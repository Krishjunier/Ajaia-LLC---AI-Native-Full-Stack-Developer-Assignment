import { create } from 'zustand'

export const useDocumentStore = create((set, get) => ({
  documents: [],
  activeDocId: null,

  setDocuments: (docs) => set({ documents: docs }),
  setActiveDocId: (id) => set({ activeDocId: id }),

  addDocument: (doc) => set((s) => ({ documents: [doc, ...s.documents] })),
  updateDocument: (updated) =>
    set((s) => ({
      documents: s.documents.map((d) => (d.id === updated.id ? { ...d, ...updated } : d)),
    })),
  removeDocument: (id) =>
    set((s) => ({
      documents: s.documents.filter((d) => d.id !== id),
      activeDocId: s.activeDocId === id ? null : s.activeDocId,
    })),
}))
