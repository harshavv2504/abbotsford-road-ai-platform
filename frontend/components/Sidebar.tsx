import React from 'react';
import { HomeButton } from './HomeButton';
import { LoginButton } from './LoginButton';

type Page = 'home' | 'chatbot' | 'crm' | 'login';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  currentPage: Page;
  isLoggedIn: boolean;
  isAuthLoading: boolean;
  onHomeClick: () => void;
  onLoginClick: () => void;
  isChatVisible: boolean;
  onToggleChat: () => void;
  onToggleAvatar: () => void;
  isAvatarVisible: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onClose,
  currentPage,
  isLoggedIn,
  isAuthLoading,
  onHomeClick,
  onLoginClick,
  isChatVisible,
  onToggleChat,
  onToggleAvatar,
  isAvatarVisible,
}) => {
  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/50 z-40 transition-opacity duration-300 ${
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={onClose}
      ></div>
      {/* Sidebar */}
      <div
        className={`fixed top-0 left-0 h-full w-72 bg-slate-800 text-white shadow-xl z-50 transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-6 flex flex-col h-full">
          <h2 className="text-2xl font-bold mb-8">Menu</h2>
          <nav className="flex flex-col space-y-4">
            {currentPage !== 'home' && (
                <button onClick={onHomeClick} className="text-left text-lg hover:bg-slate-700 p-2 rounded-md">Home</button>
            )}
            {currentPage !== 'login' && (
                <button onClick={onLoginClick} className="text-left text-lg hover:bg-slate-700 p-2 rounded-md">
                    {isLoggedIn ? (isAuthLoading ? 'Logging out...' : 'Logout') : 'Login'}
                </button>
            )}
            {currentPage === 'chatbot' && (
              <>
                <hr className="border-slate-600 my-4" />
                <button onClick={onToggleAvatar} className="text-left text-lg hover:bg-slate-700 p-2 rounded-md">
                    {isAvatarVisible ? 'Avatar Off' : 'Avatar On'}
                </button>
                <button onClick={onToggleChat} className="text-left text-lg hover:bg-slate-700 p-2 rounded-md">
                    {isChatVisible ? 'Hide Chat' : 'Show Chat'}
                </button>
              </>
            )}
          </nav>
        </div>
      </div>
    </>
  );
};
