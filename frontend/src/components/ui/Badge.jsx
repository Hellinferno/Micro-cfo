import React from 'react';
import { cn } from './Button';

/**
 * Badge Component
 * @param {Object} props
 * @param {string} props.variant - Badge variant (default, success, warning, danger, info)
 * @param {string} props.className - Additional CSS classes
 * @param {React.ReactNode} props.children - Badge content
 */
export const Badge = ({
    variant = 'default',
    className = '',
    children,
    ...props
}) => {
    const baseStyles = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium';

    const variants = {
        default: 'bg-slate-100 text-slate-800',
        success: 'bg-green-100 text-green-800',
        warning: 'bg-yellow-100 text-yellow-800',
        danger: 'bg-red-100 text-red-800',
        info: 'bg-blue-100 text-blue-800',
        outline: 'border border-slate-300 text-slate-700'
    };

    const classes = cn(
        baseStyles,
        variants[variant],
        className
    );

    return (
        <span className={classes} {...props}>
            {children}
        </span>
    );
};
