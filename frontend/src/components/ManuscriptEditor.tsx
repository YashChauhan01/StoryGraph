import React, { useCallback, useEffect, useRef } from "react";
import { useStoryStore } from "../store";
import { useWebSocket } from "../hooks/useWebSocket";

interface ManuscriptEditorProps {
  manuscriptId: string;
}

export const ManuscriptEditor: React.FC<ManuscriptEditorProps> = ({
  manuscriptId,
}) => {
  const { manuscript, updateContent, processing, isConnected, entities } = useStoryStore();
  const { sendParagraph } = useWebSocket(manuscriptId);

  // 1. NEW: Ref to track the last text we successfully sent to the backend
  const lastAnalyzedText = useRef<string>("");

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      updateContent(e.target.value);
    },
    [updateContent],
  );

  const handleSave = useCallback(() => {
    const currentText = manuscript.content.trim();

    // 2. SAFETY CHECK: Don't send if empty, already processing, or SAME as last time
    if (!currentText || processing) return;
    
    if (currentText === lastAnalyzedText.current) {
      console.log("⚠️ Skipping duplicate analysis");
      return;
    }

    console.log("📤 Sending paragraph for processing...");
    
    // Update the ref so we know this text is "clean"
    lastAnalyzedText.current = currentText;

    sendParagraph(
      currentText,
      manuscript.chapter,
      manuscript.paragraph,
    );
  }, [manuscript.content, manuscript.chapter, manuscript.paragraph, processing, sendParagraph]);

  // 3. AUTO-SAVE LOGIC (Debounced)
  useEffect(() => {
    // Only set the timer if there is content and we aren't currently working
    if (!manuscript.content.trim() || processing) return;

    const timer = setTimeout(() => {
      // Trigger save logic (which now includes the duplicate check)
      handleSave();
    }, 2000);

    return () => clearTimeout(timer);
  }, [manuscript.content, processing, handleSave]); 

  return (
    <div className="manuscript-editor bg-white p-6 rounded-lg shadow-sm h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold text-gray-800">{manuscript.title}</h1>
        <div className="flex items-center gap-3">
          {/* Connection Status Indicator */}
          <div className="flex items-center gap-2 px-3 py-1 bg-gray-50 rounded-full border border-gray-200">
            <div
              className={`w-2 h-2 rounded-full transition-colors duration-300 ${
                isConnected ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]" : "bg-red-500"
              }`}
            />
            <span className="text-xs font-medium text-gray-600">
              {isConnected ? "Live" : "Offline"}
            </span>
          </div>

          {/* Processing Status */}
          {processing ? (
            <span className="text-xs text-blue-600 font-medium animate-pulse flex items-center gap-1">
              <span className="inline-block w-2 h-2 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></span>
              Analyzing...
            </span>
          ) : entities.length > 0 ? (
            <span className="text-xs text-green-600 font-medium transition-opacity duration-500">
              ✓ {entities.length} entities
            </span>
          ) : null}
        </div>
      </div>

      <div className="flex gap-2 mb-4">
        <div className="relative group">
          <span className="absolute -top-2 left-2 px-1 bg-white text-[10px] text-gray-400">Chapter</span>
          <input
            type="number"
            min="1"
            value={manuscript.chapter}
            className="w-20 px-3 py-2 border border-gray-200 rounded text-sm bg-gray-50 text-gray-500 focus:outline-none cursor-not-allowed"
            readOnly
          />
        </div>
        <div className="relative group">
          <span className="absolute -top-2 left-2 px-1 bg-white text-[10px] text-gray-400">Para</span>
          <input
            type="number"
            min="1"
            value={manuscript.paragraph}
            className="w-20 px-3 py-2 border border-gray-200 rounded text-sm bg-gray-50 text-gray-500 focus:outline-none cursor-not-allowed"
            readOnly
          />
        </div>
      </div>

      <textarea
        value={manuscript.content}
        onChange={handleChange}
        placeholder="Start writing your story here..."
        className="editor-input flex-1 w-full p-4 border border-gray-200 rounded-lg resize-none focus:ring-2 focus:ring-blue-100 focus:border-blue-400 outline-none transition-all font-serif text-lg leading-relaxed text-gray-800 placeholder-gray-300"
      />

      <div className="flex justify-end mt-4">
        <button
          onClick={handleSave}
          disabled={processing || !isConnected}
          className={`
            px-6 py-2 rounded-md font-medium text-sm transition-all duration-200
            ${processing || !isConnected 
              ? "bg-gray-100 text-gray-400 cursor-not-allowed" 
              : "bg-blue-600 text-white hover:bg-blue-700 hover:shadow-md active:transform active:scale-95"}
          `}
        >
          {processing ? "Processing..." : "Save & Analyze"}
        </button>
      </div>
    </div>
  );
};