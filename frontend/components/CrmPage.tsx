import React, { useState, useEffect } from 'react';
import { getKanbanData, updateDealColumn, updateDealDetails, deleteDeal, addDeal, getChatbotLeads, deleteChatbotLead as removeChatbotLead, getServiceBoardData, updateTicketColumn, updateServiceTicketDetails } from '../services/crmService';
import { KanbanColumnData, CrmDeal, ChatbotLead, ServiceColumnData, ServiceTicket } from '../types';
import { CrmNavbar } from './CrmNavbar';
import { ChatbotDataView } from './ChatbotDataView';
import { ManageLeadsView } from './ManageLeadsView';
import { LeadDetailsModal } from './LeadDetailsModal';
import { InboundServiceView } from './InboundServiceView';
import { ServiceTicketModal } from './ServiceTicketModal';
import { ConfirmationModal } from './ConfirmationModal';

export type CrmTab = 'manageLeads' | 'chatbotData' | 'inboundService';

export const CrmPage: React.FC = () => {
    const [kanbanData, setKanbanData] = useState<KanbanColumnData[]>([]);
    const [chatbotLeads, setChatbotLeads] = useState<ChatbotLead[]>([]);
    const [serviceBoardData, setServiceBoardData] = useState<ServiceColumnData[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<CrmTab>('chatbotData');
    const [selectedDeal, setSelectedDeal] = useState<CrmDeal | null>(null);
    const [selectedTicket, setSelectedTicket] = useState<ServiceTicket | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [ticketMoveConfirmation, setTicketMoveConfirmation] = useState<{ ticketId: string; targetColumnId: string; targetColumnTitle: string; } | null>(null);
    const [accessDenied, setAccessDenied] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            setAccessDenied(false);
            try {
                const [kanbanResult, chatbotLeadsResult, serviceBoardResult] = await Promise.all([
                    getKanbanData(),
                    getChatbotLeads(),
                    getServiceBoardData(),
                ]);
                setKanbanData(kanbanResult);
                setChatbotLeads(chatbotLeadsResult);
                setServiceBoardData(serviceBoardResult);
            } catch (error: any) {
                console.error("Failed to fetch CRM data:", error);
                if (error?.message?.includes('403') || error?.message?.includes('Forbidden')) {
                    setAccessDenied(true);
                }
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, []);

    const handleCardDrop = async (dealId: string, targetColumnId: string) => {
        try {
            const updatedData = await updateDealColumn(dealId, targetColumnId);
            setKanbanData(updatedData);
        } catch (error) {
            console.error('Error updating deal column:', error);
        }
    };

    const handleCardClick = (deal: CrmDeal) => {
        setSelectedDeal(deal);
    };

    const handleCloseModal = () => {
        setSelectedDeal(null);
    };

    const handleUpdateDeal = async (updatedDeal: CrmDeal) => {
        const updatedData = await updateDealDetails(updatedDeal);
        setKanbanData(updatedData);
        // Also update the selected deal so the view reflects changes instantly if not closing
        setSelectedDeal(updatedDeal);
        return updatedData;
    };

    const handleDeleteDeal = async (dealId: string) => {
        if (window.confirm('Are you sure you want to delete this lead? This action cannot be undone.')) {
            try {
                const updatedData = await deleteDeal(dealId);
                setKanbanData(updatedData);
                setSelectedDeal(null); // Close the modal after deletion
            } catch (error) {
                console.error('Error deleting deal:', error);
            }
        }
    };

    const handleAddLead = async (lead: ChatbotLead) => {
        // 1. Map ChatbotLead to a new CrmDeal
        const newDealData: Omit<CrmDeal, 'id'> = {
            companyName: `${lead.userName}'s Company`, // Placeholder
            dealValue: 0, // Initial value
            contactPerson: lead.userName,
            email: lead.email,
            mobile: lead.mobile,
            summary: lead.summary,
            priority: 'Medium', // Default priority
            meetingNotes: '', // Initialize empty notes
            comments: '',     // Initialize empty comments
        };

        // 2. Add to Kanban and remove from chatbot leads
        try {
            const [updatedKanbanData, updatedChatbotLeads] = await Promise.all([
                addDeal(newDealData),
                removeChatbotLead(lead.id)
            ]);
            setKanbanData(updatedKanbanData);
            setChatbotLeads(updatedChatbotLeads);
        } catch (error) {
            console.error("Failed to add lead:", error);
            // Optionally show an error to the user
        }
    };

    const handleTicketDrop = (ticketId: string, targetColumnId: string) => {
        let sourceColumnId: string | undefined;
        for (const column of serviceBoardData) {
            if (column.tickets.find(t => t.id === ticketId)) {
                sourceColumnId = column.id;
                break;
            }
        }

        if (sourceColumnId === targetColumnId) {
            return; // Don't do anything if dropped in the same column
        }

        if (targetColumnId === 'connected' || targetColumnId === 'resolved') {
            const targetColumn = serviceBoardData.find(c => c.id === targetColumnId);
            if (targetColumn) {
                setTicketMoveConfirmation({
                    ticketId,
                    targetColumnId,
                    targetColumnTitle: targetColumn.title,
                });
            }
        } else {
            // No confirmation needed for moving to 'Open'
            const updatedData = updateTicketColumn(ticketId, targetColumnId);
            setServiceBoardData(updatedData);
        }
    };

    const handleConfirmTicketMove = () => {
        if (!ticketMoveConfirmation) return;
        const { ticketId, targetColumnId } = ticketMoveConfirmation;
        const updatedData = updateTicketColumn(ticketId, targetColumnId);
        setServiceBoardData(updatedData);
        setTicketMoveConfirmation(null);
    };

    const handleCancelTicketMove = () => {
        setTicketMoveConfirmation(null);
    };

    const handleTicketClick = (ticket: ServiceTicket) => {
        setSelectedTicket(ticket);
    };

    const handleCloseTicketModal = () => {
        setSelectedTicket(null);
    };

    const handleUpdateTicket = async (updatedTicket: ServiceTicket) => {
        const updatedData = await updateServiceTicketDetails(updatedTicket);
        setServiceBoardData(updatedData);
        setSelectedTicket(updatedTicket); // Keep modal in sync
    };

    if (accessDenied) {
        return (
            <div className="w-full h-screen flex flex-col items-center justify-center bg-gray-50">
                <div className="max-w-md p-8 bg-white rounded-lg shadow-lg text-center">
                    <div className="mb-4">
                        <svg className="w-16 h-16 mx-auto text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
                    <p className="text-gray-600 mb-6">
                        You don't have permission to access the CRM. Only administrators can view this page.
                    </p>
                    <button
                        onClick={() => window.location.href = '/'}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        Go to Home
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="w-full h-screen flex flex-col bg-white pt-16">
            <CrmNavbar activeTab={activeTab} onTabChange={setActiveTab} />
            <main className="flex-1 overflow-hidden flex flex-col">
                {activeTab === 'manageLeads' && (
                    <ManageLeadsView
                        isLoading={isLoading}
                        kanbanData={kanbanData}
                        searchQuery={searchQuery}
                        onSearchQueryChange={setSearchQuery}
                        onCardDrop={handleCardDrop}
                        onCardClick={handleCardClick}
                    />
                )}
                {activeTab === 'chatbotData' && (
                    <ChatbotDataView 
                        isLoading={isLoading}
                        leads={chatbotLeads}
                        onAddLead={handleAddLead}
                    />
                )}
                {activeTab === 'inboundService' && (
                    <InboundServiceView
                        isLoading={isLoading}
                        serviceBoardData={serviceBoardData}
                        onCardDrop={handleTicketDrop}
                        onCardClick={handleTicketClick}
                    />
                )}
            </main>
            {selectedDeal && (
                <LeadDetailsModal
                    deal={selectedDeal}
                    onClose={handleCloseModal}
                    onSave={handleUpdateDeal}
                    onDelete={handleDeleteDeal}
                />
            )}
            {selectedTicket && (
                <ServiceTicketModal
                    ticket={selectedTicket}
                    onClose={handleCloseTicketModal}
                    onSave={handleUpdateTicket}
                />
            )}
            {ticketMoveConfirmation && (
                <ConfirmationModal
                    isOpen={!!ticketMoveConfirmation}
                    title="Confirm Status Change"
                    message={`Are you sure you want to move this ticket to the "${ticketMoveConfirmation.targetColumnTitle}" column?`}
                    onConfirm={handleConfirmTicketMove}
                    onCancel={handleCancelTicketMove}
                    confirmButtonText="Move Ticket"
                />
            )}
        </div>
    );
};