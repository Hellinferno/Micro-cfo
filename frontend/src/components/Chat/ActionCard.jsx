import React from 'react';
import { CheckCircle, ArrowRight, AlertCircle, Info } from 'lucide-react';

const ActionCard = ({ data, onAction }) => {
    const { text, actions = [], type = 'success' } = data;
    
    const getIcon = () => {
        switch (type) {
            case 'success':
                return <CheckCircle className="w-5 h-5 text-emerald-500 mr-2" />;
            case 'warning':
                return <AlertCircle className="w-5 h-5 text-amber-500 mr-2" />;
            case 'info':
            default:
                return <Info className="w-5 h-5 text-blue-500 mr-2" />;
        }
    };
    
    const getHeaderStyle = () => {
        switch (type) {
            case 'success':
                return 'bg-emerald-50 border-emerald-100 text-emerald-800';
            case 'warning':
                return 'bg-amber-50 border-amber-100 text-amber-800';
            case 'info':
            default:
                return 'bg-blue-50 border-blue-100 text-blue-800';
        }
    };
    
    const getHeaderText = () => {
        switch (type) {
            case 'success':
                return 'Audit Passed';
            case 'warning':
                return 'Action Required';
            case 'info':
            default:
                return 'Information';
        }
    };
    
    const handleActionClick = (action) => {
        if (onAction) {
            onAction(action);
        }
    };

    return (
        <div className="flex w-full mb-4 justify-start animate-fade-in-up">
            <div className="bg-white rounded-xl shadow-md border border-slate-100 overflow-hidden max-w-[85%] lg:max-w-[320px]">
                {/* Header */}
                <div className={`p-3 flex items-center border-b ${getHeaderStyle()}`}>
                    {getIcon()}
                    <span className="text-sm font-bold">{getHeaderText()}</span>
                </div>

                {/* Content */}
                <div className="p-4">
                    <p className="text-sm text-slate-600 mb-4">{text}</p>

                    {actions.length > 0 && (
                        <div className="space-y-2">
                            {actions.map((action, index) => (
                                <button
                                    key={index}
                                    onClick={() => handleActionClick(action.action)}
                                    className={`w-full flex items-center justify-center text-sm font-medium py-2 rounded-lg transition-colors ${
                                        index === 0
                                            ? 'bg-primary hover:bg-primary-dark text-white'
                                            : 'bg-slate-100 hover:bg-slate-200 text-slate-600'
                                    }`}
                                >
                                    <span>{action.label}</span>
                                    {index === 0 && <ArrowRight className="w-4 h-4 ml-1" />}
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ActionCard;
