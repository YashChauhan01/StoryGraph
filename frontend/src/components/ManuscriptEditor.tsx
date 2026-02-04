import React, { useCallback, useEffect } from "react";
import { useStoryStore } from "../store";
import { useWebSocket } from "../hooks/useWebSocket";

interface ManuscriptEditorProps {
  manuscriptId: string;
}

export const ManuscriptEditor: React.FC<ManuscriptEditorProps> = ({
  manuscriptId,
}) => {
  const { manuscript, updateContent, processing, isConnected } =
    useStoryStore();
  const { sendParagraph } = useWebSocket(manuscriptId);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      updateContent(e.target.value);
    },
    [updateContent],
  );

  const handleSave = useCallback(() => {
    if (manuscript.content.trim()) {
      sendParagraph(
        manuscript.content,
        manuscript.chapter,
        manuscript.paragraph,
      );
    }
  }, [manuscript, sendParagraph]);

  // Auto-process after user stops typing
  useEffect(() => {
    const timer = setTimeout(() => {
      if (manuscript.content.trim() && !processing) {
        handleSave();
      }
    }, 2000); // Wait 2 seconds after last change

    return () => clearTimeout(timer);
  }, [manuscript.content, processing, handleSave]);

  return (
    <div className="manuscript-editor">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">{manuscript.title}</h1>
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"}`}
          />
          <span className="text-sm text-gray-600">
            {isConnected ? "Connected" : "Disconnected"}
          </span>
          {processing && (
            <span className="text-sm text-blue-600">Processing...</span>
          )}
        </div>
      </div>

      <div className="flex gap-2 mb-4">
        <input
          type="number"
          min="1"
          value={manuscript.chapter}
          placeholder="Chapter"
          className="w-20 px-2 py-1 border rounded"
          readOnly
        />
        <input
          type="number"
          min="1"
          value={manuscript.paragraph}
          placeholder="Paragraph"
          className="w-20 px-2 py-1 border rounded"
          readOnly
        />
      </div>

      <textarea
        value={manuscript.content}
        onChange={handleChange}
        placeholder="Start writing your story..."
        className="editor-input"
      />

      <button
        onClick={handleSave}
        disabled={processing || !isConnected}
        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
      >
        {processing ? "Processing..." : "Save & Analyze"}
      </button>
    </div>
  );
};
