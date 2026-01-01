import React, { useState, useEffect } from 'react';
import { CrmDeal } from '../types';
import { ButtonSpinner, TrashIcon } from './Icons';

interface LeadDetailsEditFormProps {
    formData: CrmDeal;
    onFormChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => void;
    onSave: () => void;
    onCancel: () => void;
    onDelete: () => void;
    isSaving: boolean;
}

type FormErrors = {
    companyName?: string;
    dealValue?: string;
    contactPerson?: string;
    summary?: string;
};

export const LeadDetailsEditForm: React.FC<LeadDetailsEditFormProps> = ({
    formData,
    onFormChange,
    onSave,
    onCancel,
    onDelete,
    isSaving,
}) => {
    const [errors, setErrors] = useState<FormErrors>({});

    const validateForm = (data: CrmDeal): FormErrors => {
        const newErrors: FormErrors = {};
        if (!data.companyName.trim()) {
            newErrors.companyName = "Company Name cannot be empty.";
        }
        if (data.dealValue < 0) { // Will be a number from parent, just check negativity
            newErrors.dealValue = "Deal Value must be a non-negative number.";
        }
        if (!data.contactPerson.trim()) {
            newErrors.contactPerson = "Contact Person cannot be empty.";
        }
        if (!data.summary.trim()) {
            newErrors.summary = "Summary cannot be empty.";
        }
        return newErrors;
    };

    // Use useEffect to validate the form in real-time as data changes.
    useEffect(() => {
        setErrors(validateForm(formData));
    }, [formData]);

    const handleSaveClick = () => {
        const validationErrors = validateForm(formData);
        if (Object.keys(validationErrors).length === 0) {
            onSave();
        } else {
            setErrors(validationErrors);
        }
    };

    const formInputClasses = "w-full p-2 bg-white border rounded-md text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2";
    const normalBorder = "border-gray-300 focus:ring-blue-500 focus:border-blue-500";
    const errorBorder = "border-red-500 focus:ring-red-500 focus:border-red-500";
    
    const isFormValid = Object.keys(errors).length === 0;
    
    return (
        <>
            <div className="px-6 py-4 space-y-4">
                <div>
                    <label className="text-sm font-medium text-gray-600 mb-1 block">Company Name</label>
                    <input name="companyName" value={formData.companyName} onChange={onFormChange} className={`${formInputClasses} ${errors.companyName ? errorBorder : normalBorder}`} />
                    {errors.companyName && <p className="text-red-600 text-xs mt-1">{errors.companyName}</p>}
                </div>
                <div>
                    <label className="text-sm font-medium text-gray-600 mb-1 block">Summary</label>
                    <textarea name="summary" value={formData.summary} onChange={onFormChange} className={`${formInputClasses} ${errors.summary ? errorBorder : normalBorder}`} rows={3} />
                    {errors.summary && <p className="text-red-600 text-xs mt-1">{errors.summary}</p>}
                </div>
                <div>
                    <label className="text-sm font-medium text-gray-600 mb-1 block">Meeting Notes</label>
                    <textarea name="meetingNotes" value={formData.meetingNotes || ''} onChange={onFormChange} className={`${formInputClasses} ${normalBorder}`} rows={4} placeholder="Add any meeting notes here..." />
                </div>
                <div>
                    <label className="text-sm font-medium text-gray-600 mb-1 block">Comments</label>
                    <textarea name="comments" value={formData.comments || ''} onChange={onFormChange} className={`${formInputClasses} ${normalBorder}`} rows={4} placeholder="Add general comments here..." />
                </div>
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="text-sm font-medium text-gray-600 mb-1 block">Deal Value ($)</label>
                        <input name="dealValue" value={formData.dealValue} onChange={onFormChange} className={`${formInputClasses} ${errors.dealValue ? errorBorder : normalBorder}`} type="text" />
                        {errors.dealValue && <p className="text-red-600 text-xs mt-1">{errors.dealValue}</p>}
                    </div>
                    <div>
                        <label className="text-sm font-medium text-gray-600 mb-1 block">Priority</label>
                        <select name="priority" value={formData.priority} onChange={onFormChange} className={`${formInputClasses} ${normalBorder}`}>
                            <option>Low</option>
                            <option>Medium</option>
                            <option>High</option>
                        </select>
                    </div>
                </div>
                <div>
                    <label className="text-sm font-medium text-gray-600 mb-1 block">Contact Person</label>
                    <input name="contactPerson" value={formData.contactPerson} onChange={onFormChange} className={`${formInputClasses} ${errors.contactPerson ? errorBorder : normalBorder}`} />
                    {errors.contactPerson && <p className="text-red-600 text-xs mt-1">{errors.contactPerson}</p>}
                </div>
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="text-sm font-medium text-gray-600 mb-1 block">Email</label>
                        <input name="email" value={formData.email || ''} onChange={onFormChange} className={`${formInputClasses} ${normalBorder}`} type="email" placeholder="contact@example.com" />
                    </div>
                    <div>
                        <label className="text-sm font-medium text-gray-600 mb-1 block">Mobile</label>
                        <input name="mobile" value={formData.mobile || ''} onChange={onFormChange} className={`${formInputClasses} ${normalBorder}`} type="text" placeholder="555-123-4567" />
                    </div>
                </div>
            </div>
            <div className="px-6 py-4 border-t bg-gray-50 rounded-b-xl flex justify-between items-center">
                <button
                    onClick={onDelete}
                    disabled={isSaving}
                    className="px-3 py-2 text-sm text-red-600 rounded-lg font-semibold hover:bg-red-100 transition-colors disabled:opacity-50 flex items-center gap-1.5"
                >
                    <TrashIcon className="w-4 h-4" />
                    Delete Lead
                </button>
                <div className="flex space-x-3">
                    <button
                        onClick={onCancel}
                        disabled={isSaving}
                        className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg font-semibold hover:bg-gray-300 transition-colors disabled:opacity-50"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSaveClick}
                        disabled={isSaving || !isFormValid}
                        className="px-4 py-2 w-28 flex justify-center bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:bg-blue-400 disabled:cursor-not-allowed"
                    >
                        {isSaving ? <ButtonSpinner /> : 'Save'}
                    </button>
                </div>
            </div>
        </>
    );
};