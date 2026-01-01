import React, { useRef, useEffect } from 'react';
import { ChatMessage } from '../types';
import { ChatBubble } from './ChatBubble';

interface ChatMessageAreaProps {
  messages: ChatMessage[];
}

export const ChatMessageArea: React.FC<ChatMessageAreaProps> = ({ messages }) => {
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages]);

  return (
    <div ref={chatContainerRef} className="flex-1 px-3 sm:px-6 pt-3 sm:pt-6 pb-20 sm:pb-24 space-y-3 sm:space-y-4 overflow-y-auto scroll-smooth hide-scrollbar">
      {messages.map((msg, index) => (
        <ChatBubble key={index} role={msg.role} text={msg.parts[0].text} />
      ))}
    </div>
  );
};