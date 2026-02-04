import React, { useState } from 'react';
import {
    TrendingUp,
    TrendingDown,
    Mail,
    Clock,
    AlertCircle,
    CheckCircle,
    Send,
    Edit3,
    Eye,
    Calendar,
    Users,
    Building2,
    Phone,
    MessageSquare,
    FileText,
    RefreshCw,
    Copy,
    Sparkles,
    ArrowUpRight,
    ArrowDownRight,
    Filter
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Modal, Progress } from '../components/ui';
import { CashFlowChart } from '../components/charts';

const NegotiationCenter = () => {
    const [selectedInvoice, setSelectedInvoice] = useState(null);
    const [showEmailModal, setShowEmailModal] = useState(false);
    const [emailContent, setEmailContent] = useState('');
    const [emailTone, setEmailTone] = useState('polite');
    const [activeTab, setActiveTab] = useState('receivables');

    // Cash flow forecast data
    const cashFlowData = [
        { date: 'Week 1', inflow: 150000, outflow: 80000, predicted: true },
        { date: 'Week 2', inflow: 120000, outflow: 95000, predicted: true },
        { date: 'Week 3', inflow: 180000, outflow: 110000, predicted: true },
        { date: 'Week 4', inflow: 90000, outflow: 120000, predicted: true },
    ];

    // Overdue invoices
    const overdueInvoices = [
        {
            id: 1,
            client: 'ABC Corporation',
            invoiceNo: 'INV-2024-001',
            amount: 85000,
            dueDate: '2024-01-05',
            daysOverdue: 15,
            lastContact: '2024-01-10',
            status: 'email-sent',
            contactPerson: 'Rajesh Kumar',
            email: 'rajesh@abccorp.com',
            phone: '+91 98765 43210'
        },
        {
            id: 2,
            client: 'XYZ Industries',
            invoiceNo: 'INV-2024-008',
            amount: 145000,
            dueDate: '2024-01-10',
            daysOverdue: 10,
            lastContact: null,
            status: 'pending',
            contactPerson: 'Priya Sharma',
            email: 'priya@xyzind.com',
            phone: '+91 87654 32109'
        },
        {
            id: 3,
            client: 'PQR Services',
            invoiceNo: 'INV-2023-089',
            amount: 67500,
            dueDate: '2023-12-20',
            daysOverdue: 30,
            lastContact: '2024-01-15',
            status: 'responded',
            contactPerson: 'Amit Patel',
            email: 'amit@pqrservices.com',
            phone: '+91 76543 21098'
        },
        {
            id: 4,
            client: 'LMN Tech',
            invoiceNo: 'INV-2024-015',
            amount: 230000,
            dueDate: '2024-01-15',
            daysOverdue: 5,
            lastContact: null,
            status: 'pending',
            contactPerson: 'Sneha Reddy',
            email: 'sneha@lmntech.com',
            phone: '+91 65432 10987'
        },
    ];

    // Upcoming payables
    const upcomingPayables = [
        {
            id: 1,
            vendor: 'Raw Materials Co',
            invoiceNo: 'VEN-2024-045',
            amount: 125000,
            dueDate: '2024-01-25',
            daysUntilDue: 5,
            status: 'normal'
        },
        {
            id: 2,
            vendor: 'Equipment Supplier',
            invoiceNo: 'VEN-2024-038',
            amount: 350000,
            dueDate: '2024-01-22',
            daysUntilDue: 2,
            status: 'urgent',
            aiSuggestion: 'Request 15-day extension - good payment history'
        },
        {
            id: 3,
            vendor: 'Office Supplies Ltd',
            invoiceNo: 'VEN-2024-052',
            amount: 18500,
            dueDate: '2024-01-30',
            daysUntilDue: 10,
            status: 'normal'
        },
    ];

    // Email templates
    const emailTemplates = [
        { id: 'payment-request', name: 'Payment Request', tone: 'polite' },
        { id: 'payment-reminder', name: 'Payment Reminder', tone: 'firm' },
        { id: 'final-notice', name: 'Final Notice', tone: 'urgent' },
        { id: 'credit-extension', name: 'Credit Extension Request', tone: 'polite' },
        { id: 'invoice-dispute', name: 'Invoice Dispute Resolution', tone: 'polite' },
    ];

    const getStatusBadge = (status) => {
        switch (status) {
            case 'pending': return <Badge variant="default">Pending</Badge>;
            case 'email-sent': return <Badge variant="info">Email Sent</Badge>;
            case 'responded': return <Badge variant="success">Responded</Badge>;
            case 'escalated': return <Badge variant="danger">Escalated</Badge>;
            default: return <Badge>Unknown</Badge>;
        }
    };

    const generateEmail = (invoice, tone) => {
        const templates = {
            polite: `Dear ${invoice.contactPerson},

I hope this email finds you well. I am writing to kindly follow up on invoice ${invoice.invoiceNo} dated ${invoice.dueDate} for ₹${invoice.amount.toLocaleString()}.

According to our records, this payment is currently ${invoice.daysOverdue} days past the due date. We understand that delays can sometimes occur, and we would appreciate if you could provide us with an update on the expected payment timeline.

If you have already processed this payment, please disregard this message and accept our thanks.

Please feel free to reach out if you have any questions or concerns regarding this invoice.

Best regards,
Micro-CFO Team`,
            firm: `Dear ${invoice.contactPerson},

This is a reminder regarding the overdue payment for invoice ${invoice.invoiceNo} amounting to ₹${invoice.amount.toLocaleString()}, which was due on ${invoice.dueDate}.

The payment is now ${invoice.daysOverdue} days overdue. We kindly request you to process this payment at the earliest to avoid any disruption to our business relationship.

If there are any issues with the invoice or if you require any clarification, please let us know immediately.

We look forward to receiving the payment within the next 5 business days.

Regards,
Micro-CFO Team`,
            urgent: `Dear ${invoice.contactPerson},

URGENT: Final Notice for Overdue Payment

This serves as a final notice regarding invoice ${invoice.invoiceNo} for ₹${invoice.amount.toLocaleString()}, which is now ${invoice.daysOverdue} days past due.

Despite our previous communications, we have not received payment or a response regarding this matter. We must insist on immediate payment to avoid further action.

Please process the payment within 3 business days, or contact us immediately to discuss this matter.

Regards,
Micro-CFO Team`
        };
        return templates[tone] || templates.polite;
    };

    const openEmailModal = (invoice, tone = 'polite') => {
        setSelectedInvoice(invoice);
        setEmailTone(tone);
        setEmailContent(generateEmail(invoice, tone));
        setShowEmailModal(true);
    };

    const totalReceivables = overdueInvoices.reduce((sum, inv) => sum + inv.amount, 0);
    const totalPayables = upcomingPayables.reduce((sum, inv) => sum + inv.amount, 0);

    return (
        <div className="p-4 lg:p-8 space-y-6 bg-slate-50 min-h-screen">
            {/* Page Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 className="text-2xl lg:text-3xl font-bold text-slate-800">Cash Flow & Negotiation</h1>
                    <p className="text-slate-500 mt-1">Manage payments and AI-assisted communication</p>
                </div>
                <div className="flex gap-3">
                    <Badge variant="primary" className="py-2 px-4">
                        <Sparkles className="w-4 h-4 mr-1" />
                        Powered by Negotiator AI
                    </Badge>
                </div>
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Total Receivables</p>
                                <p className="text-2xl font-bold text-emerald-600">₹{(totalReceivables / 100000).toFixed(2)}L</p>
                            </div>
                            <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                                <ArrowDownRight className="w-5 h-5 text-emerald-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Total Payables</p>
                                <p className="text-2xl font-bold text-red-600">₹{(totalPayables / 100000).toFixed(2)}L</p>
                            </div>
                            <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                                <ArrowUpRight className="w-5 h-5 text-red-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Overdue Invoices</p>
                                <p className="text-2xl font-bold text-amber-600">{overdueInvoices.length}</p>
                            </div>
                            <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
                                <Clock className="w-5 h-5 text-amber-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Emails Sent</p>
                                <p className="text-2xl font-bold text-blue-600">12</p>
                            </div>
                            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                                <Mail className="w-5 h-5 text-blue-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Cash Flow Forecast Alert */}
            <Card className="bg-gradient-to-r from-amber-50 to-orange-50 border-amber-200">
                <CardContent className="pt-6">
                    <div className="flex items-start gap-4">
                        <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center flex-shrink-0">
                            <AlertCircle className="w-6 h-6 text-amber-600" />
                        </div>
                        <div className="flex-1">
                            <h3 className="font-semibold text-amber-900">Cash Shortage Predicted</h3>
                            <p className="text-sm text-amber-700 mt-1">
                                Based on current trends, a cash shortage of approximately ₹30,000 is predicted in Week 4.
                                Consider following up on overdue receivables or negotiating payment extensions.
                            </p>
                            <div className="flex gap-2 mt-3">
                                <Button size="sm" variant="warning">Follow Up on Receivables</Button>
                                <Button size="sm" variant="ghost">Request Payment Extension</Button>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Cash Flow Chart */}
            <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                        <TrendingUp className="w-5 h-5" />
                        Cash Flow Forecast (30 Days)
                    </CardTitle>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-emerald-500" />
                            <span className="text-sm text-slate-600">Inflow</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-red-500" />
                            <span className="text-sm text-slate-600">Outflow</span>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <CashFlowChart data={cashFlowData} />
                </CardContent>
            </Card>

            {/* Tabs */}
            <div className="flex gap-2 border-b border-slate-200">
                <button
                    className={`px-4 py-2 font-medium text-sm transition-colors ${
                        activeTab === 'receivables'
                            ? 'text-primary border-b-2 border-primary'
                            : 'text-slate-500 hover:text-slate-700'
                    }`}
                    onClick={() => setActiveTab('receivables')}
                >
                    Payment Collection ({overdueInvoices.length})
                </button>
                <button
                    className={`px-4 py-2 font-medium text-sm transition-colors ${
                        activeTab === 'payables'
                            ? 'text-primary border-b-2 border-primary'
                            : 'text-slate-500 hover:text-slate-700'
                    }`}
                    onClick={() => setActiveTab('payables')}
                >
                    Vendor Payments ({upcomingPayables.length})
                </button>
                <button
                    className={`px-4 py-2 font-medium text-sm transition-colors ${
                        activeTab === 'templates'
                            ? 'text-primary border-b-2 border-primary'
                            : 'text-slate-500 hover:text-slate-700'
                    }`}
                    onClick={() => setActiveTab('templates')}
                >
                    Email Templates
                </button>
            </div>

            {/* Receivables Tab */}
            {activeTab === 'receivables' && (
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle>Overdue Invoices</CardTitle>
                        <Button variant="outline" size="sm" icon={Filter}>Filter</Button>
                    </CardHeader>
                    <CardContent className="p-0">
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-slate-50 border-b border-slate-100">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Client</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Invoice</th>
                                        <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase">Amount</th>
                                        <th className="px-4 py-3 text-center text-xs font-medium text-slate-500 uppercase">Days Overdue</th>
                                        <th className="px-4 py-3 text-center text-xs font-medium text-slate-500 uppercase">Status</th>
                                        <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {overdueInvoices.map((invoice) => (
                                        <tr key={invoice.id} className="hover:bg-slate-50">
                                            <td className="px-4 py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center">
                                                        <Building2 className="w-5 h-5 text-slate-400" />
                                                    </div>
                                                    <div>
                                                        <p className="font-medium text-slate-800">{invoice.client}</p>
                                                        <p className="text-xs text-slate-500">{invoice.contactPerson}</p>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-4 py-4">
                                                <p className="text-sm text-slate-800">{invoice.invoiceNo}</p>
                                                <p className="text-xs text-slate-500">Due: {invoice.dueDate}</p>
                                            </td>
                                            <td className="px-4 py-4 text-right">
                                                <p className="font-semibold text-slate-800">₹{invoice.amount.toLocaleString()}</p>
                                            </td>
                                            <td className="px-4 py-4 text-center">
                                                <span className={`font-semibold ${
                                                    invoice.daysOverdue > 20 ? 'text-red-600' :
                                                    invoice.daysOverdue > 10 ? 'text-amber-600' : 'text-slate-600'
                                                }`}>
                                                    {invoice.daysOverdue} days
                                                </span>
                                            </td>
                                            <td className="px-4 py-4 text-center">
                                                {getStatusBadge(invoice.status)}
                                            </td>
                                            <td className="px-4 py-4">
                                                <div className="flex items-center justify-end gap-2">
                                                    <Button 
                                                        size="sm" 
                                                        variant="ghost"
                                                        onClick={() => openEmailModal(invoice, 'polite')}
                                                    >
                                                        <Eye className="w-4 h-4" />
                                                    </Button>
                                                    <Button 
                                                        size="sm"
                                                        onClick={() => openEmailModal(invoice, invoice.daysOverdue > 20 ? 'urgent' : 'polite')}
                                                    >
                                                        <Mail className="w-4 h-4 mr-1" />
                                                        Follow Up
                                                    </Button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Payables Tab */}
            {activeTab === 'payables' && (
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle>Upcoming Payables</CardTitle>
                        <Button variant="outline" size="sm" icon={Filter}>Filter</Button>
                    </CardHeader>
                    <CardContent className="p-0">
                        <div className="divide-y divide-slate-100">
                            {upcomingPayables.map((payable) => (
                                <div key={payable.id} className="p-4 hover:bg-slate-50">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-4">
                                            <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center">
                                                <Building2 className="w-6 h-6 text-slate-400" />
                                            </div>
                                            <div>
                                                <p className="font-medium text-slate-800">{payable.vendor}</p>
                                                <p className="text-sm text-slate-500">{payable.invoiceNo}</p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="font-semibold text-slate-800">₹{payable.amount.toLocaleString()}</p>
                                            <p className={`text-sm ${
                                                payable.daysUntilDue <= 3 ? 'text-red-600' : 'text-slate-500'
                                            }`}>
                                                Due in {payable.daysUntilDue} days
                                            </p>
                                        </div>
                                    </div>
                                    {payable.aiSuggestion && (
                                        <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-100">
                                            <div className="flex items-center gap-2">
                                                <Sparkles className="w-4 h-4 text-blue-600" />
                                                <span className="text-sm text-blue-800 font-medium">AI Suggestion:</span>
                                            </div>
                                            <p className="text-sm text-blue-700 mt-1">{payable.aiSuggestion}</p>
                                            <Button size="sm" variant="ghost" className="mt-2 text-blue-700">
                                                Generate Extension Request
                                            </Button>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Templates Tab */}
            {activeTab === 'templates' && (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {emailTemplates.map((template) => (
                        <Card key={template.id} className="hover:shadow-md transition-shadow cursor-pointer">
                            <CardContent className="pt-6">
                                <div className="flex items-start gap-3">
                                    <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                                        <FileText className="w-5 h-5 text-primary" />
                                    </div>
                                    <div className="flex-1">
                                        <h4 className="font-medium text-slate-800">{template.name}</h4>
                                        <Badge variant={
                                            template.tone === 'polite' ? 'success' :
                                            template.tone === 'firm' ? 'warning' : 'danger'
                                        } size="sm" className="mt-2">
                                            {template.tone}
                                        </Badge>
                                    </div>
                                </div>
                                <div className="flex gap-2 mt-4">
                                    <Button size="sm" variant="ghost" className="flex-1">
                                        <Eye className="w-4 h-4 mr-1" />
                                        Preview
                                    </Button>
                                    <Button size="sm" variant="outline" className="flex-1">
                                        <Copy className="w-4 h-4 mr-1" />
                                        Use
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}

            {/* Email Modal */}
            <Modal
                isOpen={showEmailModal}
                onClose={() => {
                    setShowEmailModal(false);
                    setSelectedInvoice(null);
                }}
                title="AI-Generated Email"
                description={selectedInvoice ? `Follow up with ${selectedInvoice.client}` : ''}
                size="lg"
            >
                {selectedInvoice && (
                    <div className="space-y-4">
                        {/* Tone Selector */}
                        <div>
                            <label className="text-sm font-medium text-slate-700 mb-2 block">Email Tone</label>
                            <div className="flex gap-2">
                                {['polite', 'firm', 'urgent'].map((tone) => (
                                    <button
                                        key={tone}
                                        onClick={() => {
                                            setEmailTone(tone);
                                            setEmailContent(generateEmail(selectedInvoice, tone));
                                        }}
                                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                                            emailTone === tone
                                                ? tone === 'polite' ? 'bg-emerald-100 text-emerald-700' :
                                                  tone === 'firm' ? 'bg-amber-100 text-amber-700' :
                                                  'bg-red-100 text-red-700'
                                                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                                        }`}
                                    >
                                        {tone.charAt(0).toUpperCase() + tone.slice(1)}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Recipient Info */}
                        <div className="p-4 bg-slate-50 rounded-lg">
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <span className="text-slate-500">To:</span>
                                    <span className="ml-2 font-medium text-slate-800">{selectedInvoice.email}</span>
                                </div>
                                <div>
                                    <span className="text-slate-500">Invoice:</span>
                                    <span className="ml-2 font-medium text-slate-800">{selectedInvoice.invoiceNo}</span>
                                </div>
                                <div>
                                    <span className="text-slate-500">Amount:</span>
                                    <span className="ml-2 font-medium text-slate-800">₹{selectedInvoice.amount.toLocaleString()}</span>
                                </div>
                                <div>
                                    <span className="text-slate-500">Overdue:</span>
                                    <span className="ml-2 font-medium text-red-600">{selectedInvoice.daysOverdue} days</span>
                                </div>
                            </div>
                        </div>

                        {/* Email Content */}
                        <div>
                            <label className="text-sm font-medium text-slate-700 mb-2 block">Email Content</label>
                            <textarea
                                value={emailContent}
                                onChange={(e) => setEmailContent(e.target.value)}
                                rows={12}
                                className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 text-sm font-mono"
                            />
                        </div>

                        {/* Actions */}
                        <div className="flex gap-3 pt-4 border-t border-slate-100">
                            <Button variant="outline" icon={RefreshCw} onClick={() => setEmailContent(generateEmail(selectedInvoice, emailTone))}>
                                Regenerate
                            </Button>
                            <Button variant="outline" icon={Edit3}>
                                Edit Subject
                            </Button>
                            <div className="flex-1" />
                            <Button variant="outline" onClick={() => setShowEmailModal(false)}>
                                Save Draft
                            </Button>
                            <Button icon={Send}>
                                Send Email
                            </Button>
                        </div>
                    </div>
                )}
            </Modal>
        </div>
    );
};

export default NegotiationCenter;
