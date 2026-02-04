import React from 'react';
import { clsx } from 'clsx';

const variants = {
    default: 'bg-primary',
    success: 'bg-emerald-500',
    warning: 'bg-amber-500',
    danger: 'bg-red-500',
};

export const Progress = ({
    value = 0,
    max = 100,
    variant = 'default',
    size = 'md',
    showLabel = false,
    className,
    ...props
}) => {
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

    const heights = {
        sm: 'h-1.5',
        md: 'h-2.5',
        lg: 'h-4',
    };

    return (
        <div className={clsx('w-full', className)} {...props}>
            <div className={clsx('w-full bg-slate-200 rounded-full overflow-hidden', heights[size])}>
                <div
                    className={clsx(
                        'h-full rounded-full transition-all duration-500 ease-out',
                        variants[variant]
                    )}
                    style={{ width: `${percentage}%` }}
                />
            </div>
            {showLabel && (
                <span className="text-xs text-slate-500 mt-1 block text-right">
                    {Math.round(percentage)}%
                </span>
            )}
        </div>
    );
};

export default Progress;
