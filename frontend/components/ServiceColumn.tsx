import React, { useState } from 'react';
import { ServiceColumnData, ServiceTicket } from '../types';
import { ServiceCard } from './ServiceCard';

interface ServiceColumnProps {
  column: ServiceColumnData;
  onCardDrop: (ticketId: string, targetColumnId: string) => void;
  onCardClick: (ticket: ServiceTicket) => void;
}

export const ServiceColumn: React.FC<ServiceColumnProps> = ({ column, onCardDrop, onCardClick }) => {
  const [isDragOver, setIsDragOver] = useState(false);

  const baseColumnClasses = 'bg-slate-100 border border-slate-200/80 rounded-xl';
  const titleClasses = 'text-slate-700 border-b border-slate-200';
  const dragOverClasses = isDragOver ? 'bg-blue-100 border-2 !border-blue-400' : '';

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
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
    const ticketId = e.dataTransfer.getData('ticketId');
    if (ticketId) {
      onCardDrop(ticketId, column.id);
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
            {column.tickets.length}
        </span>
      </h3>
      <div className="flex flex-col gap-4 overflow-y-auto pr-1.5 hide-scrollbar">
        {column.tickets.map((ticket, index) => (
          <ServiceCard 
            key={ticket.id} 
            ticket={ticket} 
            columnTitle={column.title}
            onClick={() => onCardClick(ticket)}
            style={{ animationDelay: `${index * 50}ms` }} 
          />
        ))}
      </div>
    </div>
  );
};
