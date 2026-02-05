import { useEffect, useRef, useCallback } from "react";
import { useStoryStore } from "../store";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "ws://localhost:8000";

export const useWebSocket = (manuscriptId: string) => {
  const ws = useRef<WebSocket | null>(null);
  const { setConnected, setEntities, setProcessing } = useStoryStore();

  useEffect(() => {
    if (!manuscriptId) return;

    const wsUrl = `${BACKEND_URL}/ws/manuscript/${manuscriptId}`;
    console.log("🔌 Connecting to:", wsUrl);

    const socket = new WebSocket(wsUrl);
    ws.current = socket;

    socket.onopen = () => {
      console.log("✅ Socket Open");
      setConnected(true);
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("📩 Received:", data);

        if (data.type === "entities_extracted") {
          // Robust extraction matching your backend's StoryProcessor output
          const extracted = data.data?.entities_extracted || {};
          
          const transformed = [
            ...Object.entries(extracted).flatMap(([type, list]: [string, any]) => 
              (Array.isArray(list) ? list : []).map(item => ({
                text: typeof item === 'string' ? item : item.text,
                type: type.replace(/s$/, '') as any, // 'characters' -> 'character'
                start: 0,
                end: 0
              }))
            )
          ];

          setEntities(transformed);
          setProcessing(false);
        }
      } catch (err) {
        console.error("❌ Message Parse Error:", err);
        setProcessing(false); // Unlock UI even on error
      }
    };

    socket.onclose = (e) => {
      console.warn("🔌 Socket Closed:", e.code);
      setConnected(false);
      setProcessing(false);
    };

    return () => {
      socket.close();
      ws.current = null;
    };
  }, [manuscriptId, setConnected, setEntities, setProcessing]);

  const sendParagraph = useCallback(
    (text: string, chapter: number, paragraph: number) => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        console.log("📤 Sending text to backend...");
        setProcessing(true);
        
        ws.current.send(JSON.stringify({ text, chapter, paragraph }));

        // FALLBACK: If AI is too slow, unlock button after 10 seconds
        setTimeout(() => setProcessing(false), 10000);
      } else {
        console.error("🚫 Socket not open. ReadyState:", ws.current?.readyState);
      }
    },
    [setProcessing]
  );

  return { sendParagraph };
};