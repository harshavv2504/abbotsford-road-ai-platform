import React from 'react';
import { MicIcon, SendIcon, StopIcon } from './Icons';

interface ChatButtonProps {
  isLoading: boolean;
  isRecording: boolean;
  hasInput: boolean;
  onMicClick: () => void;
}

export const ChatButton: React.FC<ChatButtonProps> = ({ 
    isLoading, 
    isRecording, 
    hasInput,
    onMicClick
}) => {
    const buttonBaseClasses = "flex-shrink-0 w-11 h-11 rounded-full flex items-center justify-center transition-all duration-200";
    const disabledClasses = "disabled:bg-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed";

    if (hasInput) {
        return (
            <button
                type="submit"
                disabled={isLoading}
                className={`${buttonBaseClasses} bg-blue-600 text-white hover:bg-blue-700 ${disabledClasses}`}
                aria-label="Send message"
            >
                <SendIcon className="w-6 h-6" />
            </button>
        );
    }
    
    if (isRecording) {
        return (
            <button
                type="button"
                onClick={onMicClick}
                className={`${buttonBaseClasses} bg-red-500 text-white hover:bg-red-600 animate-pulse`}
                aria-label="Stop recording"
            >
                <StopIcon className="w-6 h-6" />
            </button>
        );
    }

    return (
        <button
            type="button"
            onClick={onMicClick}
            disabled={isLoading}
            className={`${buttonBaseClasses} bg-gray-200 text-gray-800 hover:bg-gray-300 ${disabledClasses}`}
            aria-label="Start recording"
        >
            <MicIcon className="w-6 h-6" />
        </button>
    );
};
