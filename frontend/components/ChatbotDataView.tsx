import React, { useState, useMemo, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { PageLoader, CloseIcon, ButtonSpinner, ChevronDownIcon, PhoneIcon, EnvelopeIcon, SortIcon, CheckIcon, CalendarIcon, ChartBarIcon } from './Icons';
import { ChatbotLead, ConversationTurn } from '../types';

// --- TYPES ---
type SortOptionKey = 'date_desc' | 'date_asc' | 'score_desc' | 'score_asc';

interface SortOption {
  key: SortOptionKey;
  label: string;
  icon: React.ReactNode;
}

// --- SORTING OPTIONS CONFIGURATION ---
const sortOptions: SortOption[] = [
    { key: 'date_desc', label: 'Date (Newest First)', icon: <CalendarIcon className="w-5 h-5 text-gray-400" /> },
    { key: 'date_asc', label: 'Date (Oldest First)', icon: <CalendarIcon className="w-5 h-5 text-gray-400" /> },
    { key: 'score_desc', label: 'Lead Score (High to Low)', icon: <ChartBarIcon className="w-5 h-5 text-gray-400" /> },
    { key: 'score_asc', label: 'Lead Score (Low to High)', icon: <ChartBarIcon className="w-5 h-5 text-gray-400" /> },
];

// --- INLINED COMPONENTS ---

interface ChatbotLeadCardProps {
  lead: ChatbotLead;
  onClick: () => void;
  style?: React.CSSProperties;
}

const ChatbotLeadCard: React.FC<ChatbotLeadCardProps> = ({ lead, onClick, style }) => {
    const getScoreColor = (score: number) => {
        if (score > 80) return 'border-green-500';
        if (score > 60) return 'border-yellow-500';
        return 'border-gray-300';
    };

    return (
        <div
            onClick={onClick}
            style={style}
            className={`bg-white rounded-lg shadow-md border-l-4 ${getScoreColor(lead.leadScore)} cursor-pointer hover:shadow-xl hover:scale-[1.02] transition-all duration-300 flex flex-col justify-between`}
        >
            <div className="p-5">
                <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-bold text-gray-800">{lead.userName}</h3>
                    <span className="text-xs font-semibold text-gray-500">{new Date(lead.date).toLocaleDateString()}</span>
                </div>
                <p className="text-sm text-gray-600 mb-4">{lead.email}</p>
                <p className="text-sm text-gray-700 leading-relaxed h-20 overflow-hidden line-clamp-3">
                    {lead.summary}
                </p>
            </div>
            <div className="bg-gray-50 px-5 py-3 rounded-b-lg flex justify-between items-center border-t">
                <span className="text-sm font-medium text-gray-600">Lead Score</span>
                <span className="text-lg font-bold text-blue-600">{lead.leadScore}</span>
            </div>
        </div>
    );
};


interface ChatbotLeadDetailModalProps {
  lead: ChatbotLead;
  onClose: () => void;
  onAddLead: (lead: ChatbotLead) => Promise<void>;
}

const ConversationHistory: React.FC<{ history: ConversationTurn[] }> = ({ history }) => {
    const [isOpen, setIsOpen] = useState(false);
    return (
        <div className="border rounded-lg">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex justify-between items-center p-3 bg-gray-50 hover:bg-gray-100 transition-colors rounded-t-lg"
            >
                <h4 className="font-semibold text-gray-700">Conversation History</h4>
                <ChevronDownIcon className={`w-5 h-5 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
            </button>
            {isOpen && (
                <div className="p-4 bg-white border-t max-h-60 overflow-y-auto hide-scrollbar">
                    <div className="space-y-4">
                        {history.map((turn, index) => (
                            <div key={index} className={`flex items-start gap-2.5 ${turn.speaker === 'user' ? 'justify-end' : ''}`}>
                                 {turn.speaker === 'bot' && (
                                     <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center font-bold text-gray-600 text-sm flex-shrink-0">AI</div>
                                 )}
                                <div className={`max-w-[80%] p-3 rounded-lg ${turn.speaker === 'user' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-gray-100 text-gray-800 rounded-bl-none'}`}>
                                    <p className="text-sm">{turn.text}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

const DetailItem: React.FC<{ icon: React.ReactNode; label: string; value: string; }> = ({ icon, label, value }) => (
    <div className="bg-gray-50 p-3 rounded-lg flex items-center gap-4">
        <div className="flex-shrink-0 w-10 h-10 bg-white rounded-full flex items-center justify-center text-blue-600 shadow-sm">
            {icon}
        </div>
        <div>
            <p className="text-sm font-medium text-gray-800">{value}</p>
            <p className="text-xs text-gray-500">{label}</p>
        </div>
    </div>
);


const ChatbotLeadDetailModal: React.FC<ChatbotLeadDetailModalProps> = ({ lead, onClose, onAddLead }) => {
  const [isAdding, setIsAdding] = useState(false);

  const handleAddLead = async () => {
    setIsAdding(true);
    await onAddLead(lead);
    // The parent will close the modal on success
  };
  
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50 modal-overlay-animate-in" onClick={onClose}>
        <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col modal-content-animate-in" onClick={e => e.stopPropagation()}>
            {/* Header */}
            <div className="flex-shrink-0 flex items-start justify-between p-5 border-b">
                <div>
                    <h2 className="text-xl font-bold text-gray-800">{lead.userName}</h2>
                    <p className="text-sm text-gray-500">Lead captured on {new Date(lead.date).toLocaleDateString()}</p>
                </div>
                <button onClick={onClose} className="p-1 rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-600">
                    <CloseIcon className="w-6 h-6" />
                </button>
            </div>
            {/* Content */}
            <div className="flex-1 p-6 space-y-6 overflow-y-auto hide-scrollbar">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <DetailItem icon={<EnvelopeIcon className="w-5 h-5"/>} label="Email" value={lead.email} />
                    <DetailItem icon={<PhoneIcon className="w-5 h-5"/>} label="Mobile" value={lead.mobile} />
                </div>
                <div className="bg-blue-50/50 p-4 rounded-lg border-l-4 border-blue-400">
                    <p className="text-xs text-blue-800 font-semibold mb-2">Conversation Summary</p>
                    <div className="text-gray-800 text-sm leading-relaxed prose prose-sm max-w-none prose-headings:font-bold prose-headings:text-gray-900 prose-p:text-gray-800 prose-strong:text-gray-900 prose-strong:font-semibold prose-ul:list-disc prose-ul:ml-4">
                        <ReactMarkdown>{lead.summary}</ReactMarkdown>
                    </div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg flex items-center justify-between">
                    <p className="text-sm font-semibold text-gray-700">Lead Score</p>
                    <p className="text-2xl font-bold text-blue-600">{lead.leadScore}</p>
                </div>
                <ConversationHistory history={lead.conversationHistory} />
            </div>
            {/* Footer */}
            <div className="px-5 py-4 border-t bg-gray-50 rounded-b-xl flex justify-end">
                <button
                    onClick={handleAddLead}
                    disabled={isAdding}
                    className="w-full sm:w-auto px-5 py-2 flex justify-center bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:bg-blue-400"
                >
                    {isAdding ? <ButtonSpinner /> : 'Add Lead to CRM'}
                </button>
            </div>
        </div>
    </div>
  );
};

// --- MAIN COMPONENT ---

interface ChatbotDataViewProps {
    isLoading: boolean;
    leads: ChatbotLead[];
    onAddLead: (lead: ChatbotLead) => Promise<void>;
}

export const ChatbotDataView: React.FC<ChatbotDataViewProps> = ({ isLoading, leads, onAddLead }) => {
  const [selectedLead, setSelectedLead] = useState<ChatbotLead | null>(null);
  const [sortBy, setSortBy] = useState<SortOptionKey>('date_desc');
  const [isSortMenuOpen, setIsSortMenuOpen] = useState(false);
  const sortMenuRef = useRef<HTMLDivElement>(null);
  
  const handleAddLeadAndCloseModal = async (lead: ChatbotLead) => {
    await onAddLead(lead);
    setSelectedLead(null); // Close modal after action
  };
  
  // Close sort menu on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (sortMenuRef.current && !sortMenuRef.current.contains(event.target as Node)) {
        setIsSortMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const sortedLeads = useMemo(() => {
    const [sortKey, sortOrder] = sortBy.split('_') as ['date' | 'score', 'asc' | 'desc'];
    const sortableLeads = [...leads];
    sortableLeads.sort((a, b) => {
      if (sortKey === 'date') {
        const dateA = new Date(a.date).getTime();
        const dateB = new Date(b.date).getTime();
        return sortOrder === 'asc' ? dateA - dateB : dateB - dateA;
      } else { // sortKey is 'score'
        const scoreA = a.leadScore;
        const scoreB = b.leadScore;
        return sortOrder === 'asc' ? scoreA - scoreB : scoreB - scoreA;
      }
    });
    return sortableLeads;
  }, [leads, sortBy]);

  if (isLoading) {
    return (
      <div className="p-8 h-full flex items-center justify-center bg-gray-50">
        <PageLoader />
      </div>
    );
  }

  const activeSortLabel = sortOptions.find(opt => opt.key === sortBy)?.label || 'Sort by';
  
  return (
    <div className="p-6 md:p-8 h-full bg-gray-50 overflow-y-auto hide-scrollbar">
        {leads.length > 0 && (
            <div className="flex items-center justify-end gap-4 mb-6">
                 <div className="relative" ref={sortMenuRef}>
                    <button 
                        onClick={() => setIsSortMenuOpen(prev => !prev)}
                        className="flex items-center gap-2 text-sm bg-white border border-gray-300 rounded-md py-2 px-4 text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <SortIcon className="w-5 h-5 text-gray-500"/>
                        <span>{activeSortLabel}</span>
                        <ChevronDownIcon className={`w-5 h-5 text-gray-500 transition-transform ${isSortMenuOpen ? 'rotate-180' : ''}`} />
                    </button>
                    {isSortMenuOpen && (
                        <div className="absolute right-0 mt-2 w-64 bg-white rounded-md shadow-lg border z-10 py-1">
                            {sortOptions.map(option => (
                                <button
                                    key={option.key}
                                    onClick={() => {
                                        setSortBy(option.key);
                                        setIsSortMenuOpen(false);
                                    }}
                                    className="w-full text-left flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                >
                                    {option.icon}
                                    <span className="flex-1">{option.label}</span>
                                    {sortBy === option.key && <CheckIcon className="w-5 h-5 text-blue-600" />}
                                </button>
                            ))}
                        </div>
                    )}
                 </div>
            </div>
        )}
        {sortedLeads.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {sortedLeads.map((lead, index) => (
                    <ChatbotLeadCard
                        key={lead.id}
                        lead={lead}
                        onClick={() => setSelectedLead(lead)}
                        style={{ animation: `card-fade-in 0.5s ease-out forwards`, animationDelay: `${index * 50}ms`, opacity: 0 }}
                    />
                ))}
            </div>
        ) : (
            <div className="text-center h-full flex flex-col items-center justify-center">
                <h2 className="text-2xl font-bold text-gray-800 mb-2">No New Leads</h2>
                <p className="text-gray-600">
                    Leads captured from the chatbot will appear here.
                </p>
            </div>
        )}
        {selectedLead && (
            <ChatbotLeadDetailModal
                lead={selectedLead}
                onClose={() => setSelectedLead(null)}
                onAddLead={handleAddLeadAndCloseModal}
            />
        )}
    </div>
  );
};