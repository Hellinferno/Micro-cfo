import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
    LayoutDashboard,
    FileScan,
    Shield,
    Percent,
    MessageSquare,
    DollarSign,
    History,
    Settings,
    LogOut,
    Menu,
    X,
    ChevronDown,
    User
} from 'lucide-react';
import { Badge } from './ui/Badge';

const Sidebar = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    const menuItems = [
        { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
        { icon: FileScan, label: 'Scanner', path: '/scanner' },
        { icon: Shield, label: 'Compliance', path: '/compliance' },
        { icon: Percent, label: 'Subsidies', path: '/subsidies' },
        { icon: DollarSign, label: 'Negotiation', path: '/negotiation' },
        { icon: MessageSquare, label: 'Chat', path: '/chat' },
        { icon: History, label: 'History', path: '/history' },
        { icon: Settings, label: 'Settings', path: '/settings' }
    ];

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    };

    return (
        <>
            {/* Mobile Menu Button */}
            <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-md"
            >
                {mobileMenuOpen ? (
                    <X className="w-6 h-6 text-slate-600" />
                ) : (
                    <Menu className="w-6 h-6 text-slate-600" />
                )}
            </button>

            {/* Backdrop */}
            {mobileMenuOpen && (
                <div
                    className="lg:hidden fixed inset-0 bg-black/50 z-30"
                    onClick={() => setMobileMenuOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside
                className={`fixed lg:static inset-y-0 left-0 z-40 w-64 bg-white border-r border-slate-200 transform transition-transform duration-300 lg:transform-none ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
                    }`}
            >
                <div className="flex flex-col h-full">
                    {/* Logo */}
                    <div className="px-6 py-5 border-b border-slate-200">
                        <Link to="/" className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-gradient-to-r from-primary-600 to-primary-400 flex items-center justify-center">
                                <span className="text-white font-bold text-lg">M</span>
                            </div>
                            <div>
                                <h1 className="text-lg font-bold text-slate-900">MicroCFO</h1>
                                <p className="text-xs text-slate-500">AI Financial Assistant</p>
                            </div>
                        </Link>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
                        {menuItems.map((item) => {
                            const Icon = item.icon;
                            const isActive = location.pathname === item.path;

                            return (
                                <Link
                                    key={item.path}
                                    to={item.path}
                                    onClick={() => setMobileMenuOpen(false)}
                                    className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${isActive
                                            ? 'bg-primary-50 text-primary-700 font-medium'
                                            : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                                        }`}
                                >
                                    <Icon className={`w-5 h-5 ${isActive ? 'text-primary-600' : ''}`} />
                                    <span>{item.label}</span>
                                    {isActive && (
                                        <div className="ml-auto w-1.5 h-1.5 rounded-full bg-primary-600" />
                                    )}
                                </Link>
                            );
                        })}
                    </nav>

                    {/* User Profile */}
                    <div className="p-4 border-t border-slate-200">
                        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-slate-50">
                            <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
                                <User className="w-5 h-5 text-primary-600" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-slate-900 truncate">
                                    John Doe
                                </p>
                                <p className="text-xs text-slate-500 truncate">
                                    john@example.com
                                </p>
                            </div>
                            <ChevronDown className="w-4 h-4 text-slate-400" />
                        </div>
                        <button
                            onClick={handleLogout}
                            className="w-full flex items-center gap-3 px-4 py-3 mt-2 text-slate-600 hover:bg-red-50 hover:text-red-600 rounded-lg transition-colors"
                        >
                            <LogOut className="w-5 h-5" />
                            <span className="text-sm font-medium">Logout</span>
                        </button>
                    </div>
                </div>
            </aside>
        </>
    );
};

export default Sidebar;
