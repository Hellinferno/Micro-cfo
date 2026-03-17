import React from 'react';
import { cn } from './Button';

/**
 * Progress Component
 * @param {Object} props
 * @param {number} props.value - Current progress value (0-100)
 * @param {string} props.variant - Progress variant (default, success, warning, danger)
 * @param {boolean} props.showLabel - Show percentage label
 * @param {string} props.className - Additional CSS classes
 */
export const Progress = ({
    value = 0,
    variant = 'default',
    showLabel = false,
    className = '',
    ...props
}) => {
    const baseStyles = 'w-full bg-slate-200 rounded-full h-2 overflow-hidden';

    const variants = {
        default: 'bg-primary-600',
        success: 'bg-green-600',
        warning: 'bg-yellow-600',
        danger: 'bg-red-600'
    };

    const normalizedValue = Math.min(Math.max(value, 0), 100);

    return (
        <div className={cn(baseStyles, className)} {...props}>
            {showLabel && (
                <div className="text-xs text-slate-600 mb-1 text-right">
                    {normalizedValue.toFixed(0)}%
                </div>
            )}
            <div
                className={cn('h-full transition-all duration-300', variants[variant])}
                style={{ width: `${normalizedValue}%` }}
            />
        </div>
    );
};
