import React, { forwardRef, useEffect, useState, useRef, useCallback } from 'react';
import StreamingAvatar, {
    StreamingEvents,
    AvatarQuality,
    VoiceEmotion,
    TaskType,
    TaskMode
} from '@heygen/streaming-avatar';
import { ConnectionQuality } from '@heygen/streaming-avatar';
import { HEYGEN_API_URL } from '../config/api';

enum SessionState {
    INACTIVE = 'inactive',
    CONNECTING = 'connecting',
    CONNECTED = 'connected',
    DISCONNECTED = 'disconnected',
    ERROR = 'error'
}

interface AvatarVideoProps {
    isVisible: boolean;
    onAvatarReady?: () => void;
}

export const AvatarVideo = forwardRef<HTMLVideoElement, AvatarVideoProps>(
    ({ isVisible, onAvatarReady }, ref) => {
        const [sessionState, setSessionState] = useState<SessionState>(SessionState.INACTIVE);
        const [connectionError, setConnectionError] = useState<string | null>(null);
        const [connectionQuality, setConnectionQuality] = useState<ConnectionQuality>(ConnectionQuality.UNKNOWN);

        const avatarRef = useRef<StreamingAvatar | null>(null);
        const sessionIdRef = useRef<string | null>(null);

        // Handle stream ready
        const handleStream = useCallback(({ detail }: { detail: MediaStream }) => {
            console.log('[Avatar] Stream ready, tracks:', detail.getTracks().length);
            if (ref && 'current' in ref && ref.current) {
                ref.current.srcObject = detail;
                ref.current.muted = true; // Start muted to allow autoplay
                ref.current.onloadedmetadata = () => {
                    console.log('[Avatar] Video metadata loaded, attempting play');
                    ref.current?.play()
                        .then(() => {
                            console.log('[Avatar] Video playing');
                            // Unmute after successful play
                            if (ref.current) {
                                ref.current.muted = false;
                            }
                        })
                        .catch(e => console.error('[Avatar] Video play error:', e));
                };
            } else {
                console.error('[Avatar] Video ref not available');
            }
            setSessionState(SessionState.CONNECTED);
            setConnectionError(null);
            onAvatarReady?.();
        }, [ref, onAvatarReady]);

        // Stop avatar
        const stopAvatar = useCallback(async () => {
            if (!avatarRef.current) return;

            avatarRef.current.off(StreamingEvents.STREAM_READY, handleStream);
            avatarRef.current.off(StreamingEvents.STREAM_DISCONNECTED, stopAvatar);

            try {
                await avatarRef.current.stopAvatar();
            } catch (error) {
                // Suppress 401 errors during cleanup - token may have expired
                console.log('[Avatar] Cleanup completed');
            }
            avatarRef.current = null;
            setSessionState(SessionState.INACTIVE);
            sessionIdRef.current = null;
        }, [handleStream]);

        // Start avatar
        const startAvatar = useCallback(async () => {
            if (sessionState !== SessionState.INACTIVE) {
                console.log('[Avatar] Session already active');
                return;
            }

            try {
                setSessionState(SessionState.CONNECTING);

                // Get token from your backend
                const response = await fetch(`${HEYGEN_API_URL}/api/heygen/token`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });

                if (!response.ok) {
                    throw new Error(`Failed to get token: ${response.status}`);
                }

                const data = await response.json();
                const token = data.token;
                const avatarId = data.avatarId || "SilasHR_public";

                if (!token) {
                    throw new Error('No token received');
                }

                // Initialize avatar
                avatarRef.current = new StreamingAvatar({ token });

                // Set up event listeners
                avatarRef.current.on(StreamingEvents.STREAM_READY, handleStream);
                avatarRef.current.on(StreamingEvents.STREAM_DISCONNECTED, stopAvatar);
                avatarRef.current.on(StreamingEvents.CONNECTION_QUALITY_CHANGED, ({ detail }: { detail: ConnectionQuality }) => {
                    setConnectionQuality(detail);
                });

                // Start session
                const sessionInfo = await avatarRef.current.createStartAvatar({
                    quality: AvatarQuality.High,
                    avatarName: avatarId,
                    knowledgeId: undefined, // Disable knowledge base - use our own chat
                    voice: {
                        rate: 1.0,
                        emotion: VoiceEmotion.FRIENDLY
                    },
                    language: "en",
                    activityIdleTimeout: 600,
                    useSilencePrompt: false
                });

                sessionIdRef.current = sessionInfo.session_id;
                console.log('[Avatar] Session started:', sessionInfo.session_id);

            } catch (error) {
                console.error('[Avatar] Failed to start:', error);
                setSessionState(SessionState.ERROR);
                setConnectionError(error instanceof Error ? error.message : 'Failed to connect');
                avatarRef.current = null;
            }
        }, [sessionState, handleStream, stopAvatar]);

        const speak = useCallback((text: string) => {
            if (avatarRef.current && sessionState === SessionState.CONNECTED) {
                console.log('[Avatar] Speaking:', text.substring(0, 50) + '...');
                avatarRef.current.speak({
                    text,
                    task_type: TaskType.REPEAT,  // Just repeat the text, don't use knowledge base
                    taskMode: TaskMode.ASYNC      // Don't block, allow concurrent processing
                }).catch(err => {
                    console.error('[Avatar] Speak failed:', err);
                });
            }
        }, [sessionState]);

        // Expose speak function globally
        useEffect(() => {
            (window as any).avatarSpeak = speak;
            return () => {
                delete (window as any).avatarSpeak;
            };
        }, [speak]);

        // Keep-alive mechanism to prevent session timeout
        useEffect(() => {
            if (sessionState !== SessionState.CONNECTED) return;

            console.log('[Avatar] Starting keep-alive mechanism');
            const keepAliveInterval = setInterval(() => {
                if (avatarRef.current) {
                    console.log('[Avatar] Sending keep-alive ping');
                    avatarRef.current.keepAlive().catch(err => {
                        console.error('[Avatar] Keep-alive failed:', err);
                    });
                }
            }, 60000); // Every 60 seconds

            return () => {
                console.log('[Avatar] Stopping keep-alive mechanism');
                clearInterval(keepAliveInterval);
            };
        }, [sessionState]);

        // Start avatar when visible, stop when hidden
        useEffect(() => {
            if (isVisible && sessionState === SessionState.INACTIVE) {
                startAvatar();
            } else if (!isVisible && sessionState !== SessionState.INACTIVE) {
                stopAvatar();
            }
        }, [isVisible]);

        // Cleanup on unmount
        useEffect(() => {
            return () => {
                if (avatarRef.current) {
                    stopAvatar();
                }
            };
        }, []);

        if (!isVisible) {
            return null;
        }

        const isConnected = sessionState === SessionState.CONNECTED;
        const isConnecting = sessionState === SessionState.CONNECTING;
        const hasError = sessionState === SessionState.ERROR;

        return (
            <div className="absolute inset-0 w-full h-full bg-black">
                <video
                    ref={ref}
                    autoPlay
                    playsInline
                    className="w-full h-full object-cover"
                />

                {isConnected && connectionQuality !== ConnectionQuality.UNKNOWN && (
                    <div className="absolute top-4 right-4 z-10">
                        <div className={`px-3 py-1 rounded-full text-xs font-medium ${connectionQuality === ConnectionQuality.GOOD ? 'bg-green-500/80 text-white' : 'bg-red-500/80 text-white'
                            }`}>
                            {connectionQuality === ConnectionQuality.GOOD ? '● Good' : '● Poor'}
                        </div>
                    </div>
                )}

                {!isConnected && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/70 backdrop-blur-sm">
                        <div className="text-center text-white max-w-md px-6">
                            {isConnecting ? (
                                <div>
                                    <div className="mb-4">
                                        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
                                    </div>
                                    <div className="text-xl mb-2">Connecting to Avatar...</div>
                                </div>
                            ) : hasError ? (
                                <div>
                                    <div className="text-xl mb-4 text-red-300">{connectionError || 'Connection failed'}</div>
                                    <button
                                        onClick={startAvatar}
                                        className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors font-medium"
                                    >
                                        Retry Connection
                                    </button>
                                </div>
                            ) : (
                                <div className="text-xl">Initializing...</div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        );
    }
);

AvatarVideo.displayName = 'AvatarVideo';