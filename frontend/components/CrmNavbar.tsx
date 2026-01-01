import React from 'react';
import { CrmTab } from './CrmPage';

interface CrmNavbarProps {
  activeTab: CrmTab;
  onTabChange: (tab: CrmTab) => void;
}

export const CrmNavbar: React.FC<CrmNavbarProps> = ({ activeTab, onTabChange }) => {
  const getTabClasses = (tabName: CrmTab) => {
    const isActive = activeTab === tabName;
    return `px-4 py-3 font-semibold text-sm transition-colors duration-200 ease-in-out ${
      isActive
        ? 'text-blue-600 border-b-2 border-blue-600'
        : 'text-gray-500 hover:text-gray-800 border-b-2 border-transparent'
    }`;
  };

  return (
    <nav className="flex-shrink-0 bg-white border-b border-gray-200">
      <div className="px-6 md:px-8 flex items-center justify-center space-x-4">
        <button
          onClick={() => onTabChange('chatbotData')}
          className={getTabClasses('chatbotData')}
        >
          Chatbot Data
        </button>
        <button
          onClick={() => onTabChange('manageLeads')}
          className={getTabClasses('manageLeads')}
        >
          Manage Leads
        </button>
        <button
          onClick={() => onTabChange('inboundService')}
          className={getTabClasses('inboundService')}
        >
          Inbound Service
        </button>
      </div>
    </nav>
  );
};
