import React, { useState, useEffect } from 'react';
import { ServiceTicket } from '../types';
import { CloseIcon, EnvelopeIcon, PhoneIcon, UserCircleIcon, ButtonSpinner, MapPinIcon } from './Icons';

interface ServiceTicketModalProps {
  ticket: ServiceTicket;
  onClose: () => void;
  onSave: (updatedTicket: ServiceTicket) => Promise<void>;
}

const ReadOnlyField: React.FC<{ label: string; value?: string; }> = ({ label, value }) => (
    <div>
        <h3 className="text-md font-semibold text-gray-700 mb-2">{label}</h3>
        <div className="p-4 bg-gray-50 rounded-lg min-h-[6rem]">
            {value && value.trim() ? (
                <p className="text-gray-800 whitespace-pre-wrap">{value}</p>
            ) : (
                <p className="text-gray-500 italic">No {label.toLowerCase()} added yet.</p>
            )}
        </div>
    </div>
);

const EditInputField: React.FC<{ label: string; name: keyof ServiceTicket; value: string; onChange: (e: React.ChangeEvent<HTMLInputElement>) => void; type?: string; placeholder?: string }> = ({ label, name, value, onChange, type = 'text', placeholder }) => (
    <div>
        <label className="text-sm font-medium text-gray-600 mb-1 block">{label}</label>
        <input
            name={name}
            value={value || ''}
            onChange={onChange}
            type={type}
            placeholder={placeholder || `Enter ${label.toLowerCase()}...`}
            className="w-full p-2 bg-white border border-gray-300 rounded-md text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        />
    </div>
);

const EditNoteField: React.FC<{ label: string; name: keyof ServiceTicket; value: string; onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void }> = ({ label, name, value, onChange }) => (
    <div>
        <label className="text-sm font-medium text-gray-600 mb-1 block">{label}</label>
        <textarea
            name={name}
            value={value || ''}
            onChange={onChange}
            className="w-full p-2 bg-white border border-gray-300 rounded-md text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            rows={4}
            placeholder={`Add ${label.toLowerCase()} here...`}
        />
    </div>
);

export const ServiceTicketModal: React.FC<ServiceTicketModalProps> = ({ ticket, onClose, onSave }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<ServiceTicket>({ ...ticket });
  const [isSaving, setIsSaving] = useState(false);
  
  useEffect(() => {
    setFormData({ ...ticket });
  }, [ticket]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
        await onSave(formData);
        setIsEditing(false);
    } catch (error) {
        console.error("Failed to save ticket:", error);
    } finally {
        setIsSaving(false);
    }
  };

  const handleCancelEdit = () => {
    setFormData({ ...ticket });
    setIsEditing(false);
  };

  const CustomerDetailsView: React.FC<{ ticket: ServiceTicket }> = ({ ticket }) => (
    <div>
      <h3 className="text-md font-semibold text-gray-700 mb-2">Customer Details</h3>
      <div className="p-4 bg-gray-50 rounded-lg grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
        <div className="flex items-center gap-3">
          <UserCircleIcon className="w-5 h-5 text-gray-500 flex-shrink-0" />
          <span className="text-gray-800 font-medium truncate" title={ticket.customerName}>{ticket.customerName}</span>
        </div>
        <div className="flex items-center gap-3">
          <EnvelopeIcon className="w-5 h-5 text-gray-500 flex-shrink-0" />
          <span className="text-gray-800 truncate" title={ticket.contactEmail}>{ticket.contactEmail || 'N/A'}</span>
        </div>
        <div className="flex items-center gap-3">
          <PhoneIcon className="w-5 h-5 text-gray-500 flex-shrink-0" />
          <span className="text-gray-800 truncate" title={ticket.contactPhone}>{ticket.contactPhone || 'N/A'}</span>
        </div>
        <div className="flex items-center gap-3">
          <MapPinIcon className="w-5 h-5 text-gray-500 flex-shrink-0" />
          <span className="text-gray-800 truncate" title={`${ticket.city}, ${ticket.country}`}>
            {ticket.city && ticket.country ? `${ticket.city}, ${ticket.country}` : 'N/A'}
          </span>
        </div>
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50 modal-overlay-animate-in" onClick={onClose}>
      <div
        className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col modal-content-animate-in"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex-shrink-0 flex items-start justify-between p-5 border-b">
          <div>
            <h2 className="text-xl font-bold text-gray-800">Ticket Details</h2>
            <p className="text-sm text-gray-500">Ticket ID: {ticket.id}</p>
          </div>
          <button onClick={onClose} className="p-1 rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-600">
            <CloseIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 p-6 space-y-6 overflow-y-auto hide-scrollbar">
            {/* Issue Summary */}
            <div>
                <h3 className="text-md font-semibold text-gray-700 mb-2">Issue Summary</h3>
                <div className="p-4 bg-blue-50/70 border-l-4 border-blue-400 rounded-r-lg">
                    <p className="text-gray-800">{ticket.issueSummary}</p>
                </div>
            </div>
            
            {isEditing ? (
                <div className="space-y-6">
                    <div>
                        <h3 className="text-md font-semibold text-gray-700 mb-2">Edit Customer Details</h3>
                        <div className="p-4 border rounded-lg grid grid-cols-1 md:grid-cols-2 gap-4">
                           <EditInputField label="Customer Name" name="customerName" value={formData.customerName} onChange={handleInputChange} />
                           <EditInputField label="Email" name="contactEmail" value={formData.contactEmail || ''} onChange={handleInputChange} type="email" />
                           <EditInputField label="Mobile Number" name="contactPhone" value={formData.contactPhone || ''} onChange={handleInputChange} placeholder="+1 555-123-4567" />
                           <EditInputField label="City" name="city" value={formData.city || ''} onChange={handleInputChange} />
                           <EditInputField label="Country" name="country" value={formData.country || ''} onChange={handleInputChange} />
                        </div>
                    </div>
                    <EditNoteField label="Notes" name="notes" value={formData.notes || ''} onChange={handleInputChange} />
                    <EditNoteField label="Comments" name="comments" value={formData.comments || ''} onChange={handleInputChange} />
                </div>
            ) : (
                <div className="space-y-6">
                    <CustomerDetailsView ticket={formData} />
                    <ReadOnlyField label="Notes" value={formData.notes} />
                    <ReadOnlyField label="Comments" value={formData.comments} />
                </div>
            )}
        </div>

        {/* Footer */}
        <div className="px-5 py-4 border-t bg-gray-50 rounded-b-xl flex justify-end space-x-3">
            {isEditing ? (
                <>
                    <button
                        onClick={handleCancelEdit}
                        disabled={isSaving}
                        className="px-5 py-2 bg-gray-200 text-gray-800 rounded-lg font-semibold hover:bg-gray-300 transition-colors disabled:opacity-50"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={isSaving}
                        className="px-5 py-2 w-28 flex justify-center bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:bg-blue-400"
                    >
                        {isSaving ? <ButtonSpinner /> : 'Save'}
                    </button>
                </>
            ) : (
                <button
                    onClick={() => setIsEditing(true)}
                    className="px-5 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
                >
                    Edit Ticket
                </button>
            )}
        </div>
      </div>
    </div>
  );
};
