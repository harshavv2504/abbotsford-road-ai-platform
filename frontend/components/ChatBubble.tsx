import React from 'react';
import { Role } from '../types';
import { LoadingSpinner } from './Icons';

interface ChatBubbleProps {
  role: Role;
  text: string;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({ role, text }) => {
  const isUser = role === 'user';
  const bubbleClasses = isUser
    ? 'bg-blue-600 text-white self-end'
    : 'bg-gray-300 text-gray-800 self-start';
  const hasContent = text && text.trim().length > 0;

  return (
    <div className={`w-full flex ${isUser ? 'justify-end' : 'justify-start'} chat-bubble-animate-in`}>
        <div className={`max-w-[80%] md:max-w-[70%] p-3 rounded-2xl ${bubbleClasses} transition-all duration-300 ease-in-out`}>
            {hasContent ? (
                <p className="whitespace-pre-wrap">{text}</p>
            ) : (
                <LoadingSpinner />
            )}
        </div>
    </div>
  );
};