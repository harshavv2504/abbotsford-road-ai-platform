import { useState, useCallback, useEffect } from 'react';
import { ChatMessage } from '../types';
import { sendMessage as sendChatMessage, initChat } from '../services/chatService';
import { handleApiError } from '../utils/errorUtils';
import * as authService from '../services/authService';

export const useChat = (isInboundMode: boolean, isLoggedIn?: boolean, chatMode?: string, sessionKey?: number) => {
    const getInitialMessages = useCallback((): ChatMessage[] => {
        let greeting = "Hey! I'm Logan from Abbotsford Road Coffee. I help folks opening new cafés, support existing café owners, and answer any coffee questions you've got. What brings you by?";
        
        if (isInboundMode) {
            const user = authService.getUser();
            const userName = user?.name || 'there';
            greeting = `Hey ${userName}! Welcome back. I'm here to help with any issues, discuss improvements, or answer questions about your café operations. What can I do for you today?`;
        }
        
        return [
            {
                role: 'model',
                parts: [{ text: greeting }],
            },
        ];
    }, [isInboundMode]);

    const [messages, setMessages] = useState<ChatMessage[]>(getInitialMessages());
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        // Initialize fresh chat session and reset messages when login state, chat mode, or session changes
        initChat();
        setMessages(getInitialMessages());
        console.log('Chat reset. isInboundMode:', isInboundMode, 'isLoggedIn:', isLoggedIn, 'chatMode:', chatMode, 'sessionKey:', sessionKey);
    }, [isInboundMode, isLoggedIn, chatMode, sessionKey, getInitialMessages]);

    const sendMessage = useCallback(async (messageText: string) => {
        if (!messageText.trim() || isLoading) return;

        setIsLoading(true);

        const userMessage: ChatMessage = { role: 'user', parts: [{ text: messageText }] };
        setMessages(prev => [...prev, userMessage]);

        try {
            const stream = await sendChatMessage(messageText, isInboundMode);
            let fullResponse = '';
            
            // Add empty bot message that we'll update
            setMessages(prev => [...prev, { role: 'model', parts: [{ text: '' }] }]);

            // Stream the response with typing animation
            for await (const chunk of stream) {
                const chunkText = chunk.text;
                fullResponse += chunkText;
                
                // Update the last message with accumulated text
                setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMessage = newMessages[newMessages.length - 1];
                    lastMessage.parts[0].text = fullResponse;
                    return newMessages;
                });
            }

            // Trigger avatar to speak the complete response
            if ((window as any).avatarSpeak && fullResponse.trim()) {
                console.log('Triggering avatar to speak:', fullResponse);
                (window as any).avatarSpeak(fullResponse);
            }

        } catch (error) {
            const errorMessage = handleApiError(error);
            setMessages(prev => [...prev, { role: 'model', parts: [{ text: errorMessage }] }]);
        } finally {
            setIsLoading(false);
        }
    }, [isLoading, isInboundMode]);

    return { messages, isLoading, sendMessage };
};
