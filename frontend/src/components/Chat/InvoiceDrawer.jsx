import React, { useState } from 'react';
import { X, Save, AlertTriangle, CheckCircle, Calendar, DollarSign, Building } from 'lucide-react';

const InvoiceDrawer = ({ invoice, onClose, onSave }) => {
    const [formData, setFormData] = useState(invoice || {});

    if (!invoice) return null;

    const handleChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    return (
        <div className="w-96 flex-shrink-0 border-l border-slate-200 bg-white h-full flex flex-col shadow-2xl z-20 transition-all duration-300">
            {/* Header */}
            <div className="p-4 border-b border-slate-700 bg-corporate text-white flex justify-between items-center shadow-md">
                <div className="flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                    <h3 className="font-semibold tracking-wide">Invoice Audit</h3>
                </div>
                <button
                    onClick={onClose}
                    className="p-1 hover:bg-white/10 rounded-full transition-colors"
                >
                    <X size={20} />
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-5 space-y-6">

                {/* Confidence Widget */}
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 flex justify-between items-center">
                    <span className="text-sm text-slate-500 font-medium">AI Confidence</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-bold ${(formData.confidence_score || 0) > 0.8
                            ? 'bg-emerald-100 text-emerald-700'
                            : 'bg-amber-100 text-amber-700'
                        }`}>
                        {Math.round((formData.confidence_score || 0) * 100)}%
                    </span>
                </div>

                {/* Vendor Details */}
                <div className="space-y-3">
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                        <Building size={12} /> Vendor Details
                    </label>
                    <div className="space-y-2">
                        <div>
                            <span className="text-xs text-slate-400">Vendor Name</span>
                            <input
                                type="text"
                                value={formData.vendor_name || ''}
                                onChange={(e) => handleChange('vendor_name', e.target.value)}
                                className="w-full text-sm font-semibold text-slate-800 border border-slate-200 rounded-md p-2 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                            />
                        </div>
                        <div>
                            <span className="text-xs text-slate-400">GSTIN</span>
                            <input
                                type="text"
                                value={formData.gstin || ''}
                                onChange={(e) => handleChange('gstin', e.target.value)}
                                className="w-full text-sm font-mono text-slate-600 border border-slate-200 rounded-md p-2 focus:ring-2 focus:ring-primary outline-none"
                                placeholder="Missing"
                            />
                        </div>
                    </div>
                </div>

                {/* Financials */}
                <div className="space-y-3">
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                        <DollarSign size={12} /> Financials
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                        <div className="col-span-2">
                            <span className="text-xs text-slate-400">Total Amount</span>
                            <div className="relative">
                                <span className="absolute left-3 top-2 text-slate-400">₹</span>
                                <input
                                    type="number"
                                    value={formData.total_amount || 0}
                                    onChange={(e) => handleChange('total_amount', parseFloat(e.target.value))}
                                    className="w-full text-lg font-bold text-corporate pl-7 border border-slate-200 rounded-md p-2 focus:ring-2 focus:ring-primary outline-none"
                                />
                            </div>
                        </div>
                        <div>
                            <span className="text-xs text-slate-400">Date</span>
                            <div className="relative">
                                <input
                                    type="date"
                                    value={formData.invoice_date || ''}
                                    onChange={(e) => handleChange('invoice_date', e.target.value)}
                                    className="w-full text-sm text-slate-700 border border-slate-200 rounded-md p-2 focus:ring-2 focus:ring-primary outline-none"
                                />
                            </div>
                        </div>
                        <div>
                            <span className="text-xs text-slate-400">Tax</span>
                            <div className="relative">
                                <span className="absolute left-2 top-2 text-slate-400 text-xs">₹</span>
                                <input
                                    type="number"
                                    value={formData.tax_amount || 0}
                                    onChange={(e) => handleChange('tax_amount', parseFloat(e.target.value))}
                                    className="w-full text-sm text-slate-700 pl-5 border border-slate-200 rounded-md p-2 focus:ring-2 focus:ring-primary outline-none"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Compliance Flags */}
                {formData.compliance_flags && formData.compliance_flags.length > 0 && (
                    <div className="bg-red-50 p-3 rounded-lg border border-red-100">
                        <label className="text-xs font-bold text-red-700 uppercase tracking-wider flex items-center gap-1 mb-2">
                            <AlertTriangle size={12} /> Compliance Risks
                        </label>
                        <ul className="text-xs text-red-600 space-y-1 list-disc pl-4">
                            {formData.compliance_flags.map((flag, idx) => (
                                <li key={idx}>{flag}</li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-slate-200 bg-slate-50 flex gap-2">
                <button
                    onClick={onClose}
                    className="flex-1 py-2 px-4 border border-slate-300 rounded-lg text-slate-600 font-medium hover:bg-slate-100 transition-colors"
                >
                    Cancel
                </button>
                <button
                    onClick={() => onSave && onSave(formData)}
                    className="flex-1 py-2 px-4 bg-primary hover:bg-primary-dark text-white rounded-lg font-medium shadow-lg shadow-primary/20 flex items-center justify-center gap-2 transition-all"
                >
                    <Save size={18} />
                    Verify
                </button>
            </div>
        </div>
    );
};

export default InvoiceDrawer;
