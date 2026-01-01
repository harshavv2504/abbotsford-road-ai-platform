import React, { useState, useEffect } from 'react';
import { CrmDeal } from '../types';
import { CloseIcon } from './Icons';
import { LeadDetailsView } from './LeadDetailsView';
import { LeadDetailsEditForm } from './LeadDetailsEditForm';

interface LeadDetailsModalProps {
  deal: CrmDeal;
  onClose: () => void;
  onSave: (updatedDeal: CrmDeal) => Promise<any>;
  onDelete: (dealId: string) => void;
}

export const LeadDetailsModal: React.FC<LeadDetailsModalProps> = ({ deal, onClose, onSave, onDelete }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<CrmDeal>({ ...deal });
  const [isSaving, setIsSaving] = useState(false);
  
  // Update form data if the underlying deal prop changes
  useEffect(() => {
    setFormData({ ...deal });
  }, [deal]);
  
  // Close modal on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    const isNumeric = name === 'dealValue';
    setFormData(prev => ({
      ...prev,
      [name]: isNumeric ? Number(value.replace(/[^0-9]/g, '')) : value,
    }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
        await onSave(formData);
        setIsEditing(false); // Switch back to view mode on successful save
    } catch (error) {
        console.error("Failed to save deal details:", error);
    } finally {
        setIsSaving(false);
    }
  };
  
  const handleCancelEdit = () => {
    setFormData({ ...deal }); // Reset changes
    setIsEditing(false);
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50 modal-overlay-animate-in lead-details-modal">
      <div
        className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col modal-content-animate-in"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex-shrink-0 flex items-center justify-between p-4 border-b">
          <h2 className="text-xl font-bold text-gray-800">{deal.companyName}</h2>
          <button onClick={onClose} className="p-1 rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-600">
            <CloseIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto hide-scrollbar">
            {isEditing ? (
                <LeadDetailsEditForm
                    formData={formData}
                    onFormChange={handleInputChange}
                    onSave={handleSave}
                    onCancel={handleCancelEdit}
                    isSaving={isSaving}
                    onDelete={() => onDelete(formData.id)}
                />
            ) : (
                <LeadDetailsView deal={formData} onEditClick={() => setIsEditing(true)} />
            )}
        </div>
      </div>
    </div>
  );
};