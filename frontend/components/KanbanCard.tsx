import React from 'react';
import { CrmDeal, DealPriority } from '../types';

interface KanbanCardProps {
  deal: CrmDeal;
  theme?: 'light' | 'dark';
  style?: React.CSSProperties;
  onClick: () => void;
}

const PriorityTag: React.FC<{ priority: DealPriority; theme: 'light' | 'dark' }> = ({ priority, theme }) => {
    const isLightTheme = theme === 'light';
    const priorityClasses = {
      Low: isLightTheme ? 'bg-green-100 text-green-800' : 'bg-green-900/50 text-green-300',
      Medium: isLightTheme ? 'bg-amber-100 text-amber-800' : 'bg-amber-900/50 text-amber-300',
      High: isLightTheme ? 'bg-red-100 text-red-800' : 'bg-red-900/50 text-red-300',
    }[priority];
  
    return (
      <span className={`inline-block px-2.5 py-0.5 text-xs font-medium rounded-full ${priorityClasses}`}>
        {priority}
      </span>
    );
};


export const KanbanCard: React.FC<KanbanCardProps> = ({ deal, theme = 'dark', style, onClick }) => {
  const isLightTheme = theme === 'light';

  const cardClasses = isLightTheme
    ? 'p-4 bg-white rounded-lg border border-gray-200/80 shadow transition-all duration-200 ease-in-out w-full text-left relative group hover:-translate-y-1 hover:shadow-md'
    : 'kanban-card p-4 w-full text-left relative group';
  
  const companyClasses = isLightTheme ? 'text-gray-900' : 'text-white';
  const valueClasses = isLightTheme ? 'text-green-800' : 'text-green-300';
  const personClasses = isLightTheme ? 'text-gray-800 font-semibold' : 'text-white font-semibold';
  const contactInfoClasses = isLightTheme ? 'text-gray-600' : 'text-white/80';
  const borderClass = isLightTheme ? 'border-gray-200/80' : 'border-white/20';


  const handleDragStart = (e: React.DragEvent<HTMLDivElement>) => {
    e.dataTransfer.setData('dealId', deal.id);
  };

  return (
    <div 
      className={`${cardClasses} kanban-card-animate-in`} 
      style={style}
      draggable="true"
      onDragStart={handleDragStart}
      onClick={onClick}
    >
      {/* Main clickable area for opening modal */}
      <div className="cursor-pointer">
        <h4 className={`text-lg font-bold ${companyClasses}`}>{deal.companyName}</h4>
        <p className={`mt-1 text-base font-semibold ${valueClasses}`}>${deal.dealValue.toLocaleString()}</p>

        <div className="mt-3 space-y-1">
            <p className={`text-sm ${personClasses}`}>{deal.contactPerson}</p>
            {deal.email && <p className={`text-xs ${contactInfoClasses}`}>{deal.email}</p>}
            {deal.mobile && <p className={`text-xs ${contactInfoClasses}`}>{deal.mobile}</p>}
        </div>

        <div className={`mt-4 pt-3 border-t ${borderClass}`}>
            <PriorityTag priority={deal.priority} theme={theme} />
        </div>
      </div>
    </div>
  );
};