import React from 'react';

const MessageBubble = ({ message }) => {
    const isBot = message.sender === 'bot';

    return (
        <div className={`flex w-full mb-4 ${isBot ? 'justify-start' : 'justify-end'}`}>
            <div
                className={`relative max-w-[85%] lg:max-w-[60%] px-4 py-3 rounded-2xl shadow-sm ${isBot
                        ? 'bg-chat-bot text-slate-800 rounded-tl-none'
                        : 'bg-white text-slate-800 rounded-tr-none'
                    }`}
            >
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.text}</p>
                <div className={`text-[10px] mt-1 text-right ${isBot ? 'text-emerald-700/60' : 'text-slate-400'}`}>
                    {message.timestamp}
                </div>
            </div>
        </div>
    );
};

export default MessageBubble;
