import { useState, useRef } from 'react';
import { transcribeAudio, blobToBase64 } from '../services/chatService';
import { handleApiError } from '../utils/errorUtils';

interface UseAudioRecorderProps {
  onTranscriptionComplete: (text: string) => Promise<void>;
}

export const useAudioRecorder = ({ onTranscriptionComplete }: UseAudioRecorderProps) => {
  const [isRecording, setIsRecording] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        setStatusMessage('Transcribing...');
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        try {
            const base64Audio = await blobToBase64(audioBlob);
            const mimeType = audioBlob.type;
            const transcribedText = await transcribeAudio(base64Audio, mimeType);
            if (transcribedText) {
                setStatusMessage('');
                await onTranscriptionComplete(transcribedText);
            } else {
                setStatusMessage('Transcription failed. Please try again.');
            }
        } catch(e) {
            const errorMessage = handleApiError(e);
            setStatusMessage(errorMessage);
        } finally {
            stream.getTracks().forEach(track => track.stop());
        }
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setStatusMessage('Recording...');
    } catch (err) {
      console.error("Error accessing microphone:", err);
      setStatusMessage('Microphone access denied.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleMicClick = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return { isRecording, statusMessage, handleMicClick };
};
