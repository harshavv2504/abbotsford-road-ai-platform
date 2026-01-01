export type Role = 'user' | 'model';

export interface ChatMessage {
  role: Role;
  parts: { text: string }[];
}

// --- CRM Types ---
export type DealPriority = 'Low' | 'Medium' | 'High';

export interface CrmDeal {
  id: string;
  companyName: string;
  dealValue: number;
  contactPerson: string;
  email?: string;
  mobile?: string;
  summary: string;
  priority: DealPriority;
  meetingNotes?: string;
  comments?: string;
  // assignee can be added later if needed
}

export interface KanbanColumnData {
  id:string;
  title: string;
  deals: CrmDeal[];
}

// --- Chatbot Lead Types ---
export interface ConversationTurn {
  speaker: 'user' | 'bot';
  text: string;
}

export interface ChatbotLead {
  id: string;
  date: string;
  userName: string;
  mobile: string;
  email: string;
  leadScore: number;
  summary: string;
  conversationHistory: ConversationTurn[];
}

// --- Service Desk Types ---
export interface ServiceTicket {
  id: string;
  customerName: string;
  issueSummary: string;
  dateOpened: string;
  dateConnected?: string;
  dateResolved?: string;
  contactEmail?: string;
  contactPhone?: string;
  city?: string;
  country?: string;
  notes?: string;
  comments?: string;
}

export interface ServiceColumnData {
  id: string;
  title: string;
  tickets: ServiceTicket[];
}