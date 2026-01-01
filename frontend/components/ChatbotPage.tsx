import React, { useRef } from 'react';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import { ChatMessageArea } from './ChatMessageArea';
import { ChatInput } from './ChatInput';
import { AvatarVideo } from './AvatarVideo';
import { ChatMessage } from '../types';

interface ChatbotPageProps {
    isLoggedIn: boolean;
    isChatVisible: boolean;
    isAvatarVisible: boolean;
    messages: ChatMessage[];
    isLoading: boolean;
    sendMessage: (message: string) => void;
}

export const ChatbotPage: React.FC<ChatbotPageProps> = React.memo(({ isLoggedIn, isChatVisible, isAvatarVisible, messages, isLoading, sendMessage }) => {
    const [transcribedText, setTranscribedText] = React.useState<string>('');
    const { isRecording, statusMessage, handleMicClick } = useAudioRecorder({
        onTranscriptionComplete: async (text: string) => {
            setTranscribedText(text);
        },
    });
    const videoRef = useRef<HTMLVideoElement>(null);

    // Speak the initial greeting when avatar connects
    const handleAvatarReady = React.useCallback(() => {
        console.log('Avatar is ready!');
        if (messages.length > 0 && messages[0].role === 'model') {
            const initialMessage = messages[0].parts[0].text;
            console.log('Speaking initial message:', initialMessage);
            // Add a small delay to ensure avatar is fully ready to speak
            setTimeout(() => {
                if ((window as any).avatarSpeak) {
                    console.log('Attempting to speak initial message now');
                    (window as any).avatarSpeak(initialMessage);
                } else {
                    console.error('avatarSpeak not available');
                }
            }, 300);
        }
    }, [messages]);

    return (
        <div 
            className="w-full h-full md:h-auto md:max-w-7xl md:max-h-[calc(100vh-12rem)] md:mx-auto md:aspect-[16/9] md:rounded-2xl md:shadow-2xl relative overflow-hidden md:border md:border-gray-200"
            style={{
                backgroundImage: 'url(/abbotsford-red-hook.png)',
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                backgroundRepeat: 'no-repeat'
            }}
        >
            {/* Avatar Video Background */}
            <AvatarVideo
                ref={videoRef}
                isVisible={isAvatarVisible}
                onAvatarReady={handleAvatarReady}
            />

            {/* Black Transparent Overlay - Only show when avatar is not visible */}
            {!isAvatarVisible && <div className="absolute inset-0 bg-black/40 z-[5]"></div>}

            {/* Chat Interface Overlay */}
            <div className="absolute inset-0 flex flex-col z-10">
                {isChatVisible && <ChatMessageArea messages={messages} />}
                <ChatInput
                    isLoading={isLoading}
                    isRecording={isRecording}
                    statusMessage={statusMessage}
                    onSendMessage={sendMessage}
                    onMicClick={handleMicClick}
                    transcribedText={transcribedText}
                    onTranscribedTextUsed={() => setTranscribedText('')}
                />
            </div>
        </div>
    );
});

ChatbotPage.displayName = 'ChatbotPage';