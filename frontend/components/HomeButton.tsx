import React from 'react';
import { HomeIcon } from './Icons';

interface HomeButtonProps {
  onClick: () => void;
  theme?: 'light' | 'dark';
}

export const HomeButton: React.FC<HomeButtonProps> = ({ onClick, theme = 'dark' }) => {
  const themeClasses = theme === 'light'
    ? 'bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-500'
    : 'bg-white/20 text-white hover:bg-white/30 focus:ring-white/50';

  return (
    <button
      onClick={onClick}
      className={`w-10 h-10 flex items-center justify-center rounded-full hover:scale-110 hover:shadow-lg transition-all duration-200 ease-in-out shadow-md focus:outline-none focus:ring-2 ${themeClasses}`}
      aria-label="Go to Homepage"
    >
      <HomeIcon className="w-6 h-6" />
    </button>
  );
};
