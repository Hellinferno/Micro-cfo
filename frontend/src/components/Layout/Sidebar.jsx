import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { 
    LayoutDashboard,
    ScanLine, 
    Scale, 
    Search, 
    Banknote, 
    MessageSquare, 
    History, 
    Settings, 
    Shield, 
    Menu, 
    X,
    Upload
} from 'lucide-react';

const Sidebar = () => {
    const [isOpen, setIsOpen] = useState(false);

    const navItems = [
        { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
        { icon: ScanLine, label: 'Document Scanner', path: '/scanner' },
        { icon: Scale, label: 'Compliance', path: '/compliance' },
        { icon: Search, label: 'Subsidies', path: '/subsidies' },
        { icon: Banknote, label: 'Cash Flow', path: '/negotiation' },
        { icon: MessageSquare, label: 'AI Chat', path: '/chat' },
        { icon: History, label: 'History', path: '/history' },
        { icon: Settings, label: 'Settings', path: '/settings' },
    ];

    return (
        <>
            {/* Mobile Menu Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-corporate rounded-md shadow-md text-white"
            >
                {isOpen ? <X size={24} /> : <Menu size={24} />}
            </button>

            {/* Sidebar Container */}
            <aside
                className={`fixed lg:static inset-y-0 left-0 z-40 w-64 bg-corporate border-r border-slate-700 transform transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
                    } flex flex-col`}
            >
                {/* Logo Section */}
                <div className="h-16 flex items-center px-6 border-b border-slate-700">
                    <div className="bg-primary p-2 rounded-lg mr-3">
                        <Shield className="w-6 h-6 text-white" />
                    </div>
                    <span className="text-xl font-bold text-white tracking-wide">Micro-CFO</span>
                </div>

                {/* Main Action Button */}
                <div className="p-4">
                    <button className="w-full bg-primary hover:bg-primary-dark text-white font-semibold py-3 px-4 rounded-xl shadow-lg shadow-primary/20 flex items-center justify-center transition-all duration-200 group">
                        <span className="mr-2 text-lg">+</span>
                        Upload Invoice
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 overflow-y-auto px-3 space-y-1">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            onClick={() => setIsOpen(false)}
                            className={({ isActive }) =>
                                `flex items-center px-4 py-3 rounded-xl transition-all duration-200 group ${isActive
                                    ? 'bg-slate-800 text-white shadow-md border-l-4 border-primary'
                                    : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                                }`
                            }
                        >
                            <item.icon className="w-5 h-5 mr-3 transition-colors" />
                            <span className="font-medium">{item.label}</span>
                        </NavLink>
                    ))}
                </nav>

                {/* Mini-Stat Widget */}
                <div className="p-4 border-t border-slate-700 bg-slate-800/50">
                    <div className="bg-gradient-to-br from-primary-dark to-primary p-4 rounded-xl text-white shadow-lg shadow-primary/20 relative overflow-hidden">
                        {/* Background Pattern */}
                        <div className="absolute top-0 right-0 -mr-4 -mt-4 w-20 h-20 rounded-full bg-white/10 blur-xl"></div>

                        <p className="text-xs font-medium text-emerald-100 mb-1 opacity-90">Total Money Saved</p>
                        <h3 className="text-2xl font-bold mb-3 font-serif">₹45,000</h3>

                        <div className="flex items-center text-xs bg-white/20 rounded-lg p-2 backdrop-blur-sm border border-white/10">
                            <div className="w-2 h-2 rounded-full bg-emerald-300 animate-pulse mr-2"></div>
                            <span>2 Pending Drafts</span>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Overlay for mobile */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/60 z-30 lg:hidden backdrop-blur-sm"
                    onClick={() => setIsOpen(false)}
                ></div>
            )}
        </>
    );
};

export default Sidebar;
