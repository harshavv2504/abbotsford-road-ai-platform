import React, { useState, useRef, useEffect } from 'react';
import { ChatButton } from './ChatButton';

interface ChatInputProps {
  isLoading: boolean;
  isRecording: boolean;
  statusMessage: string;
  onSendMessage: (message: string) => void;
  onMicClick: () => void;
  transcribedText?: string;
  onTranscribedTextUsed?: () => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({ 
    isLoading, 
    isRecording, 
    statusMessage, 
    onSendMessage, 
    onMicClick,
    transcribedText,
    onTranscribedTextUsed
}) => {
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-focus on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Re-focus after bot responds (when loading completes)
  useEffect(() => {
    if (!isLoading && !isRecording) {
      inputRef.current?.focus();
    }
  }, [isLoading, isRecording]);

  // Populate input with transcribed text
  useEffect(() => {
    if (transcribedText) {
      setInput(transcribedText);
      onTranscribedTextUsed?.();
      inputRef.current?.focus();
    }
  }, [transcribedText, onTranscribedTextUsed]);

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
        onSendMessage(input);
        setInput('');
        // Re-focus after sending message
        setTimeout(() => inputRef.current?.focus(), 0);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        // The form submission logic now also handles the enter key press
        handleFormSubmit(e as unknown as React.FormEvent);
    }
  };

  return (
    <div className="absolute bottom-0 left-0 right-0 p-2 sm:p-4 bg-gradient-to-t from-white via-white/90 to-transparent">
      <form onSubmit={handleFormSubmit} className="flex items-center w-full rounded-full bg-white shadow-lg border border-gray-200/80 py-1.5 pl-6 pr-2">
        <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={statusMessage || "Type or record a message..."}
            className="flex-grow w-full bg-transparent text-gray-800 placeholder-gray-500 focus:outline-none resize-none mr-3"
            rows={1}
            disabled={isLoading || isRecording}
        />
        <ChatButton
          isLoading={isLoading}
          isRecording={isRecording}
          hasInput={input.trim().length > 0}
          onMicClick={onMicClick}
        />
      </form>
    </div>
  );
};
