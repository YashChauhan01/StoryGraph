import React, { useState } from "react";
import { Send, Sparkles, BookOpen, AlertCircle } from "lucide-react";

interface StoryQueryProps {
  manuscriptId: string;
}

const StoryQuery: React.FC<StoryQueryProps> = ({ manuscriptId }) => {
  const [question, setQuestion] = useState<string>("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleAsk = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    setAnswer(null);

    try {
      const response = await fetch("http://localhost:8000/rag/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          manuscript_id: manuscriptId,
          question: question,
        }),
      });

      if (!response.ok) throw new Error("Failed to fetch answer");

      const data = await response.json();
      setAnswer(data.answer);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto mt-8 bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="bg-indigo-600 p-4 flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-yellow-300" />
        <h2 className="text-white font-semibold text-lg">Story Intelligence</h2>
      </div>

      <div className="p-6">
        {/* Input Area */}
        <form onSubmit={handleAsk} className="relative">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask about character motivations, plot holes, or themes..."
            className="w-full pl-4 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="absolute right-2 top-2 p-1.5 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </form>

        {/* Error State */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-lg flex items-center gap-2 text-sm">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        {/* Answer Display */}
        {answer && (
          <div className="mt-6 animate-fade-in">
            <div className="flex items-center gap-2 mb-2 text-indigo-900 font-medium">
              <BookOpen className="w-4 h-4" />
              <span>Analysis based on Narrative Graph:</span>
            </div>
            <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-100 text-gray-800 leading-relaxed text-sm md:text-base">
              {answer}
            </div>
          </div>
        )}

        {/* Empty State / Suggestions */}
        {!answer && !loading && !error && (
          <div className="mt-6">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
              Try asking:
            </p>
            <div className="flex flex-wrap gap-2">
              {[
                "How did the protagonist's emotions change?",
                "What was the turning point in Scene 3?",
                "Why is the character feeling miserable?",
              ].map((q, i) => (
                <button
                  key={i}
                  onClick={() => setQuestion(q)}
                  className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-600 text-xs rounded-full transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StoryQuery;
