import React, { useState, useRef, useEffect } from 'react';
import { X, Send, Bot, User, Mic, Volume2, MicOff, MessageCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { ColorOrb } from './ui/color-orb';
import { AILoader } from './ui/ai-loader';
import { SimilarQuestions } from './SimilarQuestions';
import { API_CONFIG } from '../utils/constants';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

export const Chatbot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Hello! I\'m your EduQuest.ai assistant. How can I help you today?',
      sender: 'bot',
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [similarQuestions, setSimilarQuestions] = useState<any[]>([]);
  const [showSimilarModal, setShowSimilarModal] = useState(false);
  const [isCheckingSimilar, setIsCheckingSimilar] = useState(false);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  const FORM_WIDTH = 420;
  const FORM_HEIGHT = 600;
  const SPEED_FACTOR = 1;

  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    function clickOutsideHandler(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node) && isOpen) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', clickOutsideHandler);
    return () => document.removeEventListener('mousedown', clickOutsideHandler);
  }, [isOpen]);

  // Debounced similar question detection
  useEffect(() => {
    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Only check if input is substantial (more than 10 characters)
    if (inputValue.trim().length > 10) {
      setIsCheckingSimilar(true);
      
      // Wait 2 seconds after typing stops
      debounceTimerRef.current = setTimeout(async () => {
        try {
          const response = await fetch(`${API_CONFIG.BACKEND_URL}/api/detect-similar-questions`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
              questionText: inputValue,
              threshold: 0.5 // 50% similarity threshold
            }),
          });

          const data = await response.json();
          
          if (data.similarQuestions && data.similarQuestions.length > 0) {
            setSimilarQuestions(data.similarQuestions);
            setShowSimilarModal(true);
          }
        } catch (error) {
          console.error('Error checking similar questions:', error);
        } finally {
          setIsCheckingSimilar(false);
        }
      }, 2000);
    } else {
      setIsCheckingSimilar(false);
      setSimilarQuestions([]);
    }

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [inputValue]);

  // Initialize Web Speech API
  useEffect(() => {
    if (typeof window !== 'undefined') {
      synthRef.current = window.speechSynthesis;

      // Check for speech recognition support
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = false;
        recognitionRef.current.interimResults = false;
        recognitionRef.current.lang = 'en-US';

        recognitionRef.current.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript;
          setInputValue(transcript);
          setIsRecording(false);
        };

        recognitionRef.current.onerror = (event: any) => {
          console.error('Speech recognition error:', event.error);
          setIsRecording(false);
        };

        recognitionRef.current.onend = () => {
          setIsRecording(false);
        };
      }
    }

    return () => {
      if (synthRef.current) {
        synthRef.current.cancel();
      }
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const startVoiceRecording = () => {
    if (recognitionRef.current && !isRecording) {
      try {
        setIsRecording(true);
        recognitionRef.current.start();
      } catch (error) {
        console.error('Error starting voice recognition:', error);
        setIsRecording(false);
      }
    }
  };

  const stopVoiceRecording = () => {
    if (recognitionRef.current && isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    }
  };

  const speakText = (text: string) => {
    if (synthRef.current && voiceEnabled) {
      // Cancel any ongoing speech
      synthRef.current.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1;
      utterance.pitch = 1;
      utterance.volume = 1;

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      synthRef.current.speak(utterance);
    }
  };

  const toggleVoice = () => {
    if (isSpeaking && synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
    setVoiceEnabled(!voiceEnabled);
  };

  const sendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      const response = await fetch(`${API_CONFIG.BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: inputValue }),
      });

      const data = await response.json();

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.response,
        sender: 'bot',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botMessage]);
      
      // Speak the bot's response if voice is enabled
      if (voiceEnabled) {
        speakText(data.response);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, I\'m having trouble connecting. Please try again.',
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      {/* AI Loader Overlay */}
      {isTyping && <AILoader size={180} text="Thinking" />}

      {/* Similar Questions Modal */}
      {showSimilarModal && similarQuestions.length > 0 && (
        <SimilarQuestions
          questions={similarQuestions}
          onClose={() => setShowSimilarModal(false)}
          onContinue={() => {
            setShowSimilarModal(false);
            setSimilarQuestions([]);
          }}
        />
      )}

      <div className="fixed bottom-8 right-6 z-50 flex items-center justify-center">
        <motion.div
          ref={wrapperRef}
          data-panel
          className={`relative flex flex-col items-center overflow-hidden border shadow-xl ${isOpen ? 'bg-white border-gray-200' : 'bg-gradient-to-br from-amber-400 to-orange-500 border-orange-400/30'}`}
          initial={false}
          animate={{
            width: isOpen ? FORM_WIDTH : 'auto',
            height: isOpen ? FORM_HEIGHT : 56,
            borderRadius: isOpen ? 20 : 999,
          }}
          transition={{
            type: 'spring',
            stiffness: 550 / SPEED_FACTOR,
            damping: 45,
            mass: 0.7,
            delay: isOpen ? 0 : 0.08,
          }}
        >
        {/* Dock Bar - Collapsed State */}
        <footer className="mt-auto flex h-[56px] items-center justify-center whitespace-nowrap select-none">
          <div className="flex items-center justify-center gap-2 px-3">
            <div className="flex w-fit items-center gap-2">
              <AnimatePresence mode="wait">
                {isOpen ? (
                  <motion.div
                    key="blank"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 0 }}
                    exit={{ opacity: 0 }}
                    className="h-5 w-5"
                  />
                ) : (
                  <motion.div
                    key="orb"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <MessageCircle className="h-5 w-5 text-white" aria-hidden="true" />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <button
              type="button"
              className={`flex h-fit flex-1 justify-end rounded-full px-2 py-1 transition-colors text-sm font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/70 ${isOpen ? 'hover:bg-gray-100 text-gray-700 focus-visible:ring-orange-500/50' : 'hover:bg-white/15 text-white'}`}
              onClick={() => setIsOpen(true)}
              aria-label="Open Ask AI assistant"
            >
              <span className="truncate">Ask AI</span>
            </button>
          </div>
        </footer>

        {/* Expanded Chat View */}
        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ type: 'spring', stiffness: 550 / SPEED_FACTOR, damping: 45, mass: 0.7 }}
              className="absolute bottom-0 flex h-full flex-col w-full"
            >
              {/* Header */}
              <div className="flex justify-between items-center p-3 border-b border-gray-200">
                <div className="flex items-center gap-2">
                  <ColorOrb dimension="24px" tones={{ base: 'oklch(22.64% 0 0)' }} />
                  <div>
                    <h3 className="font-medium text-sm text-gray-900">AI Assistant</h3>
                    <p className="text-xs text-gray-500">{isSpeaking ? 'Speaking...' : 'Online'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={toggleVoice}
                    className="hover:bg-gray-100 rounded p-2 transition-colors text-gray-600"
                    title={voiceEnabled ? 'Disable voice' : 'Enable voice'}
                  >
                    {voiceEnabled ? <Volume2 size={16} /> : <MicOff size={16} />}
                  </button>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="hover:bg-gray-100 rounded p-2 transition-colors text-gray-600"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>

              {/* Messages */}
              <div 
                ref={messagesContainerRef}
                className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50"
              >
                {messages.length === 1 && (
                  <div className="text-center py-12 px-4">
                    <Bot size={40} className="text-gray-400 mx-auto mb-3" />
                    <h4 className="text-base font-medium text-gray-700 mb-1">Start a conversation</h4>
                    <p className="text-sm text-gray-500">
                      Ask me anything about EduQuest
                    </p>
                  </div>
                )}

                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex gap-2 ${message.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                  >
                    <div 
                      className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
                        message.sender === 'user' 
                          ? 'bg-gray-800 text-white' 
                          : 'bg-gray-200 text-gray-700'
                      }`}
                    >
                      {message.sender === 'user' ? <User size={14} /> : <Bot size={14} />}
                    </div>
                    <div className={`flex-1 flex flex-col ${message.sender === 'user' ? 'items-end' : 'items-start'}`}>
                      <div
                        className={`px-3 py-2 rounded-lg max-w-[85%] text-sm ${
                          message.sender === 'user'
                            ? 'bg-gray-800 text-white'
                            : 'bg-white text-gray-800 border border-gray-200'
                        }`}
                      >
                        <p className="leading-relaxed whitespace-pre-wrap break-words">
                          {message.text}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}

                {isTyping && (
                  <div className="flex gap-2">
                    <div className="w-7 h-7 rounded-full bg-gray-200 flex items-center justify-center">
                      <Bot size={14} className="text-gray-700" />
                    </div>
                    <div className="px-3 py-2 bg-white border border-gray-200 rounded-lg">
                      <div className="flex gap-1">
                        {[0, 1, 2].map((i) => (
                          <motion.div
                            key={i}
                            className="w-1.5 h-1.5 bg-gray-400 rounded-full"
                            animate={{ 
                              scale: [1, 1.2, 1],
                              opacity: [0.5, 1, 0.5]
                            }}
                            transition={{
                              duration: 1,
                              repeat: Infinity,
                              delay: i * 0.2
                            }}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Input */}
              <div className="p-3 bg-white border-t border-gray-200">
                <div className="flex gap-2">
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={isRecording ? '🎤 Listening...' : isCheckingSimilar ? '🔍 Checking similarity...' : 'Type a message...'}
                    className="flex-1 px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-800 focus:border-transparent transition-all text-sm"
                  />
                  <button
                    onClick={isRecording ? stopVoiceRecording : startVoiceRecording}
                    disabled={isTyping}
                    className={`p-2 rounded-lg text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                      isRecording ? 'bg-red-600 hover:bg-red-700' : 'bg-gray-600 hover:bg-gray-700'
                    }`}
                    title={isRecording ? 'Stop recording' : 'Start voice input'}
                  >
                    <Mic size={18} />
                  </button>
                  <button
                    onClick={sendMessage}
                    disabled={!inputValue.trim() || isTyping}
                    className="bg-gray-800 hover:bg-gray-900 text-white p-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Send size={18} />
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
    </>
  );
};
