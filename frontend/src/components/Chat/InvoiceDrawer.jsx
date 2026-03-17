import React from 'react';

const InvoiceDrawer = ({ invoice, onClose }) => {
    if (!invoice) return null;

    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-end" onClick={onClose}>
            <div
                className="bg-white w-full max-w-md h-full overflow-y-auto shadow-2xl"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="border-b border-slate-200 px-6 py-4 flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-slate-900">Invoice Details</h2>
                    <button onClick={onClose} className="text-slate-500 hover:text-slate-700">
                        ✕
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-6">
                    {/* Invoice Info */}
                    <div>
                        <h3 className="text-sm font-semibold text-slate-900 mb-3">Invoice Information</h3>
                        <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                                <span className="text-slate-600">Vendor:</span>
                                <span className="font-medium text-slate-900">{invoice.vendor_name}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-slate-600">Date:</span>
                                <span className="font-medium text-slate-900">{invoice.invoice_date}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-slate-600">GSTIN:</span>
                                <span className="font-medium text-slate-900">{invoice.gstin || 'N/A'}</span>
                            </div>
                        </div>
                    </div>

                    {/* Amount Summary */}
                    <div className="bg-slate-50 p-4 rounded-lg">
                        <h3 className="text-sm font-semibold text-slate-900 mb-3">Amount Summary</h3>
                        <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                                <span className="text-slate-600">Total Amount:</span>
                                <span className="font-semibold text-slate-900">₹{invoice.total_amount.toLocaleString('en-IN')}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-slate-600">Tax Amount:</span>
                                <span className="font-medium text-slate-900">₹{invoice.tax_amount.toLocaleString('en-IN')}</span>
                            </div>
                        </div>
                    </div>

                    {/* Line Items */}
                    {invoice.line_items && invoice.line_items.length > 0 && (
                        <div>
                            <h3 className="text-sm font-semibold text-slate-900 mb-3">Line Items</h3>
                            <div className="space-y-2">
                                {invoice.line_items.map((item, index) => (
                                    <div key={index} className="p-3 bg-slate-50 rounded-lg">
                                        <div className="flex justify-between mb-1">
                                            <span className="text-sm font-medium text-slate-900">{item.description}</span>
                                            <span className="text-sm font-semibold text-slate-900">₹{item.amount.toLocaleString('en-IN')}</span>
                                        </div>
                                        <Badge variant="info">{item.category}</Badge>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Compliance Status */}
                    <div>
                        <h3 className="text-sm font-semibold text-slate-900 mb-3">Compliance Status</h3>
                        <div className="space-y-2">
                            {invoice.is_handwritten && (
                                <div className="flex items-center gap-2 text-sm text-yellow-700 bg-yellow-50 p-2 rounded">
                                    <span>⚠️</span>
                                    <span>Handwritten invoice - verify authenticity</span>
                                </div>
                            )}
                            {invoice.tampering_detected && (
                                <div className="flex items-center gap-2 text-sm text-red-700 bg-red-50 p-2 rounded">
                                    <span>🚨</span>
                                    <span>Tampering detected - manual verification required</span>
                                </div>
                            )}
                            {!invoice.gstin && invoice.tax_amount > 0 && (
                                <div className="flex items-center gap-2 text-sm text-red-700 bg-red-50 p-2 rounded">
                                    <span>⚠️</span>
                                    <span>Tax charged without GSTIN - compliance risk</span>
                                </div>
                            )}
                            {invoice.compliance_flags && invoice.compliance_flags.length > 0 ? (
                                invoice.compliance_flags.map((flag, index) => (
                                    <div key={index} className="flex items-center gap-2 text-sm text-red-700 bg-red-50 p-2 rounded">
                                        <span>⚠️</span>
                                        <span>{flag}</span>
                                    </div>
                                ))
                            ) : (
                                <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 p-2 rounded">
                                    <span>✅</span>
                                    <span>No compliance issues detected</span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Confidence Score */}
                    <div>
                        <div className="flex justify-between mb-2">
                            <span className="text-sm font-semibold text-slate-900">Confidence Score</span>
                            <span className="text-sm font-medium text-slate-900">{(invoice.confidence_score * 100).toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-slate-200 rounded-full h-2">
                            <div
                                className="bg-primary-600 h-2 rounded-full transition-all"
                                style={{ width: `${invoice.confidence_score * 100}%` }}
                            />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default InvoiceDrawer;
