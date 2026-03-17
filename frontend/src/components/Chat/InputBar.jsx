import React from 'react';
import { Send, Mic, Paperclip, Sparkles } from 'lucide-react';
import { Button } from '../ui/Button';

const InputBar = ({
    value,
    onChange,
    onSend,
    onKeyPress,
    loading,
    placeholder = "Type your message..."
}) => {
    const handleSubmit = () => {
        if (!loading && value.trim()) {
            onSend();
        }
    };

    return (
        <div className="flex items-end gap-3 bg-slate-50 border border-slate-200 rounded-xl p-3">
            {/* Attachment Button */}
            <Button
                variant="ghost"
                size="icon"
                className="flex-shrink-0 text-slate-500 hover:text-primary-600"
                title="Attach file"
            >
                <Paperclip className="w-5 h-5" />
            </Button>

            {/* Text Input */}
            <textarea
                value={value}
                onChange={(e) => onChange(e.target.value)}
                onKeyPress={onKeyPress}
                placeholder={placeholder}
                rows={1}
                className="flex-1 bg-transparent border-0 focus:outline-none focus:ring-0 text-sm resize-none max-h-32 py-2"
                style={{ minHeight: '40px' }}
            />

            {/* Voice Input (Future) */}
            <Button
                variant="ghost"
                size="icon"
                className="flex-shrink-0 text-slate-500 hover:text-primary-600"
                title="Voice input"
            >
                <Mic className="w-5 h-5" />
            </Button>

            {/* Send Button */}
            <Button
                onClick={handleSubmit}
                disabled={loading || !value.trim()}
                className="flex-shrink-0"
                size="icon"
            >
                {loading ? (
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                    <Send className="w-5 h-5" />
                )}
            </Button>
        </div>
    );
};

export default InputBar;
