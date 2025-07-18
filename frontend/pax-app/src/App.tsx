import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FaMicrophone, 
  FaMicrophoneSlash, 
  FaPaperPlane, 
  FaPhone,
  FaUser,
  FaCar
} from 'react-icons/fa';
import axios from 'axios';
import { API_ENDPOINTS, CONFIG } from './config';

// Types
interface Message {
  id: string;
  text: string;
  sender: 'driver' | 'passenger' | 'ai';
  timestamp: string;
  type: 'text' | 'call';
  callDetails?: {
    duration: number;
    status: string;
  };
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message: string;
}

interface SpeechRecognitionResult {
  transcript: string;
  confidence: number;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface VoiceRecognition extends EventTarget {
  start(): void;
  stop(): void;
  abort(): void;
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onstart: ((this: VoiceRecognition, ev: Event) => any) | null;
  onend: ((this: VoiceRecognition, ev: Event) => any) | null;
  onerror: ((this: VoiceRecognition, ev: SpeechRecognitionErrorEvent) => any) | null;
  onresult: ((this: VoiceRecognition, ev: SpeechRecognitionEvent) => any) | null;
}

declare global {
  interface Window {
    SpeechRecognition: new () => VoiceRecognition;
    webkitSpeechRecognition: new () => VoiceRecognition;
  }
}

// Styled Components (same as DAX app)
const AppContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
`;

const Header = styled.header`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  padding: 1rem;
  text-align: center;
  color: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
`;

const Title = styled.h1`
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
`;

const Subtitle = styled.p`
  margin: 0.5rem 0 0 0;
  font-size: 0.9rem;
  opacity: 0.8;
`;

const MainContent = styled.main`
  flex: 1;
  display: flex;
  flex-direction: column;
  max-width: 600px;
  margin: 0 auto;
  width: 100%;
  padding: 1rem;
`;

const BookingCodeInput = styled.div`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  padding: 1rem;
  margin-bottom: 1rem;
  display: flex;
  gap: 0.5rem;
  align-items: center;
`;

const Input = styled.input`
  flex: 1;
  padding: 0.75rem;
  border: none;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.9);
  font-size: 1rem;
  outline: none;
  
  &:focus {
    box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.3);
  }
`;

const ChatContainer = styled.div`
  flex: 1;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  padding: 1rem;
  margin-bottom: 1rem;
  overflow-y: auto;
  max-height: 60vh;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const MessageBubble = styled(motion.div)<{ $isOwn: boolean }>`
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  justify-content: ${props => props.$isOwn ? 'flex-end' : 'flex-start'};
`;

const MessageContent = styled.div<{ $isOwn: boolean }>`
  background: ${props => props.$isOwn ? 'rgba(255, 255, 255, 0.9)' : 'rgba(255, 255, 255, 0.2)'};
  color: ${props => props.$isOwn ? '#333' : 'white'};
  padding: 0.75rem 1rem;
  border-radius: 18px;
  max-width: 70%;
  word-break: break-word;
  white-space: pre-wrap;
  position: relative;
  
  ${props => props.$isOwn ? `
    border-bottom-right-radius: 5px;
  ` : `
    border-bottom-left-radius: 5px;
  `}
`;

const MessageTime = styled.div`
  font-size: 0.7rem;
  opacity: 0.7;
  margin-top: 0.25rem;
`;

const Avatar = styled.div<{ $type: 'driver' | 'passenger' | 'ai' }>`
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: ${props => {
    switch (props.$type) {
      case 'driver': return 'rgba(255, 255, 255, 0.9)';
      case 'passenger': return 'rgba(255, 255, 255, 0.7)';
      case 'ai': return 'rgba(255, 255, 255, 0.8)';
      default: return 'rgba(255, 255, 255, 0.5)';
    }
  }};
  color: #333;
  font-size: 0.8rem;
  font-weight: bold;
`;

const InputContainer = styled.div`
  display: flex;
  gap: 0.5rem;
  align-items: center;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 25px;
  padding: 0.5rem;
`;

const TextInput = styled.input`
  flex: 1;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.9);
  font-size: 1rem;
  outline: none;
  
  &:focus {
    box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.3);
  }
`;

const Button = styled(motion.button)`
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  color: #333;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 1.2rem;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 1);
    transform: scale(1.05);
  }
  
  &:active {
    transform: scale(0.95);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const VoiceButton = styled(Button)<{ $isListening: boolean }>`
  background: ${props => props.$isListening ? 'rgba(255, 100, 100, 0.9)' : 'rgba(255, 255, 255, 0.9)'};
  color: ${props => props.$isListening ? 'white' : '#333'};
`;

const StatusMessage = styled.div`
  text-align: center;
  color: white;
  font-size: 0.9rem;
  opacity: 0.8;
  margin: 0.5rem 0;
`;

const CallIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 100, 100, 0.2);
  padding: 0.5rem 1rem;
  border-radius: 10px;
  color: white;
  font-size: 0.9rem;
`;

const CallOverlay = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
`;

const CallCard = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 2rem;
  text-align: center;
  max-width: 400px;
  width: 90%;
`;

const CallStatus = styled.div<{ $status: string }>`
  font-size: 1.2rem;
  font-weight: bold;
  color: ${props => {
    switch (props.$status) {
      case 'calling': return '#ff6b6b';
      case 'ringing': return '#4ecdc4';
      case 'connected': return '#45b7d1';
      default: return '#333';
    }
  }};
  margin-bottom: 1rem;
`;

const CallDuration = styled.div`
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
  margin: 1rem 0;
`;

const CallButtons = styled.div`
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 1rem;
`;

const CallButton = styled.button<{ $type: 'accept' | 'reject' | 'end' }>`
  width: 60px;
  height: 60px;
  border: none;
  border-radius: 50%;
  background: ${props => {
    switch (props.$type) {
      case 'accept': return '#4ecdc4';
      case 'reject': return '#ff6b6b';
      case 'end': return '#ff6b6b';
    }
  }};
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:hover {
    transform: scale(1.1);
  }
`;

// App Component
const App: React.FC = () => {
  const [bookingCode, setBookingCode] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState<string>('');
  const [isListening, setIsListening] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [recognition, setRecognition] = useState<VoiceRecognition | null>(null);
  const [statusMessage, setStatusMessage] = useState('');
  const [callState, setCallState] = useState<'idle' | 'calling' | 'ringing' | 'connected' | 'ended'>('idle');
  const [callDuration, setCallDuration] = useState(0);
  const [callButtons, setCallButtons] = useState<('accept' | 'reject' | 'end' | 'cancel')[]>([]);
  
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const connectionRef = useRef({ isConnected: false, bookingCode: '' });
  const websocketRef = useRef<WebSocket | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize speech recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';
      
      recognition.onstart = () => {
        setIsListening(true);
        setStatusMessage('Listening...');
      };
      
      recognition.onend = () => {
        setIsListening(false);
        setStatusMessage('');
      };
      
      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        console.error('Error details:', event);
        setIsListening(false);
        setStatusMessage(`Voice recognition error: ${event.error}. Please try again.`);
      };
      
      recognition.onresult = (event) => {
        console.log('Speech recognition result:', event);
        console.log('Results length:', event.results.length);
        
        if (event.results.length > 0) {
          const result = event.results[0];
          console.log('First result:', result);
          
          // Try different ways to access transcript
          let transcript = null;
          
          // Method 1: Direct transcript property
          if (result.transcript) {
            transcript = result.transcript;
            console.log('Found transcript via result.transcript');
          }
          // Method 2: Access via index if it's an array-like object
          else if ((result as any)[0] && (result as any)[0].transcript) {
            transcript = (result as any)[0].transcript;
            console.log('Found transcript via result[0].transcript');
          }
          // Method 3: Try to access the first item
          else if (typeof (result as any).item === 'function') {
            const firstItem = (result as any).item(0);
            if (firstItem && firstItem.transcript) {
              transcript = firstItem.transcript;
              console.log('Found transcript via result.item(0).transcript');
            }
          }
          // Method 4: Try to iterate through results
          else {
            for (let i = 0; i < (result as any).length; i++) {
              const item = (result as any)[i];
              if (item && item.transcript) {
                transcript = item.transcript;
                console.log(`Found transcript via result[${i}].transcript`);
                break;
              }
            }
          }
          
          if (transcript) {
            console.log('Voice transcript:', transcript);
            
            // Check if connected before processing voice command
            console.log('🔍 DEBUG: Connection check - isConnected:', connectionRef.current.isConnected, 'bookingCode:', connectionRef.current.bookingCode);
            if (!connectionRef.current.isConnected || !connectionRef.current.bookingCode) {
              console.log('❌ DEBUG: Voice recognition triggered but not connected');
              setStatusMessage('Please connect to a booking first by entering the booking code.');
              return;
            }
            
            setStatusMessage('Processing voice command...');
            
            // Use AI agent to process voice command
            processVoiceCommand(transcript);
          } else {
            console.log('No transcript found in any method');
            console.log('Available properties:', Object.keys(result));
            setStatusMessage('No speech detected. Please try again.');
          }
        } else {
          console.log('No results in event');
          setStatusMessage('No speech detected. Please try again.');
        }
      };
      
      setRecognition(recognition);
    } else {
      setStatusMessage('Voice recognition not supported in this browser.');
    }
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  // Poll for new messages
  useEffect(() => {
    if (!isConnected || !bookingCode) return;

    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_ENDPOINTS.GET_MESSAGES}/${bookingCode}`);
        if (response.data.success) {
          const newMessages = response.data.data.messages || [];
          // Merge messages instead of overwriting
          setMessages(prevMessages => {
            const existingIds = new Set(prevMessages.map((m: Message) => m.id));
            const uniqueNewMessages = newMessages.filter((m: any) => !existingIds.has(m.id));
            return [...prevMessages, ...uniqueNewMessages];
          });
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 3000); // Poll every 3 seconds

    return () => clearInterval(pollInterval);
  }, [isConnected, bookingCode]);

  // WebSocket connection for real-time call updates
  useEffect(() => {
    if (isConnected && bookingCode) {
      const wsUrl = CONFIG.getWebsocketUrlForBooking(bookingCode);
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('🔌 WebSocket connected for calls');
        // Register WebSocket connection with Lambda
        ws.send(JSON.stringify({
          action: 'register',
          booking_code: bookingCode,
          user_type: 'passenger'
        }));
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('📨 WebSocket message received:', data);
        
        if (data.type === 'call_state_update') {
          // Handle call state updates from Lambda
          const { call_state, user_type, message, show_buttons } = data;
          
          setCallState(call_state);
          setStatusMessage(message);
          
          // Update call buttons based on user type and state
          if (call_state === 'calling' && user_type === 'passenger') {
            // Passenger is calling - show cancel button
            setCallButtons(['cancel']);
          } else if (call_state === 'ringing' && user_type === 'passenger') {
            // Passenger is being called - show accept/reject buttons
            setCallButtons(['accept', 'reject']);
          } else if (call_state === 'connected') {
            // Call is connected - show end button for both
            setCallButtons(['end']);
          } else if (call_state === 'ended') {
            // Call ended - no buttons
            setCallButtons([]);
            setTimeout(() => {
              setCallState('idle');
              setCallDuration(0);
            }, 2000);
          }
        } else if (data.type === 'message') {
          // Handle incoming messages
          const newMessage: Message = {
            id: data.id || Date.now().toString(),
            text: data.message,
            sender: data.sender,
            timestamp: data.timestamp || new Date().toISOString(),
            type: 'text'
          };
          setMessages(prev => [...prev, newMessage]);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
      };
      
      websocketRef.current = ws;
      
      return () => {
        ws.close();
      };
    }
  }, [isConnected, bookingCode]);

  // Connect to booking
  const connectToBooking = async () => {
    if (!(bookingCode || '').trim()) {
      setStatusMessage('Please enter a booking code.');
      return;
    }

    try {
      setStatusMessage('Connecting to booking...');
      
      // Test connection by getting messages
      const response = await axios.get(`${API_ENDPOINTS.GET_MESSAGES}/${bookingCode}`);
      
      if (response.data.success) {
        setIsConnected(true);
        setMessages(response.data.data.messages || []);
        setStatusMessage('Connected successfully!');
        
        // Update connection ref
        connectionRef.current = { isConnected: true, bookingCode: bookingCode };
        
        // Add welcome message
        const welcomeMessage: Message = {
          id: Date.now().toString(),
          text: `Welcome to booking ${bookingCode}! You can now chat with your driver.`,
          sender: 'ai',
          timestamp: new Date().toISOString(),
          type: 'text'
        };
        setMessages(prev => [...prev, welcomeMessage]);
      }
    } catch (error) {
      console.error('Connection error:', error);
      setStatusMessage('Failed to connect. Please check your booking code.');
    }
  };

  // Send message
  const sendMessage = async () => {
    console.log('Send message called with inputText:', inputText);
    if (!(inputText || '').trim() || !isConnected) {
      console.log('Send message blocked - inputText:', inputText, 'isConnected:', isConnected);
      return;
    }

    const newMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      sender: 'passenger',
      timestamp: new Date().toISOString(),
      type: 'text'
    };

    console.log('Adding message to UI:', newMessage);
    setMessages(prev => [...prev, newMessage]);
    setInputText('');
    setStatusMessage('Sending message...');

    try {
      const response = await axios.post(API_ENDPOINTS.SEND_MESSAGE, {
        booking_code: bookingCode,
        message: inputText,
        sender: 'passenger'
      });

      if (response.data.success) {
        setStatusMessage('Message sent successfully!');
        
        // Add AI response
        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          text: 'Message sent successfully. The driver will be notified.',
          sender: 'ai',
          timestamp: new Date().toISOString(),
          type: 'text'
        };
        setMessages(prev => [...prev, aiResponse]);
      }
    } catch (error) {
      console.error('Send message error:', error);
      setStatusMessage('Failed to send message. Please try again.');
    }
  };

  // Make call
  const makeCall = async () => {
    if (!isConnected) return;

    setStatusMessage('Initiating call...');
    setCallState('calling');
    setCallButtons(['cancel']);

    try {
      const response = await axios.post(API_ENDPOINTS.MAKE_CALL, {
        booking_code: bookingCode,
        caller_type: 'passenger',
        call_type: 'voice',
        action: 'initiate',
        duration: 0
      });

      if (response.data.success) {
        const callMessage: Message = {
          id: Date.now().toString(),
          text: 'Call initiated successfully',
          sender: 'ai',
          timestamp: new Date().toISOString(),
          type: 'call',
          callDetails: {
            duration: 0,
            status: 'initiated'
          }
        };
        setMessages(prev => [...prev, callMessage]);
        setStatusMessage('Calling driver...');
      }
    } catch (error) {
      console.error('Make call error:', error);
      setStatusMessage('Failed to initiate call. Please try again.');
      setCallState('idle');
      setCallButtons([]);
    }
  };

  // Start voice recognition
  const startListening = () => {
    if (recognition && !isListening) {
      recognition.start();
    }
  };

  // Process voice command using AI agent
  const processVoiceCommand = async (transcript: string) => {
    console.log('🔍 DEBUG: processVoiceCommand called with:', transcript);
    console.log('🔍 DEBUG: isConnected:', connectionRef.current.isConnected, 'bookingCode:', connectionRef.current.bookingCode);
    
    // Only process voice commands if already connected
    if (!connectionRef.current.isConnected || !connectionRef.current.bookingCode) {
      console.log('❌ DEBUG: Not connected to booking');
      setStatusMessage('Please connect to a booking first by entering the booking code.');
      return;
    }

    // If connected, process with AI
    await processVoiceCommandWithAI(transcript, connectionRef.current.bookingCode);
  };

  // Helper function to process voice command with AI
  const processVoiceCommandWithAI = async (transcript: string, bookingCode: string) => {
    try {
      console.log('Processing voice command:', transcript);
      
      const response = await axios.post(API_ENDPOINTS.AI_AGENT, {
        booking_code: bookingCode,
        user_input: transcript,
        user_type: 'passenger'
      });

      if (response.data.success) {
        console.log('AI agent response:', response.data);
        
        // Check if this is a call command
        if (response.data.data.type === 'call') {
          console.log('📞 DEBUG: Call command detected');
          handleCallCommand();
        } else {
          // Add AI response to chat
          const aiMessage: Message = {
            id: Date.now().toString(),
            text: `AI processed: "${transcript}" → "${response.data.data.text}"`,
            sender: 'ai',
            timestamp: new Date().toISOString(),
            type: 'text'
          };
          
          setMessages(prev => [...prev, aiMessage]);
          setStatusMessage('Voice command processed successfully!');
        }
      }
    } catch (error) {
      console.error('AI agent error:', error);
      setStatusMessage('Failed to process voice command. Please try again.');
    }
  };

  // Handle call command
  const handleCallCommand = () => {
    // Reset call state and duration
    setCallState('calling');
    setCallDuration(0);
    setCallButtons(['cancel']);
    setStatusMessage('Initiating call...');
    
    // Call the make_call API
    makeCall();
  };

  // Start call timer
  const startCallTimer = () => {
    // Clear any existing timer
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    
    // Reset duration
    setCallDuration(0);
    
    const interval = setInterval(() => {
      setCallDuration(prev => prev + 1);
    }, 1000);
    
    // Store interval ID for cleanup
    timerRef.current = interval;
    
    return () => clearInterval(interval);
  };

  // End call
  const endCall = async () => {
    // Clear timer
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    
    setCallState('ended');
    setStatusMessage(`Call ended - Duration: ${callDuration} seconds`);
    setCallButtons([]);
    
    // Call the make_call API to end the call
    try {
      const response = await axios.post(API_ENDPOINTS.MAKE_CALL, {
        booking_code: bookingCode,
        caller_type: 'passenger',
        call_type: 'voice',
        action: 'end',
        duration: callDuration
      });

      if (response.data.success) {
        const callMessage: Message = {
          id: Date.now().toString(),
          text: `Call ended - Duration: ${callDuration} seconds`,
          sender: 'ai',
          timestamp: new Date().toISOString(),
          type: 'call',
          callDetails: {
            duration: callDuration,
            status: 'ended'
          }
        };
        setMessages(prev => [...prev, callMessage]);
      }
    } catch (error) {
      console.error('End call error:', error);
    }
    
    setTimeout(() => {
      setCallState('idle');
      setCallDuration(0);
    }, 2000);
  };

  // Accept call
  const acceptCall = async () => {
    setCallState('connected');
    setStatusMessage('Call accepted');
    setCallButtons(['end']);
    startCallTimer();
    
    // Call the make_call API to accept the call
    try {
      const response = await axios.post(API_ENDPOINTS.MAKE_CALL, {
        booking_code: bookingCode,
        caller_type: 'passenger',
        call_type: 'voice',
        action: 'accept',
        duration: 0
      });

      if (response.data.success) {
        const callMessage: Message = {
          id: Date.now().toString(),
          text: 'Call accepted',
          sender: 'ai',
          timestamp: new Date().toISOString(),
          type: 'call',
          callDetails: {
            duration: 0,
            status: 'connected'
          }
        };
        setMessages(prev => [...prev, callMessage]);
      }
    } catch (error) {
      console.error('Accept call error:', error);
    }
  };

  // Reject call
  const rejectCall = async () => {
    setCallState('ended');
    setStatusMessage('Call rejected');
    setCallButtons([]);
    
    // Call the make_call API to reject the call
    try {
      const response = await axios.post(API_ENDPOINTS.MAKE_CALL, {
        booking_code: bookingCode,
        caller_type: 'passenger',
        call_type: 'voice',
        action: 'reject',
        duration: 0
      });

      if (response.data.success) {
        const callMessage: Message = {
          id: Date.now().toString(),
          text: 'Call rejected',
          sender: 'ai',
          timestamp: new Date().toISOString(),
          type: 'call',
          callDetails: {
            duration: 0,
            status: 'rejected'
          }
        };
        setMessages(prev => [...prev, callMessage]);
      }
    } catch (error) {
      console.error('Reject call error:', error);
    }
    
    setTimeout(() => {
      setCallState('idle');
      setCallDuration(0);
    }, 2000);
  };

  // Cancel call
  const cancelCall = async () => {
    setCallState('ended');
    setStatusMessage('Call cancelled');
    setCallButtons([]);
    
    // Call the make_call API to end the call
    try {
      const response = await axios.post(API_ENDPOINTS.MAKE_CALL, {
        booking_code: bookingCode,
        caller_type: 'passenger',
        call_type: 'voice',
        action: 'end',
        duration: 0
      });

      if (response.data.success) {
        const callMessage: Message = {
          id: Date.now().toString(),
          text: 'Call cancelled',
          sender: 'ai',
          timestamp: new Date().toISOString(),
          type: 'call',
          callDetails: {
            duration: 0,
            status: 'cancelled'
          }
        };
        setMessages(prev => [...prev, callMessage]);
      }
    } catch (error) {
      console.error('Cancel call error:', error);
    }
    
    setTimeout(() => {
      setCallState('idle');
      setCallDuration(0);
    }, 2000);
  };

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Poll for new messages
  useEffect(() => {
    if (!isConnected || !bookingCode) return;

    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_ENDPOINTS.GET_MESSAGES}/${bookingCode}`);
        if (response.data.success) {
          const newMessages = response.data.data.messages || [];
          setMessages(newMessages);
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 3000); // Poll every 3 seconds

    return () => clearInterval(pollInterval);
  }, [isConnected, bookingCode]);

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, []);

  return (
    <AppContainer>
      <Header>
        <Title>PAX - Passenger Assistant</Title>
        <Subtitle>AI-powered chat and voice assistant</Subtitle>
      </Header>

      <MainContent>
        {!isConnected ? (
          <BookingCodeInput>
            <Input
              type="text"
              placeholder="Enter booking code..."
              value={bookingCode}
              onChange={(e) => setBookingCode(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && connectToBooking()}
            />
            <Button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={connectToBooking}
            >
              Connect
            </Button>
          </BookingCodeInput>
        ) : (
          <>
            <ChatContainer ref={chatContainerRef}>
              <AnimatePresence>
                {messages.map((message) => (
                  <MessageBubble
                    key={message.id}
                    $isOwn={message.sender === 'passenger'}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.3 }}
                  >
                    {message.sender !== 'passenger' && (
                      <Avatar $type={message.sender}>
                        {message.sender === 'driver' ? <FaCar /> : <FaUser />}
                      </Avatar>
                    )}
                    <div>
                      <MessageContent $isOwn={message.sender === 'passenger'}>
                        {message.type === 'call' ? (
                          <CallIndicator>
                            <FaPhone />
                            {message.text}
                          </CallIndicator>
                        ) : (
                          message.text
                        )}
                      </MessageContent>
                      <MessageTime>
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </MessageTime>
                    </div>
                    {message.sender === 'passenger' && (
                      <Avatar $type={message.sender}>
                        <FaUser />
                      </Avatar>
                    )}
                  </MessageBubble>
                ))}
              </AnimatePresence>
            </ChatContainer>

            <InputContainer>
              <TextInput
                ref={inputRef}
                type="text"
                placeholder="Type a message or use voice..."
                value={inputText || ''}
                onChange={(e) => setInputText(e.target.value || '')}
                onKeyPress={handleKeyPress}
                disabled={!isConnected}
              />
              <VoiceButton
                $isListening={isListening}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={startListening}
                disabled={!isConnected || isListening}
              >
                {isListening ? <FaMicrophoneSlash /> : <FaMicrophone />}
              </VoiceButton>
              <Button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={sendMessage}
                disabled={!(inputText || '').trim() || !isConnected}
              >
                <FaPaperPlane />
              </Button>
              <Button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={makeCall}
                disabled={!isConnected}
              >
                <FaPhone />
              </Button>
            </InputContainer>
          </>
        )}

        {statusMessage && (
          <StatusMessage>{statusMessage}</StatusMessage>
        )}
      </MainContent>

      {/* Call Overlay */}
      {callState !== 'idle' && (
        <CallOverlay
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <CallCard>
            <CallStatus $status={callState}>
              {callState === 'calling' && 'Calling...'}
              {callState === 'ringing' && 'Ringing...'}
              {callState === 'connected' && 'Connected'}
              {callState === 'ended' && 'Call Ended'}
            </CallStatus>
            
            {callState === 'connected' && (
              <CallDuration>
                {Math.floor(callDuration / 60)}:{(callDuration % 60).toString().padStart(2, '0')}
              </CallDuration>
            )}
            
            <CallButtons>
              {callButtons.includes('cancel') && (
                <CallButton $type="end" onClick={cancelCall}>
                  <FaMicrophoneSlash />
                </CallButton>
              )}
              {callButtons.includes('accept') && (
                <CallButton $type="accept" onClick={acceptCall}>
                  <FaPhone />
                </CallButton>
              )}
              {callButtons.includes('reject') && (
                <CallButton $type="reject" onClick={rejectCall}>
                  <FaMicrophoneSlash />
                </CallButton>
              )}
              {callButtons.includes('end') && (
                <CallButton $type="end" onClick={endCall}>
                  <FaMicrophoneSlash />
                </CallButton>
              )}
            </CallButtons>
          </CallCard>
        </CallOverlay>
      )}
    </AppContainer>
  );
};

export default App; 