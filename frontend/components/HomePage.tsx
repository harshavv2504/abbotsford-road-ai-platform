import React from 'react';
import { HomeCard } from './HomeCard';
import { CrmIcon, ChatbotIcon } from './Icons';
import * as authService from '../services/authService';

interface HomePageProps {
  onNavigateToChatbot: () => void;
  onNavigateToCrm: () => void;
}

export const HomePage: React.FC<HomePageProps> = ({ onNavigateToChatbot, onNavigateToCrm }) => {
  return (
    <div className="w-full max-w-4xl mx-auto text-center">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <HomeCard
                icon={<CrmIcon className="w-12 h-12 mb-4" />}
                title="Dashboard"
                onClick={onNavigateToCrm}
                animationDelay="0s"
            />
            <HomeCard
                icon={<ChatbotIcon className="w-12 h-12 mb-4" />}
                title="Chatbot"
                onClick={onNavigateToChatbot}
                animationDelay="0.1s"
            />
        </div>
    </div>
  );
};
