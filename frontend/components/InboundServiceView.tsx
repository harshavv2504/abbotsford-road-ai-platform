import React from 'react';
import { ServiceColumnData, ServiceTicket } from '../types';
import { ServiceColumn } from './ServiceColumn';
import { PageLoader } from './Icons';

interface InboundServiceViewProps {
  isLoading: boolean;
  serviceBoardData: ServiceColumnData[];
  onCardDrop: (ticketId: string, targetColumnId:string) => void;
  onCardClick: (ticket: ServiceTicket) => void;
}

export const InboundServiceView: React.FC<InboundServiceViewProps> = ({
  isLoading,
  serviceBoardData,
  onCardDrop,
  onCardClick,
}) => {

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <PageLoader />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-hidden">
        <div className="kanban-board h-full">
          {serviceBoardData.map(column => (
            <ServiceColumn
              key={column.id} 
              column={column} 
              onCardDrop={onCardDrop}
              onCardClick={onCardClick}
            />
          ))}
        </div>
      </div>
  );
};
