import React from 'react';
import { Bot, User, FileText, Shield, Percent, DollarSign } from 'lucide-react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

const MessageBubble = ({ message, onActionClick }) => {
    const isUser = message.role === 'user';
    const isAssistant = message.role === 'assistant';

    const getAgentIcon = (agent) => {
        const icons = {
            visual_auditor: FileText,
            legal_sentinel: Shield,
            subsidy_hunter: Percent,
            negotiator: DollarSign,
            general: Bot
        };
        return icons[agent] || Bot;
    };

    const getAgentColor = (agent) => {
        const colors = {
            visual_auditor: 'bg-blue-500',
            legal_sentinel: 'bg-purple-500',
            subsidy_hunter: 'bg-green-500',
            negotiator: 'bg-orange-500',
            general: 'bg-slate-500'
        };
        return colors[agent] || colors.general;
    };

    const formatContent = (content) => {
        // Simple markdown-like formatting
        return content.split('\n').map((line, index) => (
            <React.Fragment key={index}>
                {line}
                {index < content.split('\n').length - 1 && <br />}
            </React.Fragment>
        ));
    };

    return (
        <div className={`flex gap-4 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
            {/* Avatar */}
            <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${isUser ? 'bg-primary-600' : getAgentColor(message.agent)
                }`}>
                {isUser ? (
                    <User className="w-5 h-5 text-white" />
                ) : (
                    React.createElement(getAgentIcon(message.agent), { className: 'w-5 h-5 text-white' })
                )}
            </div>

            {/* Message Content */}
            <div className={`flex flex-col max-w-2xl ${isUser ? 'items-end' : 'items-start'}`}>
                {/* Header */}
                {!isUser && (
                    <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-semibold text-slate-900">
                            {message.agent === 'visual_auditor' ? 'Visual Auditor' :
                                message.agent === 'legal_sentinel' ? 'Legal Sentinel' :
                                    message.agent === 'subsidy_hunter' ? 'Subsidy Hunter' :
                                        message.agent === 'negotiator' ? 'Negotiator' : 'MicroCFO'}
                        </span>
                        <Badge variant="info">{message.agent}</Badge>
                        <span className="text-xs text-slate-500">
                            {new Date(message.timestamp).toLocaleTimeString()}
                        </span>
                    </div>
                )}

                {/* Bubble */}
                <div className={`px-4 py-3 rounded-2xl ${isUser
                        ? 'bg-primary-600 text-white rounded-tr-sm'
                        : 'bg-white border border-slate-200 text-slate-900 rounded-tl-sm shadow-sm'
                    }`}>
                    <div className="text-sm whitespace-pre-wrap leading-relaxed">
                        {formatContent(message.content)}
                    </div>
                </div>

                {/* Suggested Actions */}
                {isAssistant && message.suggestedActions && message.suggestedActions.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                        {message.suggestedActions.map((action, index) => (
                            <Button
                                key={index}
                                size="sm"
                                variant="outline"
                                onClick={() => onActionClick(action)}
                                className="text-xs"
                            >
                                {action.label}
                            </Button>
                        ))}
                    </div>
                )}

                {/* Metadata */}
                {isAssistant && message.metadata && (
                    <div className="mt-2 text-xs text-slate-500">
                        {message.metadata.risk_level && (
                            <Badge variant={
                                message.metadata.risk_level === 'LOW' ? 'success' :
                                    message.metadata.risk_level === 'MEDIUM' ? 'warning' : 'danger'
                            }>
                                Risk: {message.metadata.risk_level}
                            </Badge>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default MessageBubble;
