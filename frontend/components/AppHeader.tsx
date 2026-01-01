import React from 'react';
import { HomeButton } from './HomeButton';
import { LoginButton } from './LoginButton';
import { HamburgerIcon } from './Icons';

type Page = 'home' | 'chatbot' | 'crm' | 'login';

interface AppHeaderProps {
  currentPage: Page;
  isLoggedIn: boolean;
  isAuthLoading: boolean;
  onHomeClick: () => void;
  onLoginClick: () => void;
  isMobile: boolean;
  onMenuClick: () => void;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  currentPage,
  isLoggedIn,
  isAuthLoading,
  onHomeClick,
  onLoginClick,
  isMobile,
  onMenuClick,
}) => {
  const iconTheme = currentPage === 'crm' ? 'light' : 'dark';
  const hamburgerColor = 'text-black';

  if (isMobile) {
    return (
      <header className="absolute top-4 left-4 right-4 flex items-center justify-between z-20">
        <button onClick={onMenuClick} className={`p-2 rounded-full hover:bg-black/10 ${hamburgerColor}`}>
            <HamburgerIcon className="w-6 h-6" />
        </button>
         {currentPage === 'crm' && (
          <h1 className="text-xl font-bold text-gray-800">Chatbot CRM</h1>
        )}
      </header>
    );
  }

  return (
    <header className="absolute top-4 left-4 right-4 flex items-center justify-between z-30">
      <div className="flex items-center gap-3">
        {currentPage !== 'home' && (
          <HomeButton 
            onClick={onHomeClick} 
            theme={iconTheme} 
          />
        )}
        {currentPage === 'crm' && (
          <h1 className="text-xl font-bold text-gray-800">Chatbot CRM</h1>
        )}
      </div>

      {currentPage !== 'login' && (
        <LoginButton 
          isLoggedIn={isLoggedIn} 
          isLoading={isAuthLoading}
          onClick={onLoginClick} 
        />
      )}
    </header>
  );
};
