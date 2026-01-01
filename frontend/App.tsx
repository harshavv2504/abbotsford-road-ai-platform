import React, { useState } from 'react';
import PageWrapper from './components/PageWrapper';
import { LoginPage } from './components/LoginPage';
import { HomePage } from './components/HomePage';
import { CrmPage } from './components/CrmPage';
import { ChatbotPage } from './components/ChatbotPage';
import { AppHeader } from './components/AppHeader';
import { Sidebar } from './components/Sidebar';
import { useMediaQuery } from './hooks/useMediaQuery';
import { useChat } from './hooks/useChat';
import * as authService from './services/authService';

type Page = 'home' | 'chatbot' | 'crm' | 'login';
type ChatMode = 'outbound' | 'inbound';

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<Page>('home');
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(() => authService.isAuthenticated());
  const [isAuthLoading, setIsAuthLoading] = useState(false);
  const [redirectPath, setRedirectPath] = useState<Page>('home');
  const [isChatVisible, setIsChatVisible] = useState(true);
  const [isAvatarVisible, setIsAvatarVisible] = useState(false); // Avatar starts turned off
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [chatMode, setChatMode] = useState<ChatMode>('outbound');
  const [sessionKey, setSessionKey] = useState<number>(Date.now()); // Force chat reset on login/logout

  const isMobile = useMediaQuery('(max-width: 768px)');

  // Lift useChat to App level to prevent ChatbotPage re-renders
  // Use chatMode === 'inbound' to determine if using inbound mode
  // Pass sessionKey to force reset on login/logout
  const { messages, isLoading, sendMessage } = useChat(chatMode === 'inbound', isLoggedIn, chatMode, sessionKey);

  const handleLoginButtonClick = async () => {
    if (isLoggedIn) {
      setIsAuthLoading(true);
      try {
        await authService.logout();
        setIsLoggedIn(false);
        setCurrentPage('home');
        // Reset chat mode to outbound on logout
        setChatMode('outbound');
        // Force chat reset by changing session key
        setSessionKey(Date.now());
      } catch (error) {
        console.error("Logout failed", error);
      } finally {
        setIsAuthLoading(false);
      }
    } else {
      setRedirectPath(currentPage === 'login' ? 'home' : currentPage);
      setCurrentPage('login');
    }
  };

  const handleLoginSuccess = () => {
    setIsLoggedIn(true);
    setCurrentPage(redirectPath);
    // Force chat reset by changing session key
    setSessionKey(Date.now());
  };

  const handleNavigateToCrm = () => {
    if (isLoggedIn) {
      // Check if user is admin
      const user = authService.getUser();
      if (user && user.role === 'admin') {
        setCurrentPage('crm');
      } else {
        // Non-admin users cannot access CRM
        alert('Access Denied: Only administrators can access the CRM.');
      }
    } else {
      setRedirectPath('crm');
      setCurrentPage('login');
    }
  };

  const handleToggleChatVisibility = () => {
    setIsChatVisible(prev => !prev);
  };

  const handleToggleAvatar = () => {
    setIsAvatarVisible(prev => {
      const newAvatarState = !prev;
      // Hide chat when avatar is turned on
      if (newAvatarState) {
        setIsChatVisible(false);
      }
      return newAvatarState;
    });
  }

  const handleHomeClick = () => {
    setCurrentPage('home');
    setIsSidebarOpen(false);
  }

  const handleNavigateToChatbot = () => {
    if (isLoggedIn) {
      setCurrentPage('chatbot');
    } else {
      setRedirectPath('chatbot');
      setCurrentPage('login');
    }
  };

  // Enforce login check when on chatbot page
  React.useEffect(() => {
    if (currentPage === 'chatbot' && !isLoggedIn) {
      setRedirectPath('chatbot');
      setCurrentPage('login');
    }
  }, [currentPage, isLoggedIn]);

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'chatbot':
        // Require login for chatbot access (both outbound and inbound)
        if (!isLoggedIn) {
          setRedirectPath('chatbot');
          setCurrentPage('login');
          return <LoginPage onLoginSuccess={handleLoginSuccess} />;
        }
        return (
          <>
            <ChatbotPage
              key={`chatbot-${chatMode}`}
              isLoggedIn={isLoggedIn}
              isChatVisible={isChatVisible}
              isAvatarVisible={isAvatarVisible}
              messages={messages}
              isLoading={isLoading}
              sendMessage={sendMessage}
            />
            {/* Chat Mode Selector */}
            <div className="fixed top-20 right-4 z-30 bg-white/10 backdrop-blur-lg rounded-lg p-3 border border-white/20">
              <div className="text-white text-sm font-medium mb-2">Chat Mode:</div>
              <div className="flex gap-2">
                <button
                  onClick={() => setChatMode('outbound')}
                  className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                    chatMode === 'outbound'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white/20 text-white/70 hover:bg-white/30'
                  }`}
                >
                  Lead Gen
                </button>
                <button
                  onClick={() => setChatMode('inbound')}
                  className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                    chatMode === 'inbound'
                      ? 'bg-green-600 text-white'
                      : 'bg-white/20 text-white/70 hover:bg-white/30'
                  }`}
                >
                  Support
                </button>
              </div>
            </div>
          </>
        );
      case 'crm':
        return <CrmPage />;
      case 'login':
        return <LoginPage onLoginSuccess={handleLoginSuccess} />;
      case 'home':
      default:
        return <HomePage
          onNavigateToChatbot={handleNavigateToChatbot}
          onNavigateToCrm={handleNavigateToCrm}
        />;
    }
  };

  return (
    <PageWrapper isFullScreen={currentPage === 'crm'} bgClass="bg-main-dark">
      {isMobile && (
        <Sidebar
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
          currentPage={currentPage}
          isLoggedIn={isLoggedIn}
          isAuthLoading={isAuthLoading}
          onHomeClick={handleHomeClick}
          onLoginClick={handleLoginButtonClick}
          isChatVisible={isChatVisible}
          onToggleChat={handleToggleChatVisibility}
          onToggleAvatar={handleToggleAvatar}
          isAvatarVisible={isAvatarVisible}
        />
      )}
      <AppHeader
        currentPage={currentPage}
        isLoggedIn={isLoggedIn}
        isAuthLoading={isAuthLoading}
        onHomeClick={handleHomeClick}
        onLoginClick={handleLoginButtonClick}
        isMobile={isMobile}
        onMenuClick={() => setIsSidebarOpen(true)}
      />
      {renderCurrentPage()}
      {!isMobile && currentPage === 'chatbot' && (
        <div className="chatbot-controls absolute left-1/2 -translate-x-1/2 flex items-center space-x-4 z-20">
          <button
            onClick={handleToggleAvatar}
            className="px-5 py-2 bg-white/20 backdrop-blur-sm text-white rounded-full font-semibold hover:bg-white/30 transition-colors duration-200 shadow-lg">
            {isAvatarVisible ? 'Avatar Off' : 'Avatar On'}
          </button>
          <button
            onClick={handleToggleChatVisibility}
            className="px-5 py-2 bg-white/20 backdrop-blur-sm text-white rounded-full font-semibold hover:bg-white/30 transition-colors duration-200 shadow-lg"
          >
            {isChatVisible ? 'Hide Chat' : 'Show Chat'}
          </button>
        </div>
      )}
    </PageWrapper>
  );
};

export default App;