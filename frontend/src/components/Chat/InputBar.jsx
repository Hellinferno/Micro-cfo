import React, { useState } from 'react';
import { Paperclip, Send, Camera } from 'lucide-react';

const InputBar = ({ onSend }) => {
    const [input, setInput] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (input.trim()) {
            onSend(input);
            setInput('');
        }
    };

    return (
        <div className="bg-white p-3 lg:p-4 border-t border-slate-200">
            <form onSubmit={handleSubmit} className="flex items-center space-x-2 lg:space-x-4 max-w-5xl mx-auto">
                {/* Attach Button */}
                <button
                    type="button"
                    className="p-2 text-slate-400 hover:text-primary transition-colors hover:bg-slate-50 rounded-full"
                >
                    <Paperclip size={24} />
                </button>

                {/* Input Field */}
                <div className="flex-1 relative">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask me anything..."
                        className="w-full bg-slate-100 text-slate-800 placeholder-slate-400 px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all border-none"
                    />
                    <button
                        type="button"
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 lg:hidden"
                    >
                        <Camera size={20} />
                    </button>
                </div>

                {/* Send Button */}
                <button
                    type="submit"
                    disabled={!input.trim()}
                    className="p-3 bg-primary hover:bg-primary-dark text-white rounded-full shadow-lg shadow-primary/30 disabled:opacity-50 disabled:shadow-none transition-all transform active:scale-95"
                >
                    <Send size={20} />
                </button>
            </form>
        </div>
    );
};

export default InputBar;
