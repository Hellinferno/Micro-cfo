import React from 'react';
import { CheckCircle, ArrowRight, X } from 'lucide-react';

const ActionCard = ({ data }) => {
    return (
        <div className="flex w-full mb-4 justify-start">
            <div className="bg-white rounded-xl shadow-md border border-slate-100 overflow-hidden max-w-[85%] lg:max-w-[280px]">
                {/* Header */}
                <div className="bg-emerald-50 p-3 flex items-center border-b border-emerald-100">
                    <CheckCircle className="w-5 h-5 text-emerald-500 mr-2" />
                    <span className="text-sm font-bold text-emerald-800">Audit Passed</span>
                </div>

                {/* Content */}
                <div className="p-4">
                    <p className="text-sm text-slate-600 mb-4">{data.text || "I found a subsidy for this machine."}</p>

                    <div className="space-y-2">
                        <button className="w-full flex items-center justify-center bg-primary hover:bg-primary-dark text-white text-sm font-medium py-2 rounded-lg transition-colors">
                            <span>Apply Now</span>
                            <ArrowRight className="w-4 h-4 ml-1" />
                        </button>
                        <button className="w-full bg-slate-100 hover:bg-slate-200 text-slate-600 text-sm font-medium py-2 rounded-lg transition-colors">
                            Ignore
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ActionCard;
