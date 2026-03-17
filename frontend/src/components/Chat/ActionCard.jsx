import React from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

const ActionCard = ({ title, description, actions, metadata }) => {
    return (
        <Card className="mt-4 bg-slate-50 border-slate-200">
            <div className="p-4">
                <h3 className="font-semibold text-slate-900 mb-2">{title}</h3>
                {description && (
                    <p className="text-sm text-slate-600 mb-3">{description}</p>
                )}

                {metadata && (
                    <div className="mb-3 space-y-2">
                        {Object.entries(metadata).map(([key, value]) => (
                            <div key={key} className="flex justify-between text-sm">
                                <span className="text-slate-600 capitalize">{key.replace(/_/g, ' ')}:</span>
                                <span className="font-medium text-slate-900">{value}</span>
                            </div>
                        ))}
                    </div>
                )}

                {actions && actions.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                        {actions.map((action, index) => (
                            <Button
                                key={index}
                                size="sm"
                                variant={action.primary ? 'primary' : 'outline'}
                                onClick={action.handler}
                            >
                                {action.label}
                            </Button>
                        ))}
                    </div>
                )}
            </div>
        </Card>
    );
};

export default ActionCard;
