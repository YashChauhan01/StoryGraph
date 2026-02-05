import React from "react";
import { useStoryStore } from "../store";

interface EntitySidebarProps {
  onEntityClick?: (entity: any) => void;
}

export const EntitySidebar: React.FC<EntitySidebarProps> = ({
  onEntityClick,
}) => {
  // Pull both entities and processing state from your Zustand store
  const { entities, processing } = useStoryStore();

  // Group entities by their type (character, location, etc.)
  const groupedEntities = entities.reduce(
    (acc, entity) => {
      const type = entity.type || 'unknown';
      if (!acc[type]) {
        acc[type] = [];
      }
      acc[type].push(entity);
      return acc;
    },
    {} as Record<string, any[]>,
  );

  // Mapping types to specific Tailwind color themes for visual hierarchy
  const typeColors: Record<string, string> = {
    character: "bg-blue-100 text-blue-800 border-blue-300",
    location: "bg-green-100 text-green-800 border-green-300",
    object: "bg-yellow-100 text-yellow-800 border-yellow-300",
    event: "bg-purple-100 text-purple-800 border-purple-300",
    time: "bg-orange-100 text-orange-800 border-orange-300",
  };

  return (
    <div className="sidebar p-4 bg-gray-50 border-l border-gray-200 overflow-y-auto h-full min-w-[300px]">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-lg font-bold text-gray-800">
          Extracted Entities
        </h2>
        {/* Visual feedback for the background extraction worker */}
        {processing && (
          <div className="flex items-center gap-2">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent"></div>
            <span className="text-xs text-blue-600 font-medium animate-pulse">Analyzing...</span>
          </div>
        )}
      </div>

      {/* State 1: AI is currently working and we have no data yet */}
      {processing && entities.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <p className="text-gray-500 text-sm italic">
            Connecting to Groq LPU...
          </p>
        </div>
      )}

      {/* State 2: No data and AI is idle */}
      {!processing && Object.entries(groupedEntities).length === 0 ? (
        <div className="border-2 border-dashed border-gray-200 rounded-lg p-8 text-center">
          <p className="text-gray-400 text-sm">
            No entities extracted yet. 
            <br />
            <span className="font-semibold text-blue-500">Write and analyze</span> text to see the story structure.
          </p>
        </div>
      ) : (
        /* State 3: Render grouped entities */
        Object.entries(groupedEntities).map(([type, items]) => (
          <div key={type} className="mb-8">
            <h3 className="font-bold text-[10px] text-gray-500 mb-3 uppercase tracking-[0.1em] border-b border-gray-200 pb-1">
              {type}s ({items.length})
            </h3>
            <div className="space-y-2">
              {items.map((entity, idx) => (
                <div
                  key={`${type}-${idx}`}
                  onClick={() => onEntityClick?.(entity)}
                  className={`px-3 py-2 rounded border text-sm font-medium cursor-pointer 
                    hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 active:scale-95
                    ${typeColors[type] || "bg-gray-100 text-gray-800 border-gray-300"}`}
                >
                  <div className="flex justify-between items-center">
                    <span>{entity.text}</span>
                    <span className="text-[10px] opacity-60">→</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
};