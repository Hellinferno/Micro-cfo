import { useState } from 'react';
import { XMarkIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

const Disclaimer = ({ onAccept, onClose }) => {
    const [accepted, setAccepted] = useState(false);

    const handleAccept = () => {
        if (accepted) {
            onAccept();
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="sticky top-0 bg-amber-50 border-b border-amber-200 px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <ExclamationTriangleIcon className="h-8 w-8 text-amber-600" />
                        <h2 className="text-xl font-bold text-amber-900">Important Disclaimer</h2>
                    </div>
                    {onClose && (
                        <button
                            onClick={onClose}
                            className="text-amber-600 hover:text-amber-800 transition-colors"
                        >
                            <XMarkIcon className="h-6 w-6" />
                        </button>
                    )}
                </div>

                {/* Content */}
                <div className="px-6 py-6 space-y-4">
                    <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded">
                        <p className="text-amber-900 font-semibold text-lg mb-2">
                            Micro-CFO is an AI assistant, not a chartered accountant, lawyer, or financial advisor.
                        </p>
                    </div>

                    <div className="space-y-3 text-slate-700">
                        <p>
                            All outputs, recommendations, and analyses provided by this system are for{' '}
                            <strong>informational purposes only</strong> and must be verified by a qualified 
                            professional before taking any action.
                        </p>

                        <div className="bg-slate-50 p-4 rounded-lg space-y-2">
                            <p className="font-semibold text-slate-900">You should always:</p>
                            <ul className="list-disc list-inside space-y-1 ml-2">
                                <li>Verify all AI-generated outputs with qualified professionals</li>
                                <li>Consult with licensed chartered accountants for financial advice</li>
                                <li>Seek legal counsel for compliance and legal matters</li>
                                <li>Review all tax calculations with tax professionals</li>
                                <li>Never rely solely on AI for critical business decisions</li>
                            </ul>
                        </div>

                        <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
                            <p className="font-semibold text-red-900 mb-2">Important Limitations:</p>
                            <ul className="list-disc list-inside space-y-1 ml-2 text-red-800">
                                <li>AI may make errors in data extraction and analysis</li>
                                <li>Legal and tax information may be incomplete or outdated</li>
                                <li>Negotiation drafts are suggestions only - review before sending</li>
                                <li>Subsidy information must be verified with official sources</li>
                            </ul>
                        </div>

                        <p className="text-sm text-slate-600 italic">
                            Micro-CFO and its creators assume no liability for decisions made based on 
                            AI-generated information. Always consult with qualified professionals for 
                            advice specific to your situation.
                        </p>
                    </div>

                    {/* Acceptance Checkbox */}
                    <div className="border-t border-slate-200 pt-4 mt-6">
                        <label className="flex items-start gap-3 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={accepted}
                                onChange={(e) => setAccepted(e.target.checked)}
                                className="mt-1 h-5 w-5 text-blue-600 rounded border-slate-300 focus:ring-blue-500"
                            />
                            <span className="text-slate-700">
                                I understand that Micro-CFO is an AI assistant and not a substitute for 
                                professional advice. I will verify all outputs with qualified professionals 
                                before taking any action.
                            </span>
                        </label>
                    </div>
                </div>

                {/* Footer */}
                <div className="sticky bottom-0 bg-slate-50 border-t border-slate-200 px-6 py-4 flex justify-end gap-3">
                    {onClose && (
                        <button
                            onClick={onClose}
                            className="px-4 py-2 text-slate-700 hover:text-slate-900 font-medium transition-colors"
                        >
                            Cancel
                        </button>
                    )}
                    <button
                        onClick={handleAccept}
                        disabled={!accepted}
                        className={`px-6 py-2 rounded-lg font-medium transition-all ${
                            accepted
                                ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-md hover:shadow-lg'
                                : 'bg-slate-300 text-slate-500 cursor-not-allowed'
                        }`}
                    >
                        I Understand & Accept
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Disclaimer;
