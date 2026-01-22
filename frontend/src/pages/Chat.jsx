import { useState, useEffect, useRef } from 'react';
import MessageBubble from '../components/Chat/MessageBubble';
import ActionCard from '../components/Chat/ActionCard';
import InputBar from '../components/Chat/InputBar';
import InvoiceDrawer from '../components/Chat/InvoiceDrawer';
import Disclaimer from '../components/Disclaimer';
import api from '../services/api';

const Chat = () => {
    const [messages, setMessages] = useState([
        {
            id: 1,
            text: "Namaste! Upload a bill to start the audit.",
            sender: 'bot',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
    ]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [showDisclaimer, setShowDisclaimer] = useState(false);
    const [disclaimerAccepted, setDisclaimerAccepted] = useState(false);
    const [activeInvoice, setActiveInvoice] = useState(null);

    const messagesEndRef = useRef(null);

    // Check if disclaimer has been accepted in this session
    useEffect(() => {
        const accepted = sessionStorage.getItem('disclaimer_accepted');
        if (!accepted) {
            setShowDisclaimer(true);
        } else {
            setDisclaimerAccepted(true);
        }
    }, []);

    const handleDisclaimerAccept = () => {
        sessionStorage.setItem('disclaimer_accepted', 'true');
        setDisclaimerAccepted(true);
        setShowDisclaimer(false);

        // Add welcome message after disclaimer acceptance
        addMessage(
            "✅ Thank you for accepting the disclaimer. Remember to always verify AI outputs with qualified professionals.",
            'bot'
        );
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const addMessage = (text, sender = 'bot', data = null, type = null) => {
        const newMessage = {
            id: Date.now() + Math.random(),
            text,
            sender,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            ...(data && { data }),
            ...(type && { type })
        };
        setMessages(prev => [...prev, newMessage]);
        return newMessage;
    };

    const handleFileUpload = async (file) => {
        if (!file) return;

        setIsProcessing(true);

        // Add user message showing file upload
        addMessage(`Uploaded: ${file.name}`, 'user');

        // Add processing message
        const processingMsg = addMessage("Processing your invoice...", 'bot');

        try {
            // Call the real API
            const response = await api.visualAuditor.uploadDocument(file, true);

            // Remove processing message
            setMessages(prev => prev.filter(msg => msg.id !== processingMsg.id));

            if (response.success && response.invoice_data) {
                const invoice = response.invoice_data;
                setActiveInvoice(invoice); // Open the drawer

                // Add success message with invoice details
                const summaryText = `✅ Invoice processed successfully!\n\n` +
                    `Vendor: ${invoice.vendor_name}\n` +
                    `Date: ${invoice.invoice_date}\n` +
                    `Total: ₹${invoice.total_amount.toLocaleString()}\n` +
                    `Tax: ₹${invoice.tax_amount.toLocaleString()}\n` +
                    `Items: ${invoice.line_items.length}`;

                addMessage(summaryText, 'bot');

                // Add compliance flags if any
                if (invoice.compliance_flags && invoice.compliance_flags.length > 0) {
                    addMessage(`⚠️ Compliance Flags: ${invoice.compliance_flags.join(', ')}`, 'bot');
                }

                // Add action card for next steps
                addMessage(
                    null,
                    'bot',
                    {
                        text: "What would you like to do next?",
                        actions: [
                            { label: "Check Legal Compliance", action: "legal_check" },
                            { label: "Find Subsidies", action: "find_subsidies" },
                            { label: "Generate Negotiation Email", action: "negotiate" }
                        ]
                    },
                    'action'
                );
            } else {
                addMessage("❌ Failed to process invoice. Please try again.", 'bot');
            }
        } catch (error) {
            console.error('Upload error:', error);
            setMessages(prev => prev.filter(msg => msg.id !== processingMsg.id));
            addMessage(`❌ Error: ${error.message || 'Failed to process invoice'}`, 'bot');
        } finally {
            setIsProcessing(false);
        }
    };

    const handleAction = async (actionType) => {
        addMessage(`Executing: ${actionType}`, 'user');

        // Handle different action types
        switch (actionType) {
            case 'legal_check':
                addMessage("Checking legal compliance... This feature will be available soon!", 'bot');
                break;
            case 'find_subsidies':
                addMessage("Searching for applicable subsidies... This feature will be available soon!", 'bot');
                break;
            case 'negotiate':
                addMessage("Generating negotiation email... This feature will be available soon!", 'bot');
                break;
            default:
                addMessage("Processing your request...", 'bot');
        }
    };

    const handleSend = (text) => {
        if (!text.trim()) return;

        // Add user message
        addMessage(text, 'user');

        // Add bot response
        setTimeout(() => {
            addMessage("I'm analyzing that for you...", 'bot');
        }, 500);
    };

    return (
        <div className="flex h-full bg-slate-50 relative overflow-hidden">
            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col h-full min-w-0 transition-all duration-300 relative">

                {/* Disclaimer Modal */}
                {showDisclaimer && (
                    <Disclaimer
                        onAccept={handleDisclaimerAccept}
                        onClose={null}  // Don't allow closing without accepting
                    />
                )}

                {/* Disclaimer Banner - Always visible */}
                <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 flex items-center justify-center gap-2 text-sm">
                    <span className="text-amber-800">⚠️</span>
                    <span className="text-amber-900 font-medium">
                        AI Assistant - Not a professional. Always verify outputs with qualified experts.
                    </span>
                    <button
                        onClick={() => setShowDisclaimer(true)}
                        className="text-amber-700 hover:text-amber-900 underline ml-2"
                    >
                        View Full Disclaimer
                    </button>
                </div>

                {/* Date Divider */}
                <div className="flex justify-center my-4 sticky top-0 z-10 transition-opacity">
                    <span className="bg-slate-200 text-slate-600 text-xs py-1 px-3 rounded-full font-medium shadow-sm border border-white">
                        Today
                    </span>
                </div>

                {/* Messages Area */}
                <div className="flex-1 overflow-y-auto px-4 pb-4 max-w-5xl mx-auto w-full scroll-smooth">
                    {messages.map((msg) => (
                        <div key={msg.id}>
                            {msg.type === 'action' ? (
                                <div className="flex justify-start animate-fade-in-up">
                                    <ActionCard data={msg.data} onAction={handleAction} />
                                </div>
                            ) : (
                                <MessageBubble message={msg} />
                            )}
                        </div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="bg-slate-50 border-t border-slate-200">
                    <InputBar
                        onSend={handleSend}
                        onFileUpload={handleFileUpload}
                        isProcessing={isProcessing}
                    />
                </div>
            </div>

            {/* Split View Drawer */}
            <InvoiceDrawer
                invoice={activeInvoice}
                onClose={() => setActiveInvoice(null)}
                onSave={(data) => {
                    console.log('Saved invoice data:', data);
                    setActiveInvoice(null);
                    addMessage("✅ Invoice verified and saved.", "bot");
                }}
            />
        </div>
    );
};

export default Chat;
