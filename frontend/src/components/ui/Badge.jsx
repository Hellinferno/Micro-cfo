import React from 'react';
import { clsx } from 'clsx';

const variants = {
    default: 'bg-slate-100 text-slate-700',
    primary: 'bg-primary/10 text-primary',
    success: 'bg-emerald-100 text-emerald-700',
    warning: 'bg-amber-100 text-amber-700',
    danger: 'bg-red-100 text-red-700',
    info: 'bg-blue-100 text-blue-700',
};

const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs',
    lg: 'px-3 py-1.5 text-sm',
};

export const Badge = ({
    children,
    variant = 'default',
    size = 'md',
    className,
    dot,
    ...props
}) => {
    return (
        <span
            className={clsx(
                'inline-flex items-center font-medium rounded-full',
                variants[variant],
                sizes[size],
                className
            )}
            {...props}
        >
            {dot && (
                <span
                    className={clsx(
                        'w-1.5 h-1.5 rounded-full mr-1.5',
                        variant === 'success' && 'bg-emerald-500',
                        variant === 'warning' && 'bg-amber-500',
                        variant === 'danger' && 'bg-red-500',
                        variant === 'info' && 'bg-blue-500',
                        variant === 'primary' && 'bg-primary',
                        variant === 'default' && 'bg-slate-500'
                    )}
                />
            )}
            {children}
        </span>
    );
};

export default Badge;
