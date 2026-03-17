import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Utility function for merging Tailwind classes
export function cn(...inputs) {
    return twMerge(clsx(inputs));
}

/**
 * Button Component
 * @param {Object} props
 * @param {string} props.variant - Button variant (primary, secondary, outline, ghost, danger)
 * @param {string} props.size - Button size (sm, md, lg, icon)
 * @param {boolean} props.disabled - Disabled state
 * @param {string} props.className - Additional CSS classes
 * @param {React.ReactNode} props.children - Button content
 * @param {Function} props.onClick - Click handler
 */
export const Button = React.forwardRef(({
    variant = 'primary',
    size = 'md',
    disabled = false,
    className = '',
    children,
    onClick,
    type = 'button',
    ...props
}, ref) => {
    const baseStyles = 'inline-flex items-center justify-center font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg';

    const variants = {
        primary: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500',
        secondary: 'bg-secondary-600 text-white hover:bg-secondary-700 focus:ring-secondary-500',
        outline: 'border-2 border-slate-300 text-slate-700 hover:border-primary-500 hover:text-primary-600 bg-transparent focus:ring-primary-500',
        ghost: 'text-slate-700 hover:bg-slate-100 focus:ring-slate-500',
        danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
        link: 'text-primary-600 hover:underline focus:ring-primary-500'
    };

    const sizes = {
        sm: 'px-3 py-1.5 text-sm',
        md: 'px-4 py-2 text-base',
        lg: 'px-6 py-3 text-lg',
        icon: 'p-2'
    };

    const classes = cn(
        baseStyles,
        variants[variant],
        sizes[size],
        className
    );

    return (
        <button
            ref={ref}
            type={type}
            className={classes}
            disabled={disabled}
            onClick={onClick}
            {...props}
        >
            {children}
        </button>
    );
});

Button.displayName = 'Button';
