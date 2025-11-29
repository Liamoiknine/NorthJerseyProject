import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';

const API_ENDPOINT = process.env.NEXT_PUBLIC_API_ENDPOINT;

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function SopranoChatbot() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Eyy, what's the matter with you? Go ahead, ask me something.",
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    if (!API_ENDPOINT) {
      console.error('API endpoint not configured');
      const errorMessage: Message = {
        role: 'assistant',
        content: "Madone! The API endpoint isn't configured. Check your .env file.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      return;
    }

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: input })
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const data = await response.json();
      
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.response || 'Fuhgeddaboudit...',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: "Madone! Something went wrong with the connection. Try again, will ya?",
        timestamp: new Date()
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

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-stone-900">
      {/* Header */}
      <div className="bg-black/40 backdrop-blur-sm border-b border-amber-900/30 px-6 py-4 shadow-lg">
        <div className="max-w-4xl mx-auto flex items-center gap-4">
          <div className="w-12 h-12 rounded-full overflow-hidden shadow-lg ring-2 ring-amber-600/50">
            <img 
              src="/tony.webp" 
              alt="Tony Soprano" 
              className="w-full h-full object-cover"
            />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-amber-600">
              The North Jersey Project
            </h1>
            <p className="text-zinc-400 text-sm">Chat with Tony Soprano</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex gap-3 ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {message.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full overflow-hidden shadow-md ring-2 ring-amber-600/30 flex-shrink-0">
                  <img 
                    src="/tony.webp" 
                    alt="Tony Soprano" 
                    className="w-full h-full object-cover"
                  />
                </div>
              )}
              <div
                className={`max-w-2xl rounded-2xl px-5 py-3 shadow-lg ${
                  message.role === 'user'
                    ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white'
                    : 'bg-zinc-800/80 backdrop-blur text-zinc-100 border border-amber-900/20'
                }`}
              >
                <p className="text-sm leading-relaxed whitespace-pre-wrap">
                  {message.content}
                </p>
                <p className="text-xs mt-2 opacity-60">
                  {message.timestamp.toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </p>
              </div>
              {message.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center text-white font-bold text-sm flex-shrink-0 shadow-md">
                  U
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-full overflow-hidden shadow-md ring-2 ring-amber-600/30 flex-shrink-0">
                <img 
                  src="/tony.webp" 
                  alt="Tony Soprano" 
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="bg-zinc-800/80 backdrop-blur rounded-2xl px-5 py-3 border border-amber-900/20 shadow-lg">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-amber-500" />
                  <span className="text-zinc-400 text-sm">Tony is thinking...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-black/40 backdrop-blur-sm border-t border-amber-900/30 px-4 py-4 shadow-lg">
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-3 items-end">
            <div className="flex-1 bg-zinc-800/80 backdrop-blur rounded-2xl border border-zinc-700 focus-within:border-amber-600 transition-colors shadow-lg">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask Tony something..."
                className="w-full bg-transparent text-white placeholder-zinc-500 px-5 py-3 resize-none outline-none max-h-32"
                rows={1}
                disabled={isLoading}
              />
            </div>
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading}
              className="bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 disabled:from-zinc-700 disabled:to-zinc-800 text-white p-3 rounded-xl transition-all disabled:cursor-not-allowed shadow-lg hover:shadow-amber-900/50 disabled:shadow-none"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
          <p className="text-xs text-zinc-500 mt-3 text-center">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
}