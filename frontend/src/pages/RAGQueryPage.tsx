import React, { useState } from "react";
import {
  Send,
  Sparkles,
  BookOpen,
  AlertCircle,
  Quote,
  Lightbulb,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

interface RAGResponse {
  answer: string;
  relevant_scenes?: string[];
  confidence?: number;
}

const RAGQueryPage: React.FC = () => {
  const navigate = useNavigate();
  const [question, setQuestion] = useState<string>("");
  const [answer, setAnswer] = useState<RAGResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const manuscriptId = "test-manuscript";

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
      setAnswer({
        answer: data.answer,
        relevant_scenes: data.relevant_scenes || [],
        confidence: data.confidence || 0.8,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const suggestionQuestions = [
    "How did the protagonist's emotions change?",
    "What was the turning point in the story?",
    "Why is the character feeling this way?",
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* HEADER */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-indigo-600 p-2 rounded-lg text-white">
              <BookOpen size={20} />
            </div>
            <h1 className="text-xl font-bold text-gray-900">StoryGraph AI</h1>
          </div>

          <div className="flex items-center gap-4">
            <nav className="flex gap-4">
              <button
                onClick={() => navigate("/")}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg font-medium transition-colors"
              >
                Knowledge Graph
              </button>
              <button
                onClick={() => navigate("/rag")}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
              >
                RAG Query
              </button>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-12">
        {/* TITLE SECTION */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Sparkles className="w-8 h-8 text-indigo-600" />
            <h2 className="text-4xl font-bold text-gray-900">
              Story Intelligence
            </h2>
          </div>
          <p className="text-gray-600 text-lg">
            Ask questions about your story. Get AI-powered insights based on
            narrative analysis.
          </p>
        </div>

        {/* INPUT FORM */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-8 mb-8">
          <form onSubmit={handleAsk}>
            <div className="relative">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask about characters, plot, themes, emotions..."
                className="w-full pl-6 pr-16 py-4 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all text-lg"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !question.trim()}
                className="absolute right-3 top-3 p-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          </form>

          {/* SUGGESTIONS */}
          {!answer && !loading && !error && (
            <div className="mt-8 pt-8 border-t border-gray-100">
              <p className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
                Try asking:
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {suggestionQuestions.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => setQuestion(q)}
                    className="p-4 bg-gradient-to-br from-indigo-50 to-purple-50 hover:from-indigo-100 hover:to-purple-100 text-gray-700 text-sm rounded-lg border border-indigo-100 transition-all"
                  >
                    <Lightbulb className="w-4 h-4 text-indigo-600 mb-2" />
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ERROR STATE */}
        {error && (
          <div className="bg-red-50 border-2 border-red-200 rounded-2xl p-6 flex items-start gap-4 mb-8">
            <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-semibold text-red-900 mb-1">Error</h3>
              <p className="text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* ANSWER DISPLAY */}
        {answer && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* MAIN ANSWER */}
            <div className="bg-white rounded-2xl shadow-lg border border-indigo-100 overflow-hidden mb-8">
              <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-8 py-6 flex items-center gap-3">
                <Quote className="w-5 h-5 text-indigo-100" />
                <h3 className="text-white font-semibold text-lg">
                  AI Analysis
                </h3>
              </div>

              <div className="p-8">
                <div className="prose prose-lg max-w-none">
                  <p className="text-gray-800 leading-relaxed text-lg whitespace-pre-wrap">
                    {answer.answer}
                  </p>
                </div>

                {/* CONFIDENCE INDICATOR */}
                {answer.confidence !== undefined && (
                  <div className="mt-8 pt-8 border-t border-gray-100">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm font-medium text-gray-600">
                        Confidence Score
                      </span>
                      <span className="text-sm font-bold text-indigo-600">
                        {Math.round(answer.confidence * 100)}%
                      </span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
                        style={{ width: `${answer.confidence * 100}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* RELEVANT SCENES */}
            {answer.relevant_scenes && answer.relevant_scenes.length > 0 && (
              <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
                <div className="bg-gray-50 px-8 py-6 border-b border-gray-100">
                  <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                    <BookOpen className="w-5 h-5 text-gray-600" />
                    Relevant Story Scenes
                  </h3>
                </div>

                <div className="divide-y divide-gray-100">
                  {answer.relevant_scenes.map((scene, idx) => (
                    <div
                      key={idx}
                      className="p-6 hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex gap-4">
                        <div className="flex-shrink-0">
                          <span className="inline-flex items-center justify-center h-8 w-8 rounded-full bg-indigo-100 text-indigo-600 font-semibold text-sm">
                            {idx + 1}
                          </span>
                        </div>
                        <div className="flex-grow">
                          <p className="text-gray-700 leading-relaxed text-sm md:text-base">
                            {scene}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ASK FOLLOW-UP */}
            <div className="mt-8 text-center">
              <button
                onClick={() => setQuestion("")}
                className="text-indigo-600 hover:text-indigo-700 font-medium transition-colors"
              >
                Ask another question →
              </button>
            </div>
          </div>
        )}

        {/* LOADING STATE */}
        {loading && (
          <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-12 flex flex-col items-center justify-center gap-4">
            <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
            <p className="text-gray-600 font-medium">Analyzing your story...</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default RAGQueryPage;
