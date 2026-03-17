import React from 'react';
import { cn } from './Button';

/**
 * Card Component
 */
export const Card = ({ className = '', children, ...props }) => {
    return (
        <div
            className={cn(
                'bg-white rounded-xl shadow-sm border border-slate-200',
                className
            )}
            {...props}
        >
            {children}
        </div>
    );
};

/**
 * Card Header Component
 */
export const CardHeader = ({ className = '', children, ...props }) => {
    return (
        <div
            className={cn(
                'px-6 py-4 border-b border-slate-200',
                className
            )}
            {...props}
        >
            {children}
        </div>
    );
};

/**
 * Card Content Component
 */
export const CardContent = ({ className = '', children, ...props }) => {
    return (
        <div
            className={cn('p-6', className)}
            {...props}
        >
            {children}
        </div>
    );
};
