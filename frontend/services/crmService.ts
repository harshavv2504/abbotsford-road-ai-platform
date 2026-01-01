import { KanbanColumnData, CrmDeal, ChatbotLead, ServiceColumnData, ServiceTicket } from '../types';
import { API_BASE_URL } from '../config/api';

const SERVICE_BOARD_DATA_KEY = 'serviceBoardData';

// Helper to get auth headers
const getAuthHeaders = () => {
  const token = localStorage.getItem('authToken');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};

// ============================================
// CHATBOT LEADS
// ============================================

export const getChatbotLeads = async (): Promise<ChatbotLead[]> => {
  const response = await fetch(`${API_BASE_URL}/crm/leads`, {
    headers: getAuthHeaders()
  });
  
  if (!response.ok) {
    if (response.status === 403) {
      throw new Error('403 Forbidden: Admin access required');
    }
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  const leads = await response.json();
  return leads;
};

export const deleteChatbotLead = async (leadId: string): Promise<ChatbotLead[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/crm/leads/${leadId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    // After deleting, fetch updated list
    return await getChatbotLeads();
  } catch (error) {
    console.error('Error deleting chatbot lead:', error);
    throw error;
  }
};

// ============================================
// CRM DEALS
// ============================================

export const getKanbanData = async (): Promise<KanbanColumnData[]> => {
  const response = await fetch(`${API_BASE_URL}/crm/deals`, {
    headers: getAuthHeaders()
  });
  
  if (!response.ok) {
    if (response.status === 403) {
      throw new Error('403 Forbidden: Admin access required');
    }
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  const kanbanData = await response.json();
  
  // Ensure we always return an array
  if (!Array.isArray(kanbanData)) {
    console.error('Kanban data is not an array:', kanbanData);
    return [];
  }
  
  return kanbanData;
};

export const updateDealColumn = async (dealId: string, targetColumnId: string): Promise<KanbanColumnData[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/crm/deals/${dealId}/stage`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify({ status: targetColumnId }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    // After updating, fetch updated kanban data
    return await getKanbanData();
  } catch (error) {
    console.error('Error updating deal column:', error);
    throw error;
  }
};

export const updateDealDetails = async (updatedDeal: CrmDeal): Promise<KanbanColumnData[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/crm/deals/${updatedDeal.id}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(updatedDeal),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    // After updating, fetch updated kanban data
    return await getKanbanData();
  } catch (error) {
    console.error('Error updating deal details:', error);
    throw error;
  }
};

export const deleteDeal = async (dealId: string): Promise<KanbanColumnData[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/crm/deals/${dealId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    // After deleting, fetch updated kanban data
    return await getKanbanData();
  } catch (error) {
    console.error('Error deleting deal:', error);
    throw error;
  }
};

export const addDeal = async (deal: Omit<CrmDeal, 'id'>): Promise<KanbanColumnData[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/crm/deals`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(deal),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    // After adding, fetch updated kanban data
    return await getKanbanData();
  } catch (error) {
    console.error('Error adding deal:', error);
    throw error;
  }
};


// ============================================
// INBOUND SERVICE (localStorage-based)
// ============================================

const initialServiceBoardData: ServiceColumnData[] = [
    {
        id: 'open',
        title: 'Open',
        tickets: [
            { id: 'ticket-1', customerName: 'Laura Williams', issueSummary: 'Cannot log in to my account. Password reset link is not working.', dateOpened: '2024-07-29T14:00:00Z', contactEmail: 'laura.w@example.com', contactPhone: '+1-415-555-0101', city: 'San Francisco', country: 'USA', notes: 'User is blocked. Needs immediate assistance with password reset.', comments: '' },
            { id: 'ticket-2', customerName: 'Michael Brown', issueSummary: 'Billing inquiry - I was charged twice for this month\'s subscription.', dateOpened: '2024-07-29T11:30:00Z', contactEmail: 'michael.b@example.com', contactPhone: '+44-20-7946-0958', city: 'London', country: 'UK', notes: 'Check Stripe for duplicate charges. Reference transaction ID #XYZ-123.', comments: 'Follow up with a credit note if confirmed.' },
        ],
    },
    {
        id: 'connected',
        title: 'Connected',
        tickets: [
            { id: 'ticket-3', customerName: 'Sophia Jones', issueSummary: 'Feature request for exporting data to CSV format.', dateOpened: '2024-07-28T18:00:00Z', dateConnected: '2024-07-29T09:00:00Z', contactEmail: 'sophia.j@example.com', contactPhone: '+61-2-9999-0100', city: 'Sydney', country: 'Australia', notes: 'User wants to export their dashboard data. Emailed them to let them know we have passed the feedback to the product team.', comments: 'Good suggestion. Link this ticket to internal feature tracker #PROD-456.' },
        ],
    },
    {
        id: 'resolved',
        title: 'Resolved',
        tickets: [
             { id: 'ticket-4', customerName: 'Daniel Garcia', issueSummary: 'How to integrate the API with my Python application?', dateOpened: '2024-07-27T10:00:00Z', dateConnected: '2024-07-27T10:15:00Z', dateResolved: '2024-07-27T11:00:00Z', contactEmail: 'daniel.g@example.com', contactPhone: '+1-212-555-0199', city: 'New York', country: 'USA', notes: 'Sent the user our Python SDK documentation and a code example.', comments: 'User confirmed the provided resources resolved their issue.' },
        ],
    },
];

const getServiceBoardDataFromStorage = (): ServiceColumnData[] => {
    try {
        const storedData = localStorage.getItem(SERVICE_BOARD_DATA_KEY);
        if (storedData) {
            const parsedData = JSON.parse(storedData);
            if (Array.isArray(parsedData) && parsedData[0]?.tickets) {
                return parsedData;
            }
        }
    } catch (error) {
        console.error("Failed to parse Service Board data from localStorage", error);
    }
    const initialData = JSON.parse(JSON.stringify(initialServiceBoardData));
    localStorage.setItem(SERVICE_BOARD_DATA_KEY, JSON.stringify(initialData));
    return initialData;
};

export const getServiceBoardData = (): Promise<ServiceColumnData[]> => {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve(getServiceBoardDataFromStorage());
        }, 1200); // Simulate network delay
    });
};

export const updateTicketColumn = (ticketId: string, targetColumnId: string): ServiceColumnData[] => {
    const data = getServiceBoardDataFromStorage();
    let ticketToMove: ServiceTicket | undefined;
    let sourceColumnId: string | undefined;

    for (const column of data) {
        const ticketIndex = column.tickets.findIndex(ticket => ticket.id === ticketId);
        if (ticketIndex !== -1) {
            ticketToMove = column.tickets[ticketIndex];
            sourceColumnId = column.id;
            column.tickets.splice(ticketIndex, 1);
            break;
        }
    }
    
    if (ticketToMove && sourceColumnId !== targetColumnId) {
        // Add a timestamp based on the new column
        if (targetColumnId === 'connected') {
            ticketToMove.dateConnected = new Date().toISOString();
        } else if (targetColumnId === 'resolved') {
            // Ensure connected date exists if it's being resolved now
            if (!ticketToMove.dateConnected) {
                ticketToMove.dateConnected = new Date().toISOString();
            }
            ticketToMove.dateResolved = new Date().toISOString();
        }

        const targetColumn = data.find(column => column.id === targetColumnId);
        if (targetColumn) {
            targetColumn.tickets.push(ticketToMove);
        }
    }

    localStorage.setItem(SERVICE_BOARD_DATA_KEY, JSON.stringify(data));
    return data;
};

export const updateServiceTicketDetails = (updatedTicket: ServiceTicket): Promise<ServiceColumnData[]> => {
    return new Promise((resolve) => {
        setTimeout(() => {
            const data = getServiceBoardDataFromStorage();
            let ticketFound = false;

            for (const column of data) {
                const ticketIndex = column.tickets.findIndex(t => t.id === updatedTicket.id);
                if (ticketIndex !== -1) {
                    column.tickets[ticketIndex] = { ...column.tickets[ticketIndex], ...updatedTicket };
                    ticketFound = true;
                    break;
                }
            }

            if (ticketFound) {
                localStorage.setItem(SERVICE_BOARD_DATA_KEY, JSON.stringify(data));
            }
            resolve(data);
        }, 500); // 0.5-second delay
    });
};
