import React, { useState, useRef, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";
import { encodingForModel } from "js-tiktoken";

const API_ENDPOINT = process.env.NEXT_PUBLIC_API_ENDPOINT;

// Initialize tokenizer (cl100k_base encoding for Phi-3)
const tokenizer = encodingForModel("gpt-3.5-turbo"); // Uses cl100k_base

// Token limits
const MAX_INPUT_TOKENS = 512;

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export default function SopranoChatbot() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Eyy, what's the matter with you? Go ahead, ask me something.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [inputTokenCount, setInputTokenCount] = useState(0);
  const [isTokenLimitReached, setIsTokenLimitReached] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const previousInputRef = useRef<string>("");

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const countTokens = (text: string): number => {
    try {
      return tokenizer.encode(text).length;
    } catch (error) {
      console.error("Token counting error:", error);
      return Math.ceil(text.length / 4);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    const tokenCount = countTokens(newValue);

    if (tokenCount > MAX_INPUT_TOKENS) {
      try {
        const tokens = tokenizer.encode(newValue);
        const truncatedTokens = tokens.slice(0, MAX_INPUT_TOKENS);
        const truncated = tokenizer.decode(truncatedTokens);
        setInput(truncated);
        setInputTokenCount(MAX_INPUT_TOKENS);
        setIsTokenLimitReached(true);
        previousInputRef.current = truncated;
      } catch (error) {
        setInput(previousInputRef.current);
        setInputTokenCount(MAX_INPUT_TOKENS);
        setIsTokenLimitReached(true);
      }
    } else {
      setInput(newValue);
      setInputTokenCount(tokenCount);
      setIsTokenLimitReached(tokenCount === MAX_INPUT_TOKENS);
      previousInputRef.current = newValue;
    }
  };

  // --- UPDATED SEND MESSAGE FUNCTION FOR STREAMING ---
  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    if (!API_ENDPOINT) {
      console.error("API endpoint not configured");
      const errorMessage: Message = {
        role: "assistant",
        content:
          "Madone! The API endpoint isn't configured. Check your .env file.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      return;
    }

    const currentPrompt = input.trim();

    // 1. Add User Message immediately
    const userMessage: Message = {
      role: "user",
      content: currentPrompt,
      timestamp: new Date(),
    };

    // 2. Create a placeholder Assistant Message (empty content)
    const placeholderAssistantMessage: Message = {
      role: "assistant",
      content: "",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage, placeholderAssistantMessage]);
    setInput("");
    setInputTokenCount(0);
    setIsTokenLimitReached(false);
    previousInputRef.current = "";
    setIsLoading(true);

    try {
      const historyMessages = messages.slice(1).map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      const response = await fetch(API_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt: currentPrompt,
          history: historyMessages,
        }),
      });

      if (!response.ok) throw new Error("Network response was not ok");
      if (!response.body) throw new Error("Response body is empty");

      // 3. Read the Stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        // SSE lines come as "data: {json}\n\n"
        const lines = chunk
          .split("\n\n")
          .filter((line) => line.startsWith("data: "));

        for (const line of lines) {
          const jsonStr = line.replace("data: ", "");
          if (jsonStr === "[DONE]") break;

          try {
            const data = JSON.parse(jsonStr);
            if (data.token) {
              accumulatedText += data.token;

              // 4. Update the last message (the placeholder) in real-time
              setMessages((prev) => {
                const newMessages = [...prev];
                const lastMsg = newMessages[newMessages.length - 1];
                // Ensure we are only updating the assistant's placeholder
                if (lastMsg.role === "assistant") {
                  lastMsg.content = accumulatedText;
                }
                return newMessages;
              });
            }
          } catch (e) {
            console.warn("Failed to parse SSE token:", jsonStr);
          }
        }
      }
    } catch (error) {
      console.error("Error:", error);
      // If streaming fails, replace the empty placeholder with error text
      setMessages((prev) => {
        const newMessages = [...prev];
        const lastMsg = newMessages[newMessages.length - 1];
        if (lastMsg.role === "assistant" && !lastMsg.content) {
          lastMsg.content =
            "Madone! Something went wrong with the connection. Try again, will ya?";
        }
        return newMessages;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
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
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {message.role === "assistant" && (
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
                  message.role === "user"
                    ? "bg-gradient-to-r from-blue-600 to-blue-700 text-white"
                    : "bg-zinc-800/80 backdrop-blur text-zinc-100 border border-amber-900/20"
                }`}
              >
                <p className="text-sm leading-relaxed whitespace-pre-wrap">
                  {message.content}
                  {/* Show typing cursor if loading and this is the last message */}
                  {isLoading &&
                    index === messages.length - 1 &&
                    message.role === "assistant" && (
                      <span className="inline-block w-1.5 h-4 ml-1 align-middle bg-amber-500 animate-pulse"></span>
                    )}
                </p>
                <p className="text-xs mt-2 opacity-60">
                  {message.timestamp.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
              {message.role === "user" && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center text-white font-bold text-sm flex-shrink-0 shadow-md">
                  U
                </div>
              )}
            </div>
          ))}
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
                onChange={handleInputChange}
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
          <div className="flex items-center justify-between mt-2">
            <p className="text-xs text-zinc-500 text-center flex-1">
              Press Enter to send, Shift+Enter for new line
            </p>
            {isTokenLimitReached && (
              <p className="text-xs text-amber-500/80 ml-2">
                Character limit reached. Further input will be cut off.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
