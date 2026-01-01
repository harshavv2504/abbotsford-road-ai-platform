import React from 'react';

interface HomeCardProps {
  icon: React.ReactNode;
  title: string;
  onClick: () => void;
  animationDelay?: string;
}

export const HomeCard: React.FC<HomeCardProps> = ({ 
    icon, 
    title, 
    onClick, 
    animationDelay = '0s' 
}) => {
  return (
    <div 
        className="p-8 bg-white/10 backdrop-blur-md rounded-2xl shadow-lg border border-white/20 text-white cursor-pointer transition-all duration-300 hover:bg-white/20 hover:scale-105 hover:shadow-xl home-card-enter"
        onClick={onClick}
        style={{ animationDelay }}
    >
      <div className="flex flex-col items-center justify-center">
        {icon}
        <h3 className="text-2xl font-bold">{title}</h3>
      </div>
    </div>
  );
};
