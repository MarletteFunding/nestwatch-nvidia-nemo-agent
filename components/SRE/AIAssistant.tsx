import React, { useState, useRef, useEffect } from 'react';
import { useTheme } from '../ThemeContext';

interface SREEvent {
  event_id?: string;
  subject?: string;
  priority?: string;
  event_source?: string;
  current_status?: string;
  monitor_name?: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

interface AIAssistantProps {
  isVisible: boolean;
  onToggle: () => void;
  aiAvailable: boolean;
  events: SREEvent[];
}

const AIAssistant: React.FC<AIAssistantProps> = ({ 
  isVisible, 
  onToggle, 
  aiAvailable, 
  events 
}) => {
  const { theme } = useTheme();
  const currentTheme = theme || 'light';
  
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: '👋 Hi! I\'m Hawky. I can help you with:\n\n• Event analysis and troubleshooting\n• System health questions\n• Incident response guidance\n• Best practices recommendations\n\nWhat can I help you with today?',
      timestamp: Date.now()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading || !aiAvailable) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Create SRE context from current events
      const criticalEvents = events.filter(e => e.priority === 'P1').length;
      const highEvents = events.filter(e => e.priority === 'P2').length;
      const totalEvents = events.length;
      
      const contextInfo = `Current SRE Status: ${totalEvents} active events (${criticalEvents} P1, ${highEvents} P2). Recent events include: ${
        events.slice(0, 3).map(e => `${e.priority}: ${e.subject?.substring(0, 50)}...`).join('; ')
      }`;

      // Send to NeMo backend with SRE context
      const response = await fetch('http://localhost:8000/api/v1/nemo/sre-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: userMessage.content,
          events_context: contextInfo
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.response || 'I apologize, but I couldn\'t process your request at the moment.',
          timestamp: Date.now()
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error('Failed to get AI response');
      }
    } catch (error) {
      console.error('AI Assistant error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '❌ I\'m having trouble connecting right now. Please try again in a moment, or check if the AI service is running.',
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getSuggestedQuestions = () => {
    const suggestions = [
      "What's the most critical issue right now?",
      "How do I troubleshoot database timeouts?",
      "Show me recent P1 incidents",
      "What's causing high error rates?",
      "Help me prioritize these events"
    ];
    
    if (events.some(e => e.priority === 'P1')) {
      suggestions.unshift("How should I handle these P1 incidents?");
    }
    
    return suggestions.slice(0, 3);
  };

  if (!aiAvailable) {
    return null; // Don't render if AI is not available
  }

  return (
    <>
      {/* Floating Toggle Button */}
      {!isVisible && (
        <button
          onClick={onToggle}
          className={`fixed bottom-6 right-6 w-14 h-14 rounded-full shadow-lg transition-all duration-300 transform hover:scale-110 z-40 ${
            currentTheme === 'dark'
              ? 'bg-blue-600 hover:bg-blue-700 text-white'
              : 'bg-blue-500 hover:bg-blue-600 text-white'
          } flex items-center justify-center animate-pulse`}
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-400 rounded-full animate-ping"></div>
        </button>
      )}

      {/* Chat Widget */}
      {isVisible && (
        <div className={`fixed bottom-6 right-6 w-96 h-[32rem] ${
          currentTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
        } border rounded-lg shadow-2xl z-50 flex flex-col animate-slideUp`}>
          
          {/* Header */}
          <div className={`flex items-center justify-between p-4 border-b ${
            currentTheme === 'dark' ? 'border-gray-700 bg-gray-750' : 'border-gray-200 bg-gray-50'
          } rounded-t-lg`}>
            <div className="flex items-center space-x-3">
              <div className="relative">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-bold">🤖</span>
                </div>
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
              </div>
              <div>
                <h3 className={`text-sm font-semibold ${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                  Hawky
                </h3>
                <p className={`text-xs ${currentTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                  Context-aware • {events.length} events monitored
                </p>
              </div>
            </div>
            <button
              onClick={onToggle}
              className={`p-1 rounded-full transition-colors duration-200 ${
                currentTheme === 'dark' 
                  ? 'text-gray-400 hover:text-white hover:bg-gray-700' 
                  : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
              }`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-3 py-2 ${
                    message.role === 'user'
                      ? 'bg-blue-500 text-white'
                      : currentTheme === 'dark'
                      ? 'bg-gray-700 text-gray-100 border border-gray-600'
                      : 'bg-gray-100 text-gray-900 border border-gray-200'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  <p className={`text-xs mt-1 ${
                    message.role === 'user' 
                      ? 'text-blue-100' 
                      : currentTheme === 'dark' ? 'text-gray-500' : 'text-gray-400'
                  }`}>
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className={`max-w-[80%] rounded-lg px-3 py-2 ${
                  currentTheme === 'dark' ? 'bg-gray-700 border-gray-600' : 'bg-gray-100 border-gray-200'
                } border`}>
                  <div className="flex items-center space-x-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <span className={`text-xs ${currentTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                      AI thinking...
                    </span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Actions */}
          {messages.length <= 1 && (
            <div className={`p-3 border-t ${currentTheme === 'dark' ? 'border-gray-700 bg-gray-750' : 'border-gray-200 bg-gray-50'}`}>
              <p className={`text-xs ${currentTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'} mb-2`}>
                Quick questions:
              </p>
              <div className="space-y-1">
                {getSuggestedQuestions().map((question, index) => (
                  <button
                    key={index}
                    onClick={() => setInputValue(question)}
                    className={`w-full text-left text-xs p-2 rounded transition-colors duration-200 ${
                      currentTheme === 'dark'
                        ? 'text-gray-300 hover:bg-gray-700 border border-gray-600'
                        : 'text-gray-600 hover:bg-gray-100 border border-gray-200'
                    }`}
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className={`p-4 border-t ${currentTheme === 'dark' ? 'border-gray-700' : 'border-gray-200'}`}>
            <div className="flex space-x-2">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about SRE events, troubleshooting, or best practices..."
                className={`flex-1 text-sm border rounded-md px-3 py-2 resize-none ${
                  currentTheme === 'dark'
                    ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                    : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                } focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
                rows={1}
                disabled={isLoading}
              />
              <button
                onClick={sendMessage}
                disabled={!inputValue.trim() || isLoading}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
                  !inputValue.trim() || isLoading
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-500 hover:bg-blue-600 text-white'
                }`}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default AIAssistant;
