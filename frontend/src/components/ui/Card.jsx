import React from 'react';
import { clsx } from 'clsx';

export const Card = ({ children, className, ...props }) => {
    return (
        <div
            className={clsx(
                'bg-white rounded-xl shadow-sm border border-slate-200',
                className
            )}
            {...props}
        >
            {children}
        </div>
    );
};

export const CardHeader = ({ children, className, ...props }) => {
    return (
        <div
            className={clsx('p-6 border-b border-slate-100', className)}
            {...props}
        >
            {children}
        </div>
    );
};

export const CardTitle = ({ children, className, ...props }) => {
    return (
        <h3
            className={clsx('text-lg font-semibold text-slate-800', className)}
            {...props}
        >
            {children}
        </h3>
    );
};

export const CardDescription = ({ children, className, ...props }) => {
    return (
        <p
            className={clsx('text-sm text-slate-500 mt-1', className)}
            {...props}
        >
            {children}
        </p>
    );
};

export const CardContent = ({ children, className, ...props }) => {
    return (
        <div className={clsx('p-6', className)} {...props}>
            {children}
        </div>
    );
};

export const CardFooter = ({ children, className, ...props }) => {
    return (
        <div
            className={clsx('p-6 pt-0 flex items-center', className)}
            {...props}
        >
            {children}
        </div>
    );
};

export default Card;
