import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { MessageSquare, History, IndianRupee, Settings, Shield, Menu, X } from 'lucide-react';

const Sidebar = () => {
    const [isOpen, setIsOpen] = useState(false);

    const navItems = [
        { icon: MessageSquare, label: 'Chat', path: '/' },
        { icon: History, label: 'History', path: '/history' },
        { icon: IndianRupee, label: 'Subsidies', path: '/subsidies' },
        { icon: Settings, label: 'Settings', path: '/settings' },
    ];

    return (
        <>
            {/* Mobile Menu Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white rounded-md shadow-md text-primary-dark"
            >
                {isOpen ? <X size={24} /> : <Menu size={24} />}
            </button>

            {/* Sidebar Container */}
            <aside
                className={`fixed lg:static inset-y-0 left-0 z-40 w-64 bg-white border-r border-slate-200 transform transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
                    } flex flex-col`}
            >
                {/* Logo Section */}
                <div className="h-16 flex items-center px-6 border-b border-slate-100">
                    <div className="bg-primary/10 p-2 rounded-lg mr-3">
                        <Shield className="w-6 h-6 text-primary" />
                    </div>
                    <span className="text-xl font-bold text-slate-800">Micro-CFO</span>
                </div>

                {/* Navigation */}
                <nav className="flex-1 overflow-y-auto py-6 px-4 space-y-1">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            onClick={() => setIsOpen(false)}
                            className={({ isActive }) =>
                                `flex items-center px-4 py-3 rounded-xl transition-all duration-200 group ${isActive
                                    ? 'bg-primary text-white shadow-lg shadow-primary/20'
                                    : 'text-slate-500 hover:bg-slate-50 hover:text-primary-dark'
                                }`
                            }
                        >
                            <item.icon className={`w-5 h-5 mr-3 transition-colors ${
                                // isActive is handled by parent template, but icon needs specific styling sometimes
                                // Here inheritance works fine, but we can be specific if needed
                                ''
                                }`} />
                            <span className="font-medium">{item.label}</span>
                        </NavLink>
                    ))}
                </nav>

                {/* Mini-Stat Widget */}
                <div className="p-4 border-t border-slate-100 bg-slate-50/50">
                    <div className="bg-gradient-to-br from-primary-dark to-primary p-4 rounded-xl text-white shadow-lg shadow-primary/20 relative overflow-hidden">
                        {/* Background Pattern */}
                        <div className="absolute top-0 right-0 -mr-4 -mt-4 w-20 h-20 rounded-full bg-white/10 blur-xl"></div>

                        <p className="text-xs font-medium text-emerald-100 mb-1">Total Money Saved</p>
                        <h3 className="text-2xl font-bold mb-3">₹45,000</h3>

                        <div className="flex items-center text-xs bg-white/20 rounded-lg p-2 backdrop-blur-sm">
                            <div className="w-2 h-2 rounded-full bg-emerald-300 animate-pulse mr-2"></div>
                            <span>2 Pending Drafts</span>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Overlay for mobile */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/20 z-30 lg:hidden backdrop-blur-sm"
                    onClick={() => setIsOpen(false)}
                ></div>
            )}
        </>
    );
};

export default Sidebar;
