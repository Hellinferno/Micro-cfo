import React, { useState, useEffect, useRef } from 'react';
import MessageBubble from '../components/Chat/MessageBubble';
import ActionCard from '../components/Chat/ActionCard';
import InputBar from '../components/Chat/InputBar';

const Chat = () => {
    const [messages, setMessages] = useState([
        {
            id: 1,
            text: "Namaste! Upload a bill to start the audit.",
            sender: 'bot',
            timestamp: '10:00 AM'
        },
        {
            id: 2,
            text: "Uploaded: invoice_jan_24.pdf",
            sender: 'user',
            timestamp: '10:02 AM'
        },
        {
            id: 3,
            type: 'action',
            sender: 'bot',
            timestamp: '10:02 AM',
            data: { text: "I found a subsidy for this machine." }
        }
    ]);

    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = (text) => {
        const newMessage = {
            id: messages.length + 1,
            text: text,
            sender: 'user',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prev => [...prev, newMessage]);

        // Simulate bot response
        setTimeout(() => {
            const botResponse = {
                id: messages.length + 2,
                text: "I'm analyzing that for you...",
                sender: 'bot',
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            };
            setMessages(prev => [...prev, botResponse]);
        }, 1000);
    };

    return (
        <div className="flex flex-col h-full bg-slate-50 relative">
            {/* Date Divider */}
            <div className="flex justify-center my-4 sticky top-0 z-10 transition-opacity">
                <span className="bg-slate-200 text-slate-600 text-xs py-1 px-3 rounded-full font-medium shadow-sm border border-white">
                    Today
                </span>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto px-4 pb-4 max-w-5xl mx-auto w-full">
                {messages.map((msg) => (
                    <div key={msg.id}>
                        {msg.type === 'action' ? (
                            <div className="flex justify-start animate-fade-in-up">
                                <ActionCard data={msg.data} />
                            </div>
                        ) : (
                            <MessageBubble message={msg} />
                        )}
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="sticky bottom-0 bg-slate-50">
                <InputBar onSend={handleSend} />
            </div>
        </div>
    );
};

export default Chat;
