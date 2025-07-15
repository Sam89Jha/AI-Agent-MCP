import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FaMicrophone, 
  FaMicrophoneSlash, 
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

// Styled Components
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

const VoiceControlContainer = styled.div`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: center;
`;

const VoiceButton = styled(motion.button)<{ $isListening: boolean }>`
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: none;
  background: ${props => props.$isListening ? 'rgba(255, 100, 100, 0.9)' : 'rgba(255, 255, 255, 0.9)'};
  color: ${props => props.$isListening ? 'white' : '#333'};
  font-size: 2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  
  &:hover {
    transform: scale(1.05);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
  }
  
  &:active {
    transform: scale(0.95);
  }
`;

const StatusMessage = styled.div`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 10px;
  padding: 0.75rem;
  margin-bottom: 1rem;
  text-align: center;
  color: white;
  font-size: 0.9rem;
`;

const CallControls = styled.div`
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  margin-top: 1rem;
`;

const CallButton = styled.button<{ $variant: 'accept' | 'reject' | 'end' | 'cancel' }>`
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  
  background: ${props => {
    switch (props.$variant) {
      case 'accept': return 'rgba(76, 175, 80, 0.9)';
      case 'reject': return 'rgba(244, 67, 54, 0.9)';
      case 'end': return 'rgba(255, 152, 0, 0.9)';
      case 'cancel': return 'rgba(158, 158, 158, 0.9)';
      default: return 'rgba(255, 255, 255, 0.9)';
    }
  }};
  
  color: white;
  
  &:hover {
    transform: scale(1.05);
  }
`;

const CallDuration = styled.div`
  text-align: center;
  font-size: 1.2rem;
  font-weight: bold;
  color: white;
  margin: 1rem 0;
`;

const ConnectButton = styled.button`
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.9);
  color: #333;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 1);
    transform: scale(1.02);
  }
`;

const VoiceInstructions = styled.div`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 10px;
  padding: 1rem;
  margin-bottom: 1rem;
  color: white;
  font-size: 0.9rem;
  text-align: center;
`;

const App: React.FC = () => {
  // State
  const [bookingCode, setBookingCode] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isListening, setIsListening] = useState(false);
  const [statusMessage, setStatusMessage] = useState('Enter booking code to start');
  const [callState, setCallState] = useState<'idle' | 'calling' | 'connected' | 'ended'>('idle');
  const [callDuration, setCallDuration] = useState(0);
  const [callButtons, setCallButtons] = useState<string[]>([]);
  
  // Refs
  const recognition = useRef<VoiceRecognition | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const connectionRef = useRef({ isConnected: false, bookingCode: '' });
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Initialize speech recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (SpeechRecognition) {
      recognition.current = new SpeechRecognition();
      recognition.current.continuous = false;
      recognition.current.interimResults = false;
      recognition.current.lang = 'en-US';
      
      recognition.current.onstart = () => {
        setIsListening(true);
        setStatusMessage('Listening... Speak now!');
      };
      
      recognition.current.onend = () => {
        setIsListening(false);
        setStatusMessage('Voice recognition ended');
      };
      
      recognition.current.onerror = (event: SpeechRecognitionErrorEvent) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        setStatusMessage(`Voice recognition error: ${event.error}`);
      };
      
      recognition.current.onresult = (event: SpeechRecognitionEvent) => {
        const transcript = event.results.item(0).transcript;
        console.log('🎤 Voice input:', transcript);
        setStatusMessage(`Processing: "${transcript}"`);
        processVoiceCommand(transcript);
      };
    } else {
      setStatusMessage('Speech recognition not supported in this browser');
    }
  }, []);

  // Update connection ref when state changes
  useEffect(() => {
    connectionRef.current = { isConnected, bookingCode };
  }, [isConnected, bookingCode]);

  // Auto-scroll chat to bottom
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  // Connect to booking
  const connectToBooking = async () => {
    if (!bookingCode.trim()) {
      setStatusMessage('Please enter a booking code');
      return;
    }

    try {
      setStatusMessage('Connecting to booking...');
      
      // Test AI Intent API health
      const healthResponse = await axios.get(API_ENDPOINTS.HEALTH_CHECK);
      console.log('✅ AI Intent API health check:', healthResponse.data);
      
      setIsConnected(true);
      setStatusMessage(`Connected to booking: ${bookingCode}`);
      
      // Add connection message
      const connectionMessage: Message = {
        id: Date.now().toString(),
        text: `Connected to booking: ${bookingCode}`,
        sender: 'ai',
        timestamp: new Date().toISOString(),
        type: 'text'
      };
      setMessages([connectionMessage]);
      
    } catch (error: any) {
      console.error('Connection error:', error);
      setStatusMessage('Failed to connect. Please check the booking code and try again.');
    }
  };

  // Process voice command using AI Intent API
  const processVoiceCommand = async (transcript: string) => {
    console.log('🔍 Processing voice command:', transcript);
    
    if (!isConnected || !bookingCode) {
      setStatusMessage('Please connect to a booking first by entering the booking code.');
      return;
    }

    try {
      console.log('🚀 Sending to AI Intent API:', API_ENDPOINTS.AI_INTENT_API);
      console.log('📤 Request payload:', {
        booking_code: bookingCode,
        user_input: transcript,
        user_type: 'driver'
      });
      
      const response = await axios.post(API_ENDPOINTS.AI_INTENT_API, {
        booking_code: bookingCode,
        user_input: transcript,
        user_type: 'driver'
      });

      console.log('📥 AI Intent API response:', response.data);

      if (response.data.success) {
        console.log('✅ AI Intent API success');
        
        // Add AI response to chat
        const aiMessage: Message = {
          id: Date.now().toString(),
          text: response.data.response,
          sender: 'ai',
          timestamp: new Date().toISOString(),
          type: 'text'
        };
        
        console.log('💬 Adding AI message to chat:', aiMessage);
        setMessages(prev => [...prev, aiMessage]);
        setStatusMessage('Voice command processed successfully!');
        
        // Handle call commands
        if (response.data.intent === 'make-call') {
          handleCallCommand();
        }
      } else {
        console.log('❌ AI Intent API returned success: false');
        setStatusMessage('Failed to process voice command. Please try again.');
      }
    } catch (error: any) {
      console.error('💥 AI Intent API error:', error);
      console.error('💥 Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      });
      setStatusMessage('Failed to process voice command. Please try again.');
    }
  };

  // Handle call command
  const handleCallCommand = () => {
    setCallState('calling');
    setCallDuration(0);
    setCallButtons(['cancel']);
    setStatusMessage('Initiating call...');
    
    // Add call message
    const callMessage: Message = {
      id: Date.now().toString(),
      text: 'Initiating call...',
      sender: 'ai',
      timestamp: new Date().toISOString(),
      type: 'call'
    };
    setMessages(prev => [...prev, callMessage]);
  };

  // Start voice recognition
  const startListening = () => {
    if (!isConnected || !bookingCode) {
      setStatusMessage('Please connect to a booking first by entering the booking code.');
      return;
    }
    
    if (recognition.current && !isListening) {
      recognition.current.start();
    }
  };

  // Start call timer
  const startCallTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    
    setCallDuration(0);
    
    const interval = setInterval(() => {
      setCallDuration(prev => prev + 1);
    }, 1000);
    
    timerRef.current = interval;
    
    return () => clearInterval(interval);
  };

  // End call
  const endCall = async () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    
    setCallState('ended');
    setStatusMessage(`Call ended - Duration: ${callDuration} seconds`);
    setCallButtons([]);
    
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
  };

  // Reject call
  const rejectCall = async () => {
    setCallState('ended');
    setStatusMessage('Call rejected');
    setCallButtons([]);
    
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
    
    setTimeout(() => {
      setCallState('idle');
    }, 2000);
  };

  // Cancel call
  const cancelCall = async () => {
    setCallState('ended');
    setStatusMessage('Call cancelled');
    setCallButtons([]);
    
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
    
    setTimeout(() => {
      setCallState('idle');
    }, 2000);
  };

  // Format time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <AppContainer>
      <Header>
        <Title>🚗 DAX - Driver Assistant</Title>
        <Subtitle>Voice-Controlled Communication</Subtitle>
      </Header>

      <MainContent>
        {/* Booking Code Input */}
        {!isConnected && (
          <BookingCodeInput>
            <Input
              type="text"
              placeholder="Enter booking code..."
              value={bookingCode}
              onChange={(e) => setBookingCode(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && connectToBooking()}
            />
            <ConnectButton onClick={connectToBooking}>
              Connect
            </ConnectButton>
          </BookingCodeInput>
        )}

        {/* Voice Instructions */}
        {isConnected && (
          <VoiceInstructions>
            <strong>🎤 Voice Commands Available:</strong><br/>
            • "Send a message to the passenger saying..."<br/>
            • "Call the passenger"<br/>
            • "Show me the message history"<br/>
            • "Get recent messages"
          </VoiceInstructions>
        )}

        {/* Status Message */}
        <StatusMessage>{statusMessage}</StatusMessage>

        {/* Chat Container */}
        <ChatContainer ref={chatContainerRef}>
          <AnimatePresence>
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                $isOwn={message.sender === 'driver'}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <Avatar $type={message.sender}>
                  {message.sender === 'driver' ? <FaCar /> : 
                   message.sender === 'passenger' ? <FaUser /> : '🤖'}
                </Avatar>
                <div>
                  <MessageContent $isOwn={message.sender === 'driver'}>
                    {message.text}
                  </MessageContent>
                  <MessageTime>
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </MessageTime>
                </div>
              </MessageBubble>
            ))}
          </AnimatePresence>
        </ChatContainer>

        {/* Voice Control */}
        {isConnected && (
          <VoiceControlContainer>
            <VoiceButton
              $isListening={isListening}
              onClick={startListening}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {isListening ? <FaMicrophoneSlash /> : <FaMicrophone />}
            </VoiceButton>
            
            {isListening && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                style={{ color: 'white', textAlign: 'center' }}
              >
                🎤 Listening... Speak now!
              </motion.div>
            )}
          </VoiceControlContainer>
        )}

        {/* Call Controls */}
        {callState !== 'idle' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ textAlign: 'center' }}
          >
            {callState === 'connected' && (
              <CallDuration>
                📞 {formatTime(callDuration)}
              </CallDuration>
            )}
            
            <CallControls>
              {callButtons.includes('accept') && (
                <CallButton $variant="accept" onClick={acceptCall}>
                  Accept
                </CallButton>
              )}
              {callButtons.includes('reject') && (
                <CallButton $variant="reject" onClick={rejectCall}>
                  Reject
                </CallButton>
              )}
              {callButtons.includes('end') && (
                <CallButton $variant="end" onClick={endCall}>
                  End
                </CallButton>
              )}
              {callButtons.includes('cancel') && (
                <CallButton $variant="cancel" onClick={cancelCall}>
                  Cancel
                </CallButton>
              )}
            </CallControls>
          </motion.div>
        )}
      </MainContent>
    </AppContainer>
  );
};

export default App; 