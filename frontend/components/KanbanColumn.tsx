import React, { useState } from 'react';
import { KanbanColumnData, CrmDeal } from '../types';
import { KanbanCard } from './KanbanCard';

interface KanbanColumnProps {
  column: KanbanColumnData;
  theme?: 'light' | 'dark';
  onCardDrop: (dealId: string, targetColumnId: string) => void;
  onCardClick: (deal: CrmDeal) => void;
}

export const KanbanColumn: React.FC<KanbanColumnProps> = ({ column, theme = 'dark', onCardDrop, onCardClick }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const isLightTheme = theme === 'light';

  const baseColumnClasses = isLightTheme
    ? 'bg-slate-100 border border-slate-200/80 rounded-xl'
    : 'kanban-column'; // From global CSS
  
  const titleClasses = isLightTheme
    ? 'text-slate-700 border-b border-slate-200'
    : 'text-white border-b border-white/20';

  const dragOverClasses = isDragOver
    ? isLightTheme
      ? 'bg-blue-100 border-2 !border-blue-400' // Use ! to ensure override
      : 'kanban-column-drag-over'
    : '';

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault(); // Necessary to allow dropping
  };

  const handleDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    const dealId = e.dataTransfer.getData('dealId');
    if (dealId) {
      onCardDrop(dealId, column.id);
    }
  };

  return (
    <div 
        className={`flex-1 min-w-[300px] flex flex-col gap-4 p-4 transition-colors duration-200 ${baseColumnClasses} ${dragOverClasses}`}
        onDragOver={handleDragOver}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
    >
      <h3 className={`text-lg font-semibold mb-2 pb-2 flex items-center justify-between ${titleClasses}`}>
        <span>{column.title}</span>
        <span className="text-sm font-medium text-slate-500 bg-slate-200/80 px-2 py-0.5 rounded-full">
            {column.deals.length}
        </span>
      </h3>
      <div className="flex flex-col gap-4 overflow-y-auto pr-1.5 hide-scrollbar">
        {column.deals.map((deal, index) => (
          <KanbanCard 
            key={deal.id} 
            deal={deal} 
            theme={theme}
            onClick={() => onCardClick(deal)}
            style={{ animationDelay: `${index * 50}ms` }} 
          />
        ))}
      </div>
    </div>
  );
};