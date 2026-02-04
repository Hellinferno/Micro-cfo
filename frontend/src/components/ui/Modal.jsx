import React, { useEffect } from 'react';
import { clsx } from 'clsx';
import { X } from 'lucide-react';

export const Modal = ({
    isOpen,
    onClose,
    title,
    description,
    children,
    size = 'md',
    className,
}) => {
    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = 'unset';
        }
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, [isOpen]);

    if (!isOpen) return null;

    const sizes = {
        sm: 'max-w-md',
        md: 'max-w-lg',
        lg: 'max-w-2xl',
        xl: 'max-w-4xl',
        full: 'max-w-full mx-4',
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Modal Content */}
            <div
                className={clsx(
                    'relative bg-white rounded-2xl shadow-xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col',
                    sizes[size],
                    className
                )}
            >
                {/* Header */}
                {(title || description) && (
                    <div className="p-6 border-b border-slate-100">
                        <div className="flex items-start justify-between">
                            <div>
                                {title && (
                                    <h2 className="text-xl font-semibold text-slate-800">
                                        {title}
                                    </h2>
                                )}
                                {description && (
                                    <p className="text-sm text-slate-500 mt-1">
                                        {description}
                                    </p>
                                )}
                            </div>
                            <button
                                onClick={onClose}
                                className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                            >
                                <X className="w-5 h-5 text-slate-400" />
                            </button>
                        </div>
                    </div>
                )}

                {/* Body */}
                <div className="flex-1 overflow-y-auto p-6">
                    {children}
                </div>
            </div>
        </div>
    );
};

export default Modal;
