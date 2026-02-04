import React from "react";
import { useStoryStore } from "../store";

interface EntitySidebarProps {
  onEntityClick?: (entity: any) => void;
}

export const EntitySidebar: React.FC<EntitySidebarProps> = ({
  onEntityClick,
}) => {
  const { entities } = useStoryStore();

  const groupedEntities = entities.reduce(
    (acc, entity) => {
      if (!acc[entity.type]) {
        acc[entity.type] = [];
      }
      acc[entity.type].push(entity);
      return acc;
    },
    {} as Record<string, any[]>,
  );

  return (
    <div className="sidebar p-4">
      <h2 className="text-lg font-bold mb-4">Entities</h2>

      {Object.entries(groupedEntities).length === 0 ? (
        <p className="text-gray-500">No entities extracted yet</p>
      ) : (
        Object.entries(groupedEntities).map(([type, items]) => (
          <div key={type} className="mb-6">
            <h3 className="font-semibold text-sm text-gray-700 mb-2 uppercase">
              {type}s ({items.length})
            </h3>
            <div className="space-y-2">
              {items.map((entity, idx) => (
                <div
                  key={idx}
                  onClick={() => onEntityClick?.(entity)}
                  className={`entity-badge entity-${type} cursor-pointer hover:opacity-80 transition`}
                >
                  {entity.text}
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
};
