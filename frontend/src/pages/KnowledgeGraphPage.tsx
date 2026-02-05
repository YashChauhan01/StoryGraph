import React, { useState, useEffect, useRef } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import {
  BookOpen,
  Activity,
  Save,
  RefreshCw,
  Wifi,
  WifiOff,
  Search,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

const MANUSCRIPT_ID = "test-manuscript";
const WS_URL = `ws://localhost:8000/ws/manuscript/${MANUSCRIPT_ID}`;
const API_URL = "http://localhost:8000";

const KnowledgeGraphPage: React.FC = () => {
  const navigate = useNavigate();
  const [text, setText] = useState<string>("");
  // New state for dynamic character name input
  const [characterName, setCharacterName] = useState<string>(""); 
  const [status, setStatus] = useState<
    "disconnected" | "connected" | "processing"
  >("disconnected");
  const [graphData, setGraphData] = useState<any[]>([]);
  const [overallSentiment, setOverallSentiment] = useState<string>(
    "Waiting for data...",
  );
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connect = () => {
      ws.current = new WebSocket(WS_URL);

      ws.current.onopen = () => {
        console.log("Connected to WS");
        setStatus("connected");
      };

      ws.current.onmessage = (event) => {
        const response = JSON.parse(event.data);
        if (response.type === "entities_extracted") {
          // Note: Automatic fetch might miss the character name if not set yet.
          // We rely mostly on manual trigger or the Save button flow.
          console.log("Entities extracted, ready to fetch graph.");
        }
      };

      ws.current.onclose = () => {
        setStatus("disconnected");
        setTimeout(connect, 3000);
      };
    };

    connect();
    return () => ws.current?.close();
  }, []);

  const handleSaveAndAnalyze = async () => {
    if (!ws.current || status === "disconnected") return;

    setStatus("processing");

    ws.current.send(
      JSON.stringify({
        text: text,
        chapter: 1,
        paragraph: 0,
      }),
    );

    // If user has already typed a name, try to fetch after a delay
    if (characterName.trim()) {
      setTimeout(fetchGraphData, 2000);
    }
  };

  const fetchGraphData = async () => {
    if (!characterName.trim()) {
      alert("Please enter a character name first.");
      return;
    }

    try {
      // Encode the user input to handle spaces and special characters safely
      const encodedName = encodeURIComponent(characterName.trim());
      const res = await fetch(
        `${API_URL}/analytics/character-arc/${MANUSCRIPT_ID}/${encodedName}`,
      );
      
      if (res.ok) {
        const data = await res.json();
        setGraphData(data.data_points);
        setOverallSentiment(data.overall_sentiment);
        if (status === "processing") setStatus("connected");
      } else {
        console.error("Character not found");
        setOverallSentiment("Character not found");
        setGraphData([]);
      }
    } catch (err) {
      console.error("Failed to fetch graph", err);
      setOverallSentiment("Error fetching data");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-800 font-sans">
      {/* HEADER */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
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
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
              >
                Knowledge Graph
              </button>
              <button
                onClick={() => navigate("/rag")}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg font-medium transition-colors"
              >
                RAG Query
              </button>
            </nav>

            <span
              className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
                status === "connected"
                  ? "bg-green-100 text-green-700"
                  : status === "processing"
                    ? "bg-blue-100 text-blue-700"
                    : "bg-red-100 text-red-700"
              }`}
            >
              {status === "connected" ? (
                <Wifi size={14} />
              ) : status === "processing" ? (
                <RefreshCw size={14} className="animate-spin" />
              ) : (
                <WifiOff size={14} />
              )}
              {status === "connected"
                ? "Live"
                : status === "processing"
                  ? "Analyzing..."
                  : "Offline"}
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* LEFT COLUMN: EDITOR */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-1 flex flex-col h-[600px]">
            <textarea
              className="flex-1 w-full p-6 resize-none outline-none text-gray-700 leading-relaxed font-serif text-lg placeholder:text-gray-300"
              placeholder="Paste your story here... (Don't forget empty lines between paragraphs!)"
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <div className="p-4 border-t border-gray-100 bg-gray-50 rounded-b-xl flex justify-between items-center">
              <span className="text-xs text-gray-500">
                {text.length} characters
              </span>
              <button
                onClick={handleSaveAndAnalyze}
                disabled={status === "disconnected" || !text.trim()}
                className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Save size={18} />
                Save & Analyze
              </button>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: VISUALIZATION */}
        <div className="lg:col-span-7">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            
            {/* NEW: Character Input Section */}
            <div className="mb-6 pb-6 border-b border-gray-100">
               <label className="block text-sm font-medium text-gray-700 mb-2">Analyze Character</label>
               <div className="flex gap-2">
                 <div className="relative flex-1">
                    <Search className="absolute left-3 top-2.5 text-gray-400 w-4 h-4" />
                    <input 
                      type="text" 
                      value={characterName}
                      onChange={(e) => setCharacterName(e.target.value)}
                      placeholder="Enter Name (e.g. Little Match Girl)"
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                    />
                 </div>
                 <button 
                   onClick={fetchGraphData}
                   disabled={!characterName.trim()}
                   className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                 >
                   Load Arc
                 </button>
               </div>
            </div>

            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <Activity className="text-indigo-600" size={20} />
                <h2 className="font-semibold text-gray-900">
                  Emotional Volatility Arc
                </h2>
              </div>
              <span className="text-xs font-medium px-2 py-1 bg-gray-100 rounded text-gray-600">
                Arc Type: {overallSentiment}
              </span>
            </div>

            <div className="h-[400px] w-full">
              {graphData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={graphData}
                    margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      vertical={false}
                      stroke="#f0f0f0"
                    />
                    <XAxis
                      dataKey="step"
                      stroke="#9ca3af"
                      tick={{ fontSize: 12 }}
                      label={{
                        value: "Narrative Time (Scenes)",
                        position: "insideBottom",
                        offset: -5,
                        fontSize: 12,
                        fill: "#6b7280",
                      }}
                    />
                    <YAxis
                      domain={[-1, 1]}
                      stroke="#9ca3af"
                      tick={{ fontSize: 12 }}
                      label={{
                        value: "Emotional State",
                        angle: -90,
                        position: "insideLeft",
                        fontSize: 12,
                        fill: "#6b7280",
                      }}
                    />
                    <Tooltip
                      contentStyle={{
                        borderRadius: "8px",
                        border: "none",
                        boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                      }}
                      labelStyle={{ color: "#6b7280", fontSize: "12px" }}
                    />
                    <ReferenceLine y={0} stroke="#e5e7eb" />
                    <Line
                      type="monotone"
                      dataKey="sentiment_score"
                      stroke="#4f46e5"
                      strokeWidth={3}
                      dot={{
                        r: 4,
                        fill: "#4f46e5",
                        strokeWidth: 2,
                        stroke: "#fff",
                      }}
                      activeDot={{ r: 6 }}
                      animationDuration={1500}
                    />
                    <Line
                      type="monotone"
                      dataKey="smoothed_score"
                      stroke="#fbbf24"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-gray-400 bg-gray-50 rounded-lg border border-dashed border-gray-200">
                  <div className="text-center">
                    <p>No analysis data yet.</p>
                    <p className="text-sm mt-1">Enter a character name and click "Load Arc"</p>
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-center gap-6 mt-4 text-xs text-gray-500">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-indigo-600"></span>
                <span>Raw Emotion</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-yellow-400"></span>
                <span>Smoothed Trend</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default KnowledgeGraphPage;