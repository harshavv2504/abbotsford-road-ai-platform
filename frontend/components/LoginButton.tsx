import React from 'react';

interface LoginButtonProps {
  isLoggedIn: boolean;
  isLoading: boolean;
  onClick: () => void;
}

export const LoginButton: React.FC<LoginButtonProps> = ({ isLoggedIn, isLoading, onClick }) => {
  const buttonText = isLoading ? 'Logging out...' : (isLoggedIn ? 'Logout' : 'Login');
  
  return (
    <button
      onClick={onClick}
      disabled={isLoading}
      className="px-4 py-2 bg-blue-600 text-white rounded-full font-semibold hover:bg-blue-700 hover:scale-105 hover:shadow-lg transition-all duration-200 ease-in-out shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-blue-400 disabled:cursor-wait disabled:scale-100"
      aria-label={isLoggedIn ? 'Logout' : 'Login'}
    >
      {buttonText}
    </button>
  );
};
