import React, { useMemo } from 'react';
import { KanbanColumnData, CrmDeal } from '../types';
import { KanbanColumn } from './KanbanColumn';
import { PageLoader, SearchIcon } from './Icons';

interface ManageLeadsViewProps {
  isLoading: boolean;
  kanbanData: KanbanColumnData[];
  searchQuery: string;
  onSearchQueryChange: (query: string) => void;
  onCardDrop: (dealId: string, targetColumnId: string) => void;
  onCardClick: (deal: CrmDeal) => void;
}

export const ManageLeadsView: React.FC<ManageLeadsViewProps> = ({
  isLoading,
  kanbanData,
  searchQuery,
  onSearchQueryChange,
  onCardDrop,
  onCardClick,
}) => {
  const filteredKanbanData = useMemo(() => {
    // Ensure kanbanData is an array
    if (!Array.isArray(kanbanData)) {
      return [];
    }
    
    if (!searchQuery.trim()) {
      return kanbanData;
    }
    
    const lowercasedQuery = searchQuery.toLowerCase();
    return kanbanData.map(column => ({
      ...column,
      deals: column.deals.filter(deal =>
        deal.companyName.toLowerCase().includes(lowercasedQuery) ||
        deal.contactPerson.toLowerCase().includes(lowercasedQuery) ||
        deal.dealValue.toString().includes(lowercasedQuery)
      )
    }));
  }, [kanbanData, searchQuery]);

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <PageLoader />
      </div>
    );
  }

  return (
    <>
      <div className="flex-shrink-0 px-6 md:px-8 py-3 border-b border-gray-200">
        <div className="relative max-w-sm">
          <span className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
            <SearchIcon className="h-5 w-5 text-gray-400" />
          </span>
          <input
            type="text"
            placeholder="Search leads..."
            value={searchQuery}
            onChange={(e) => onSearchQueryChange(e.target.value)}
            className="w-full block pl-10 pr-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50"
          />
        </div>
      </div>
      <div className="flex-1 overflow-hidden">
        <div className="kanban-board h-full">
          {Array.isArray(filteredKanbanData) && filteredKanbanData.map(column => (
            <KanbanColumn 
              key={column.id} 
              column={column} 
              theme="light" 
              onCardDrop={onCardDrop}
              onCardClick={onCardClick}
            />
          ))}
        </div>
      </div>
    </>
  );
};