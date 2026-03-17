import React, { useState, useEffect, useRef } from 'react';
import { Send, Mic, Paperclip, Sparkles, User, Bot } from 'lucide-react';
import { Card, CardHeader, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import MessageBubble from '../components/Chat/MessageBubble';
import InputBar from '../components/Chat/InputBar';
import ActionCard from '../components/Chat/ActionCard';
import api from '../services/api';

const Chat = () => {
    const [messages, setMessages] = useState([
        {
            id: 1,
            role: 'assistant',
            content: "Hi! I'm MicroCFO, your AI financial assistant. I can help you with:\n\n• 📄 Invoice Analysis - Upload and analyze invoices\n• ⚖️ Compliance Checking - GST, ITC, and legal guidance\n• 💰 Subsidy Discovery - Find government schemes\n• 📧 Negotiation Assistance - Draft vendor communications\n\nWhat would you like help with today?",
            timestamp: new Date().toISOString(),
            agent: 'general'
        }
    ]);
    const [loading, setLoading] = useState(false);
    const [inputValue, setInputValue] = useState('');
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async (messageText = inputValue) => {
        if (!messageText.trim()) return;

        // Add user message
        const userMessage = {
            id: messages.length + 1,
            role: 'user',
            content: messageText,
            timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setLoading(true);

        try {
            // Call API using centralized service
            const response = await api.chat.sendMessage(
                messageText,
                'auto',
                messages.slice(-5).map(m => ({
                    role: m.role,
                    content: m.content
                }))
            );

            const data = response.data;

            // Add assistant response
            const assistantMessage = {
                id: messages.length + 2,
                role: 'assistant',
                content: data.message || "I'm sorry, I encountered an error. Please try again.",
                timestamp: new Date().toISOString(),
                agent: data.agent_used || 'general',
                metadata: data.metadata,
                suggestedActions: data.suggested_actions
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
            console.error('Error:', error);

            // Add error message
            const errorMessage = {
                id: messages.length + 2,
                role: 'assistant',
                content: error.response?.data?.detail || "I'm sorry, I encountered an error processing your request. Please try again or rephrase your question.",
                timestamp: new Date().toISOString(),
                agent: 'general'
            };

            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleSuggestedAction = (action) => {
        console.log('Suggested action:', action);
        // Handle suggested action
    };

    return (
        <div className="flex flex-col h-screen bg-slate-50">
            {/* Header */}
            <div className="bg-white border-b border-slate-200 px-6 py-4">
                <div className="max-w-5xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-r from-primary-600 to-primary-400 flex items-center justify-center">
                            <Bot className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-lg font-semibold text-slate-900">MicroCFO Assistant</h1>
                            <p className="text-sm text-slate-500">AI-powered financial guidance</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <Badge variant="info">Auto</Badge>
                        <Button variant="outline" size="sm">
                            Clear Chat
                        </Button>
                    </div>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto">
                <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
                    {messages.map((message) => (
                        <MessageBubble
                            key={message.id}
                            message={message}
                            onActionClick={handleSuggestedAction}
                        />
                    ))}

                    {loading && (
                        <div className="flex items-center gap-2 text-slate-500">
                            <div className="flex space-x-1">
                                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                            </div>
                            <span className="text-sm">MicroCFO is thinking...</span>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input Area */}
            <div className="bg-white border-t border-slate-200 px-6 py-4">
                <div className="max-w-5xl mx-auto">
                    <InputBar
                        value={inputValue}
                        onChange={setInputValue}
                        onSend={handleSend}
                        onKeyPress={handleKeyPress}
                        loading={loading}
                        placeholder="Ask about invoices, compliance, subsidies, or negotiations..."
                    />
                    <p className="text-xs text-slate-500 mt-2 text-center">
                        MicroCFO provides AI-generated guidance. Consult a CA for critical decisions.
                    </p>
                </div>
            </div>
        </div>
    );
};

// Simple Badge component
const Badge = ({ children, variant = 'default' }) => {
    const variants = {
        default: 'bg-slate-100 text-slate-800',
        info: 'bg-blue-100 text-blue-800',
        success: 'bg-green-100 text-green-800',
        warning: 'bg-yellow-100 text-yellow-800',
        danger: 'bg-red-100 text-red-800'
    };

    return (
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${variants[variant]}`}>
            {children}
        </span>
    );
};

export default Chat;
