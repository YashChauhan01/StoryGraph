import { useEffect, useRef, useCallback } from "react";
import { useStoryStore } from "../store";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "ws://localhost:8000";

export const useWebSocket = (manuscriptId: string) => {
  const ws = useRef<WebSocket | null>(null);
  const { setConnected, setEntities, setProcessing } = useStoryStore();

  useEffect(() => {
    const wsUrl = `${BACKEND_URL}/ws/manuscript/${manuscriptId}`;
    console.log("Attempting to connect to:", wsUrl);

    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log("✓ WebSocket connected successfully");
      setConnected(true);
    };

    ws.current.onmessage = (event) => {
      console.log("Message received:", event.data);
      const data = JSON.parse(event.data);

      if (data.type === "entities_extracted") {
        setEntities(data.data.entities_extracted || []);
        setProcessing(false);
      }
    };

    ws.current.onerror = (error) => {
      console.error("✗ WebSocket error:", error);
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [manuscriptId, setConnected, setEntities, setProcessing]);

  const sendParagraph = useCallback(
    (text: string, chapter: number, paragraph: number) => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        setProcessing(true);
        ws.current.send(
          JSON.stringify({
            text,
            chapter,
            paragraph,
          }),
        );
      }
    },
    [setProcessing],
  );

  return { sendParagraph };
};
