import React from 'react';
import { ServiceTicket } from '../types';

interface ServiceCardProps {
  ticket: ServiceTicket;
  columnTitle: string;
  style?: React.CSSProperties;
  onClick: () => void;
}

export const ServiceCard: React.FC<ServiceCardProps> = ({ ticket, columnTitle, style, onClick }) => {
  const cardClasses = 'p-4 bg-white rounded-lg border border-gray-200/80 shadow transition-all duration-200 ease-in-out w-full text-left relative group hover:-translate-y-1 hover:shadow-md';
  
  const handleDragStart = (e: React.DragEvent<HTMLDivElement>) => {
    e.dataTransfer.setData('ticketId', ticket.id);
  };

  const getTimestamp = () => {
    let label = 'Opened';
    let dateStr = ticket.dateOpened;

    if (columnTitle === 'Connected' && ticket.dateConnected) {
      label = 'Connected';
      dateStr = ticket.dateConnected;
    } else if (columnTitle === 'Resolved' && ticket.dateResolved) {
      label = 'Resolved';
      dateStr = ticket.dateResolved;
    }
    
    return (
      <p className="text-xs text-gray-500">
        {label}: {new Date(dateStr).toLocaleDateString()}
      </p>
    );
  };

  return (
    <div 
      className={`${cardClasses} kanban-card-animate-in`} 
      style={style}
      draggable="true"
      onDragStart={handleDragStart}
      onClick={onClick}
    >
      <div className="cursor-pointer">
        <h4 className="text-base font-bold text-gray-900">{ticket.customerName}</h4>
        <p className="mt-2 text-sm text-gray-600 leading-snug line-clamp-3">{ticket.issueSummary}</p>
        <div className="mt-3 pt-2 border-t border-gray-200/80">
            {getTimestamp()}
        </div>
      </div>
    </div>
  );
};
