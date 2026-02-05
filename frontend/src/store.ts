import { create } from 'zustand';

// Define the shape of a Narrative Entity
export interface Entity {
  text: string;
  type: 'character' | 'location' | 'object' | 'event' | 'time';
}

// Define the shape of the Manuscript
interface Manuscript {
  title: string;
  content: string;
  chapter: number;
  paragraph: number;
}

interface StoryState {
  // --- Data ---
  manuscript: Manuscript;
  entities: Entity[];
  
  // --- Connection & Status ---
  isConnected: boolean;
  processing: boolean;
  
  // --- Actions ---
  // Updates the editor content in real-time
  updateContent: (content: string) => void;
  
  // Sets whether the WebSocket is active
  setConnected: (status: boolean) => void;
  
  // Controls the 'Analyzing...' spinners in the UI
  setProcessing: (status: boolean) => void;
  
  // Updates the list of extracted characters and locations
  setEntities: (entities: Entity[]) => void;
  
  // Resets the session (useful for new chapters)
  resetStory: () => void;
}

export const useStoryStore = create<StoryState>((set) => ({
  // Initial State
  manuscript: { 
    title: "New Story", 
    content: "", 
    chapter: 1, 
    paragraph: 0 
  },
  entities: [],
  isConnected: false,
  processing: false,

  // Logic to update content
  updateContent: (content) => 
    set((state) => ({ 
      manuscript: { ...state.manuscript, content } 
    })),

  setConnected: (isConnected) => set({ isConnected }),
  
  setProcessing: (processing) => set({ processing }),
  
  setEntities: (entities) => set({ entities }),

  resetStory: () => set({
    manuscript: { title: "New Story", content: "", chapter: 1, paragraph: 0 },
    entities: [],
    processing: false
  }),
}));