import React from 'react';

interface PageWrapperProps {
  children: React.ReactNode;
  isFullScreen?: boolean;
  bgClass: string;
}

const PageWrapper: React.FC<PageWrapperProps> = ({ children, isFullScreen = false, bgClass }) => {
  // Conditionally apply layout classes for full-screen or centered content
  const layoutClasses = isFullScreen
    ? 'h-screen overflow-hidden font-sans'
    : 'flex items-center justify-center h-screen overflow-hidden font-sans p-0 pt-20 pb-24 md:pt-20 md:pb-28 md:px-4';

  return (
    <div className={`${bgClass} ${layoutClasses} transition-all duration-1000 relative`}>
      {children}
    </div>
  );
};

export default PageWrapper;