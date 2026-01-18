import React, { useState, useRef } from 'react';
import { Paperclip, Send, Camera, X } from 'lucide-react';

const InputBar = ({ onSend, onFileUpload, isProcessing = false }) => {
    const [input, setInput] = useState('');
    const [selectedFile, setSelectedFile] = useState(null);
    const fileInputRef = useRef(null);

    const handleSubmit = (e) => {
        e.preventDefault();
        
        if (selectedFile) {
            // Handle file upload
            onFileUpload(selectedFile);
            setSelectedFile(null);
        } else if (input.trim()) {
            // Handle text message
            onSend(input);
            setInput('');
        }
    };

    const handleFileSelect = (e) => {
        const file = e.target.files?.[0];
        if (file) {
            // Validate file type
            const validTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
            if (!validTypes.includes(file.type)) {
                alert('Please upload a PDF, PNG, or JPG file');
                return;
            }
            
            // Validate file size (50MB max)
            const maxSize = 50 * 1024 * 1024;
            if (file.size > maxSize) {
                alert('File size must be less than 50MB');
                return;
            }
            
            setSelectedFile(file);
            setInput(''); // Clear text input when file is selected
        }
        
        // Reset file input
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const handleAttachClick = () => {
        fileInputRef.current?.click();
    };

    const handleRemoveFile = () => {
        setSelectedFile(null);
    };

    const isDisabled = isProcessing || (!input.trim() && !selectedFile);

    return (
        <div className="bg-white p-3 lg:p-4 border-t border-slate-200">
            <form onSubmit={handleSubmit} className="max-w-5xl mx-auto">
                {/* File Preview */}
                {selectedFile && (
                    <div className="mb-2 flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-lg p-2">
                        <Paperclip size={16} className="text-blue-600" />
                        <span className="text-sm text-blue-900 flex-1 truncate">
                            {selectedFile.name}
                        </span>
                        <button
                            type="button"
                            onClick={handleRemoveFile}
                            className="text-blue-600 hover:text-blue-800"
                        >
                            <X size={16} />
                        </button>
                    </div>
                )}
                
                <div className="flex items-center space-x-2 lg:space-x-4">
                    {/* Hidden File Input */}
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf,.png,.jpg,.jpeg"
                        onChange={handleFileSelect}
                        className="hidden"
                        disabled={isProcessing}
                    />
                    
                    {/* Attach Button */}
                    <button
                        type="button"
                        onClick={handleAttachClick}
                        disabled={isProcessing}
                        className="p-2 text-slate-400 hover:text-primary transition-colors hover:bg-slate-50 rounded-full disabled:opacity-50"
                        title="Upload invoice (PDF, PNG, JPG)"
                    >
                        <Paperclip size={24} />
                    </button>

                    {/* Input Field */}
                    <div className="flex-1 relative">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder={selectedFile ? "Press send to upload..." : "Ask me anything..."}
                            disabled={isProcessing || selectedFile}
                            className="w-full bg-slate-100 text-slate-800 placeholder-slate-400 px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all border-none disabled:opacity-50"
                        />
                        <button
                            type="button"
                            onClick={handleAttachClick}
                            disabled={isProcessing}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 lg:hidden disabled:opacity-50"
                            title="Upload invoice"
                        >
                            <Camera size={20} />
                        </button>
                    </div>

                    {/* Send Button */}
                    <button
                        type="submit"
                        disabled={isDisabled}
                        className="p-3 bg-primary hover:bg-primary-dark text-white rounded-full shadow-lg shadow-primary/30 disabled:opacity-50 disabled:shadow-none transition-all transform active:scale-95"
                        title={selectedFile ? "Upload file" : "Send message"}
                    >
                        {isProcessing ? (
                            <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
                        ) : (
                            <Send size={20} />
                        )}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default InputBar;
