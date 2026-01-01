import React from 'react';
import { CrmDeal, DealPriority } from '../types';
import { EnvelopeIcon, PhoneIcon } from './Icons';

interface LeadDetailsViewProps {
  deal: CrmDeal;
  onEditClick: () => void;
}

const PriorityTag: React.FC<{ priority: DealPriority }> = ({ priority }) => {
  const priorityClass = {
    'Low': 'priority-low',
    'Medium': 'priority-medium',
    'High': 'priority-high',
  }[priority];
  return <span className={`priority-tag ${priorityClass}`}>{priority}</span>;
};

const DetailCard: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
  <div className="bg-gray-100 p-4 rounded-lg">
    <p className="text-sm text-gray-500 mb-1">{label}</p>
    <div className="text-gray-800">{children}</div>
  </div>
);

export const LeadDetailsView: React.FC<LeadDetailsViewProps> = ({ deal, onEditClick }) => {
  return (
    <>
      <div className="px-6 py-4 space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-2 pb-2 border-b">Summary</h3>
          <p className="text-gray-600 whitespace-pre-wrap">{deal.summary}</p>
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-2 pb-2 border-b">Meeting Notes</h3>
          {deal.meetingNotes && deal.meetingNotes.trim() ? (
            <p className="text-gray-600 whitespace-pre-wrap">{deal.meetingNotes}</p>
          ) : (
            <p className="text-gray-500 italic">No notes added yet.</p>
          )}
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-2 pb-2 border-b">Comments</h3>
          {deal.comments && deal.comments.trim() ? (
            <p className="text-gray-600 whitespace-pre-wrap">{deal.comments}</p>
          ) : (
            <p className="text-gray-500 italic">No comments added yet.</p>
          )}
        </div>
      </div>
      <div className="px-6 py-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        <DetailCard label="Deal Value">
          <p className="text-2xl font-bold text-blue-600">${deal.dealValue.toLocaleString()}</p>
        </DetailCard>
        <DetailCard label="Priority">
          <PriorityTag priority={deal.priority} />
        </DetailCard>
        <DetailCard label="Contact Person">
          <p className="font-semibold">{deal.contactPerson}</p>
           {deal.email && (
                <div className="flex items-center gap-2 mt-2 text-gray-600">
                    <EnvelopeIcon className="w-4 h-4 flex-shrink-0" />
                    <span className="text-sm truncate">{deal.email}</span>
                </div>
            )}
            {deal.mobile && (
                <div className="flex items-center gap-2 mt-1 text-gray-600">
                    <PhoneIcon className="w-4 h-4 flex-shrink-0" />
                    <span className="text-sm">{deal.mobile}</span>
                </div>
            )}
        </DetailCard>
        <DetailCard label="Assignee">
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-gray-300 flex items-center justify-center text-xs font-bold text-gray-600">U</span>
            <span>Unassigned</span>
          </div>
        </DetailCard>
      </div>
      <div className="px-6 py-4 border-t bg-gray-50 rounded-b-xl flex justify-end">
        <button
          onClick={onEditClick}
          className="px-5 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
        >
          Edit Details
        </button>
      </div>
    </>
  );
};