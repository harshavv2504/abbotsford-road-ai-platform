import { API_BASE_URL } from '../config/api';

let sessionId = `session_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;

export const initChat = () => {
  // Generate new session ID
  sessionId = `session_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
  console.log('New chat session initialized:', sessionId);
};

export const clearSession = () => {
  // Clear the current session
  sessionId = `session_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
  console.log('Chat session cleared and reset:', sessionId);
};

// Get user info from localStorage
const getUser = () => {
  const userStr = localStorage.getItem('user');
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
};

// Stream response from backend
async function* streamResponse(message: string, isLoggedIn: boolean): AsyncGenerator<{ text: string }> {
  try {
    const endpoint = isLoggedIn ? '/chat/inbound/message' : '/chat/outbound/message';
    const user = getUser();
    
    const requestBody: any = {
      session_id: sessionId,
      message: message,
    };
    
    // Add user_id if logged in
    if (isLoggedIn && user) {
      requestBody.user_id = user.id;
    }
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    const botResponse = data.response;

    // Simulate streaming by yielding words
    const words = botResponse.split(' ');
    for (let i = 0; i < words.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 50));
      yield { text: words[i] + (i < words.length - 1 ? ' ' : '') };
    }
  } catch (error) {
    console.error('Error calling backend:', error);
    yield { text: 'Sorry, I encountered an error. Please try again.' };
  }
}

export const sendMessage = (message: string, isLoggedIn: boolean) => {
  return streamResponse(message, isLoggedIn);
};

export const transcribeAudio = async (base64Audio: string, mimeType: string) => {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/transcribe`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        audio: base64Audio,
        mime_type: mimeType,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.transcription;
  } catch (error) {
    console.error('Error transcribing audio:', error);
    return 'Audio transcription failed. Please try again.';
  }
};

// Helper to convert Blob to Base64
export const blobToBase64 = (blob: Blob): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64String = reader.result?.toString().split(',')[1];
      if (base64String) {
        resolve(base64String);
      } else {
        reject(new Error('Failed to convert blob to base64'));
      }
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
};
