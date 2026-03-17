import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DollarSign, Mail, MessageSquare, Copy, Send, Sparkles } from 'lucide-react';
import { Card, CardHeader, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

const NegotiationCenter = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        vendor_name: '',
        invoice_number: '',
        amount: '',
        due_date: '',
        negotiation_context: '',
        vendor_relationship: 'neutral',
        tone: 'professional'
    });
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleGenerate = async () => {
        setLoading(true);

        try {
            const response = await fetch('http://localhost:8000/api/v1/negotiation/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    invoice_data: {
                        vendor_name: formData.vendor_name,
                        invoice_number: formData.invoice_number,
                        amount: parseFloat(formData.amount) || 0,
                        due_date: formData.due_date
                    },
                    negotiation_context: formData.negotiation_context,
                    vendor_relationship: formData.vendor_relationship,
                    tone: formData.tone,
                    generate_variations: true
                })
            });

            if (!response.ok) throw new Error('Failed to generate draft');

            const data = await response.json();
            setResult(data);
        } catch (error) {
            console.error('Error:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleCopy = (text) => {
        navigator.clipboard.writeText(text);
        // Show toast notification
    };

    return (
        <div className="min-h-screen bg-slate-50 p-6 lg:p-8">
            <div className="max-w-6xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900">Negotiation Center</h1>
                        <p className="text-slate-500 mt-1">AI-powered vendor communication drafts</p>
                    </div>
                    <Button variant="outline" onClick={() => navigate('/history')}>
                        View History
                    </Button>
                </div>

                {/* Quick Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <StatCard
                        icon={Mail}
                        label="Emails Sent"
                        value="47"
                        change="+12% this month"
                    />
                    <StatCard
                        icon={DollarSign}
                        label="Amount Negotiated"
                        value="₹2.4Cr"
                        change="+8% this month"
                    />
                    <StatCard
                        icon={MessageSquare}
                        label="Success Rate"
                        value="78%"
                        change="+5% this month"
                    />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Input Form */}
                    <Card>
                        <CardHeader>
                            <h2 className="text-lg font-semibold text-slate-900">Create Negotiation Draft</h2>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-2">
                                        Vendor Name
                                    </label>
                                    <input
                                        type="text"
                                        name="vendor_name"
                                        value={formData.vendor_name}
                                        onChange={handleChange}
                                        className="input"
                                        placeholder="e.g., ABC Suppliers"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-2">
                                        Invoice Number
                                    </label>
                                    <input
                                        type="text"
                                        name="invoice_number"
                                        value={formData.invoice_number}
                                        onChange={handleChange}
                                        className="input"
                                        placeholder="e.g., INV-001"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-2">
                                        Amount (₹)
                                    </label>
                                    <input
                                        type="number"
                                        name="amount"
                                        value={formData.amount}
                                        onChange={handleChange}
                                        className="input"
                                        placeholder="e.g., 100000"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-2">
                                        Due Date
                                    </label>
                                    <input
                                        type="date"
                                        name="due_date"
                                        value={formData.due_date}
                                        onChange={handleChange}
                                        className="input"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">
                                    Negotiation Context
                                </label>
                                <textarea
                                    name="negotiation_context"
                                    value={formData.negotiation_context}
                                    onChange={handleChange}
                                    rows={3}
                                    className="input"
                                    placeholder="e.g., Need 15 days extension due to cash flow timing issues..."
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-2">
                                        Vendor Relationship
                                    </label>
                                    <select
                                        name="vendor_relationship"
                                        value={formData.vendor_relationship}
                                        onChange={handleChange}
                                        className="input"
                                    >
                                        <option value="neutral">Neutral</option>
                                        <option value="good">Good</option>
                                        <option value="strained">Strained</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-2">
                                        Tone
                                    </label>
                                    <select
                                        name="tone"
                                        value={formData.tone}
                                        onChange={handleChange}
                                        className="input"
                                    >
                                        <option value="professional">Professional</option>
                                        <option value="firm">Firm</option>
                                        <option value="polite">Polite</option>
                                        <option value="friendly">Friendly</option>
                                    </select>
                                </div>
                            </div>

                            <Button
                                onClick={handleGenerate}
                                disabled={loading || !formData.vendor_name || !formData.amount}
                                className="w-full"
                            >
                                {loading ? (
                                    <>
                                        <Sparkles className="w-4 h-4 mr-2 animate-spin" />
                                        Generating Draft...
                                    </>
                                ) : (
                                    <>
                                        <Sparkles className="w-4 h-4 mr-2" />
                                        Generate Draft
                                    </>
                                )}
                            </Button>
                        </CardContent>
                    </Card>

                    {/* Results */}
                    <div className="space-y-4">
                        {result ? (
                            <>
                                {/* Primary Draft */}
                                <Card>
                                    <CardHeader>
                                        <div className="flex items-center justify-between">
                                            <h2 className="text-lg font-semibold text-slate-900">
                                                Primary Draft
                                            </h2>
                                            <Badge variant="info">{result.primary_draft.intent}</Badge>
                                        </div>
                                    </CardHeader>
                                    <CardContent className="space-y-4">
                                        <div>
                                            <label className="text-sm font-medium text-slate-700">Subject</label>
                                            <p className="text-slate-900 font-medium mt-1">
                                                {result.primary_draft.subject}
                                            </p>
                                        </div>
                                        <div>
                                            <label className="text-sm font-medium text-slate-700">Email Body</label>
                                            <div className="mt-2 p-4 bg-slate-50 rounded-lg border border-slate-200 whitespace-pre-wrap text-sm">
                                                {result.primary_draft.body}
                                            </div>
                                        </div>
                                        {result.primary_draft.telegram_message && (
                                            <div>
                                                <label className="text-sm font-medium text-slate-700">Telegram Message</label>
                                                <div className="mt-2 p-3 bg-blue-50 rounded-lg border border-blue-200 text-sm">
                                                    {result.primary_draft.telegram_message}
                                                </div>
                                            </div>
                                        )}
                                        <div className="flex gap-2">
                                            <Button
                                                size="sm"
                                                variant="outline"
                                                onClick={() => handleCopy(result.primary_draft.body)}
                                            >
                                                <Copy className="w-4 h-4 mr-2" />
                                                Copy
                                            </Button>
                                            <Button size="sm" variant="outline">
                                                <Send className="w-4 h-4 mr-2" />
                                                Send
                                            </Button>
                                        </div>
                                    </CardContent>
                                </Card>

                                {/* Alternative Draft */}
                                {result.alternative_draft && (
                                    <Card>
                                        <CardHeader>
                                            <div className="flex items-center justify-between">
                                                <h2 className="text-lg font-semibold text-slate-900">
                                                    Alternative Approach
                                                </h2>
                                                <Badge variant="outline">A/B Test</Badge>
                                            </div>
                                        </CardHeader>
                                        <CardContent className="space-y-3">
                                            <p className="text-sm text-slate-600">
                                                {result.alternative_draft.strategy_explanation}
                                            </p>
                                            <div className="p-3 bg-slate-50 rounded-lg text-sm">
                                                <p className="font-medium">{result.alternative_draft.subject}</p>
                                            </div>
                                            <Button size="sm" variant="outline" className="w-full">
                                                View Full Draft
                                            </Button>
                                        </CardContent>
                                    </Card>
                                )}

                                {/* Recommendations */}
                                {result.recommendations && (
                                    <Card>
                                        <CardHeader>
                                            <h2 className="text-lg font-semibold text-slate-900">Recommendations</h2>
                                        </CardHeader>
                                        <CardContent>
                                            <ul className="space-y-2">
                                                {result.recommendations.map((rec, index) => (
                                                    <li key={index} className="flex items-start gap-2 text-sm">
                                                        <span className="text-green-600 mt-0.5">✓</span>
                                                        <span className="text-slate-700">{rec}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </CardContent>
                                    </Card>
                                )}
                            </>
                        ) : (
                            <Card>
                                <CardContent className="p-12 text-center">
                                    <Mail className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                                    <h3 className="text-lg font-semibold text-slate-900 mb-2">
                                        No Draft Generated Yet
                                    </h3>
                                    <p className="text-slate-500">
                                        Fill in the form and click "Generate Draft" to create AI-powered negotiation emails
                                    </p>
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </div>

                {/* Templates */}
                <Card>
                    <CardHeader>
                        <h2 className="text-lg font-semibold text-slate-900">Quick Templates</h2>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <TemplateCard
                                title="Credit Extension"
                                description="Request more time for payment"
                                onClick={() => setFormData({
                                    ...formData,
                                    negotiation_context: 'Requesting 15-day extension due to cash flow timing'
                                })}
                            />
                            <TemplateCard
                                title="Payment Follow-up"
                                description="Chase overdue payments professionally"
                                onClick={() => setFormData({
                                    ...formData,
                                    negotiation_context: 'Following up on invoice overdue by 15 days'
                                })}
                            />
                            <TemplateCard
                                title="Early Payment Offer"
                                description="Offer early payment for discount"
                                onClick={() => setFormData({
                                    ...formData,
                                    negotiation_context: 'Offering early payment with 2% discount'
                                })}
                            />
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

// Sub-components

const StatCard = ({ icon: Icon, label, value, change }) => (
    <Card>
        <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-primary-100 rounded-lg">
                    <Icon className="w-6 h-6 text-primary-600" />
                </div>
                <Badge variant="success">{change}</Badge>
            </div>
            <p className="text-sm text-slate-600 mb-1">{label}</p>
            <p className="text-2xl font-bold text-slate-900">{value}</p>
        </CardContent>
    </Card>
);

const TemplateCard = ({ title, description, onClick }) => (
    <button
        onClick={onClick}
        className="p-4 bg-slate-50 border border-slate-200 rounded-lg hover:border-primary-300 hover:shadow-sm transition-all text-left"
    >
        <h3 className="font-semibold text-slate-900 mb-1">{title}</h3>
        <p className="text-sm text-slate-600">{description}</p>
    </button>
);

export default NegotiationCenter;
