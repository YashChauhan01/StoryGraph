import { create } from "zustand";

interface Entity {
  text: string;
  type: "character" | "location" | "object" | "event" | "time";
  start: number;
  end: number;
}

interface Manuscript {
  id: string;
  title: string;
  content: string;
  chapter: number;
  paragraph: number;
}

interface StoryStore {
  manuscript: Manuscript;
  entities: Entity[];
  isConnected: boolean;
  processing: boolean;
  setManuscript: (manuscript: Manuscript) => void;
  setEntities: (entities: Entity[]) => void;
  setConnected: (connected: boolean) => void;
  setProcessing: (processing: boolean) => void;
  updateContent: (content: string) => void;
}

export const useStoryStore = create<StoryStore>((set) => ({
  manuscript: {
    id: "default",
    title: "Untitled Manuscript",
    content: "",
    chapter: 1,
    paragraph: 1,
  },
  entities: [],
  isConnected: false,
  processing: false,
  setManuscript: (manuscript) => set({ manuscript }),
  setEntities: (entities) => set({ entities }),
  setConnected: (connected) => set({ isConnected: connected }),
  setProcessing: (processing) => set({ processing }),
  updateContent: (content) =>
    set((state) => ({
      manuscript: { ...state.manuscript, content },
    })),
}));
