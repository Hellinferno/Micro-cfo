import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    AreaChart, Area, PieChart, Pie, Cell, BarChart, Bar
} from 'recharts';
import {
    Users, FileText, CheckCircle, AlertTriangle, Download, Filter,
    Search, MoreHorizontal, ArrowUpRight, ArrowDownRight, RefreshCw,
    Shield, Settings, Database, Server, Activity, Zap, Globe,
    CreditCard, TrendingUp, UserPlus, Lock, Eye, Trash2, Edit,
    LogOut, Bell, Moon, Sun, ChevronDown, BarChart2
} from 'lucide-react';

const COLORS = ['#10B981', '#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444'];

const SuperAdminDashboard = () => {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState('overview');
    const [darkMode, setDarkMode] = useState(true);
    const [stats, setStats] = useState(null);
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedUsers, setSelectedUsers] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [showUserModal, setShowUserModal] = useState(false);
    const [selectedUser, setSelectedUser] = useState(null);

    // Check admin auth
    useEffect(() => {
        const adminAuth = localStorage.getItem('adminAuth');
        if (!adminAuth) {
            navigate('/admin/login');
            return;
        }
        const auth = JSON.parse(adminAuth);
        if (auth.role !== 'admin' && auth.role !== 'superadmin') {
            navigate('/admin/login');
        }
    }, [navigate]);

    // Mock data
    const systemMetrics = {
        cpu: 45,
        memory: 62,
        storage: 38,
        bandwidth: 78
    };

    const revenueData = [
        { month: 'Jul', revenue: 12000, users: 45 },
        { month: 'Aug', revenue: 19000, users: 62 },
        { month: 'Sep', revenue: 27000, users: 89 },
        { month: 'Oct', revenue: 35000, users: 124 },
        { month: 'Nov', revenue: 48000, users: 178 },
        { month: 'Dec', revenue: 62000, users: 235 },
        { month: 'Jan', revenue: 78000, users: 312 },
    ];

    const userDistribution = [
        { name: 'IT Services', value: 35 },
        { name: 'Retail', value: 25 },
        { name: 'Manufacturing', value: 20 },
        { name: 'Services', value: 15 },
        { name: 'Others', value: 5 },
    ];

    const apiUsageData = [
        { name: 'Visual Auditor', calls: 4500 },
        { name: 'Legal Sentinel', calls: 3200 },
        { name: 'Subsidy Hunter', calls: 2800 },
        { name: 'Negotiator', calls: 1900 },
        { name: 'WhatsApp', calls: 3600 },
    ];

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 500));
        
        setStats({
            total_users: 312,
            active_users_24h: 89,
            total_invoices_processed: 4562,
            total_revenue: 78000,
            api_calls_today: 15420,
            system_health: 'OPERATIONAL',
            uptime: '99.97%'
        });
        
        setUsers([
            { id: 1, full_name: 'Rahul Sharma', email: 'rahul@techstart.in', company_name: 'TechStart', business_sector: 'IT Services', invoice_count: 145, is_active: true, plan: 'Pro', created_at: '2025-08-15' },
            { id: 2, full_name: 'Priya Patel', email: 'priya@freshfoods.com', company_name: 'Fresh Foods', business_sector: 'Retail', invoice_count: 89, is_active: true, plan: 'Business', created_at: '2025-09-22' },
            { id: 3, full_name: 'Amit Kumar', email: 'amit@logistics.co', company_name: 'Fast Logistics', business_sector: 'Transport', invoice_count: 278, is_active: false, plan: 'Enterprise', created_at: '2025-07-10' },
            { id: 4, full_name: 'Sneha Gupta', email: 'sneha@creative.io', company_name: 'Creative Studio', business_sector: 'Design', invoice_count: 56, is_active: true, plan: 'Pro', created_at: '2025-10-05' },
            { id: 5, full_name: 'Vikram Singh', email: 'vikram@autoparts.com', company_name: 'AutoParts India', business_sector: 'Manufacturing', invoice_count: 312, is_active: true, plan: 'Enterprise', created_at: '2025-06-18' },
        ]);
        
        setLoading(false);
    };

    const handleLogout = () => {
        localStorage.removeItem('adminAuth');
        navigate('/admin/login');
    };

    const toggleUserStatus = (userId) => {
        setUsers(users.map(user => 
            user.id === userId ? { ...user, is_active: !user.is_active } : user
        ));
    };

    const filteredUsers = users.filter(user =>
        user.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        user.company_name?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const StatCard = ({ icon: Icon, title, value, subtitle, trend, trendUp, color, onClick }) => (
        <div 
            onClick={onClick}
            className={`bg-slate-800/50 backdrop-blur-sm p-6 rounded-xl border border-slate-700/50 hover:border-slate-600/50 transition-all cursor-pointer group ${onClick ? 'hover:scale-[1.02]' : ''}`}
        >
            <div className="flex items-start justify-between">
                <div className={`p-3 rounded-xl ${color} bg-opacity-10`}>
                    <Icon className={color} size={24} />
                </div>
                {trend && (
                    <span className={`flex items-center text-sm font-medium ${trendUp ? 'text-emerald-400' : 'text-red-400'}`}>
                        {trendUp ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                        {trend}
                    </span>
                )}
            </div>
            <h3 className="text-3xl font-bold text-white mt-4">{value}</h3>
            <p className="text-slate-400 text-sm mt-1">{title}</p>
            {subtitle && <p className="text-slate-500 text-xs mt-1">{subtitle}</p>}
        </div>
    );

    const SystemHealthCard = ({ label, value, color }) => (
        <div className="flex items-center justify-between py-3 border-b border-slate-700/30 last:border-0">
            <span className="text-slate-400 text-sm">{label}</span>
            <div className="flex items-center gap-3">
                <div className="w-32 bg-slate-700/30 rounded-full h-2">
                    <div 
                        className={`h-2 rounded-full ${color}`}
                        style={{ width: `${value}%` }}
                    />
                </div>
                <span className="text-white text-sm font-medium w-12 text-right">{value}%</span>
            </div>
        </div>
    );

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
            {/* Top Navigation */}
            <nav className="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700/50 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="bg-gradient-to-br from-amber-500 to-orange-600 p-2 rounded-xl">
                            <Shield className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-white">Super Admin</h1>
                            <p className="text-xs text-slate-400">MicroCFO Control Center</p>
                        </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                        <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-all relative">
                            <Bell size={20} />
                            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                        </button>
                        <button 
                            onClick={() => setDarkMode(!darkMode)}
                            className="p-2 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-all"
                        >
                            {darkMode ? <Sun size={20} /> : <Moon size={20} />}
                        </button>
                        <div className="h-6 w-px bg-slate-700"></div>
                        <button 
                            onClick={handleLogout}
                            className="flex items-center gap-2 px-4 py-2 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-all"
                        >
                            <LogOut size={18} />
                            Logout
                        </button>
                    </div>
                </div>
            </nav>

            {/* Tab Navigation */}
            <div className="max-w-7xl mx-auto px-6 py-4">
                <div className="flex gap-2 bg-slate-800/30 p-1 rounded-xl w-fit">
                    {['overview', 'users', 'analytics', 'system', 'settings'].map(tab => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-all ${
                                activeTab === tab 
                                    ? 'bg-amber-500 text-white shadow-lg shadow-amber-500/20' 
                                    : 'text-slate-400 hover:text-white'
                            }`}
                        >
                            {tab}
                        </button>
                    ))}
                </div>
            </div>

            {/* Main Content */}
            <div className="max-w-7xl mx-auto px-6 pb-12">
                {activeTab === 'overview' && (
                    <>
                        {/* Stats Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                            <StatCard 
                                icon={Users} 
                                title="Total Users" 
                                value={stats?.total_users || 0}
                                trend="+23%"
                                trendUp={true}
                                color="text-blue-400"
                            />
                            <StatCard 
                                icon={CreditCard} 
                                title="Monthly Revenue" 
                                value={`₹${(stats?.total_revenue || 0).toLocaleString()}`}
                                trend="+18%"
                                trendUp={true}
                                color="text-emerald-400"
                            />
                            <StatCard 
                                icon={FileText} 
                                title="Invoices Processed" 
                                value={stats?.total_invoices_processed || 0}
                                trend="+45%"
                                trendUp={true}
                                color="text-purple-400"
                            />
                            <StatCard 
                                icon={Zap} 
                                title="API Calls Today" 
                                value={(stats?.api_calls_today || 0).toLocaleString()}
                                subtitle={`Uptime: ${stats?.uptime || '99.9%'}`}
                                color="text-amber-400"
                            />
                        </div>

                        {/* Charts Row */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                            {/* Revenue Chart */}
                            <div className="lg:col-span-2 bg-slate-800/50 backdrop-blur-sm p-6 rounded-xl border border-slate-700/50">
                                <div className="flex justify-between items-center mb-6">
                                    <h3 className="text-lg font-semibold text-white">Revenue & User Growth</h3>
                                    <button className="text-slate-400 hover:text-white text-sm flex items-center gap-1">
                                        Last 7 Months <ChevronDown size={16} />
                                    </button>
                                </div>
                                <div className="h-72">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <AreaChart data={revenueData}>
                                            <defs>
                                                <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                                                    <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                                                </linearGradient>
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                            <XAxis dataKey="month" stroke="#64748b" />
                                            <YAxis stroke="#64748b" />
                                            <Tooltip 
                                                contentStyle={{ 
                                                    backgroundColor: '#1e293b', 
                                                    border: '1px solid #334155',
                                                    borderRadius: '8px'
                                                }}
                                            />
                                            <Area type="monotone" dataKey="revenue" stroke="#10B981" strokeWidth={3} fillOpacity={1} fill="url(#colorRevenue)" />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            {/* User Distribution */}
                            <div className="bg-slate-800/50 backdrop-blur-sm p-6 rounded-xl border border-slate-700/50">
                                <h3 className="text-lg font-semibold text-white mb-6">User Distribution</h3>
                                <div className="h-48">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie
                                                data={userDistribution}
                                                cx="50%"
                                                cy="50%"
                                                innerRadius={50}
                                                outerRadius={80}
                                                paddingAngle={5}
                                                dataKey="value"
                                            >
                                                {userDistribution.map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                                ))}
                                            </Pie>
                                            <Tooltip />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>
                                <div className="mt-4 space-y-2">
                                    {userDistribution.map((item, index) => (
                                        <div key={item.name} className="flex items-center justify-between text-sm">
                                            <div className="flex items-center gap-2">
                                                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index] }} />
                                                <span className="text-slate-400">{item.name}</span>
                                            </div>
                                            <span className="text-white font-medium">{item.value}%</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* System Health & API Usage */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {/* System Health */}
                            <div className="bg-slate-800/50 backdrop-blur-sm p-6 rounded-xl border border-slate-700/50">
                                <div className="flex items-center justify-between mb-6">
                                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                        <Server size={20} className="text-emerald-400" />
                                        System Health
                                    </h3>
                                    <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-medium rounded-full">
                                        {stats?.system_health}
                                    </span>
                                </div>
                                <div className="space-y-1">
                                    <SystemHealthCard label="CPU Usage" value={systemMetrics.cpu} color="bg-blue-400" />
                                    <SystemHealthCard label="Memory" value={systemMetrics.memory} color="bg-purple-400" />
                                    <SystemHealthCard label="Storage" value={systemMetrics.storage} color="bg-emerald-400" />
                                    <SystemHealthCard label="Bandwidth" value={systemMetrics.bandwidth} color="bg-amber-400" />
                                </div>
                            </div>

                            {/* API Usage */}
                            <div className="bg-slate-800/50 backdrop-blur-sm p-6 rounded-xl border border-slate-700/50">
                                <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                                    <BarChart2 size={20} className="text-purple-400" />
                                    API Usage by Agent
                                </h3>
                                <div className="h-56">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={apiUsageData} layout="vertical">
                                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                                            <XAxis type="number" stroke="#64748b" />
                                            <YAxis dataKey="name" type="category" stroke="#64748b" width={100} />
                                            <Tooltip 
                                                contentStyle={{ 
                                                    backgroundColor: '#1e293b', 
                                                    border: '1px solid #334155',
                                                    borderRadius: '8px'
                                                }}
                                            />
                                            <Bar dataKey="calls" fill="#8B5CF6" radius={[0, 4, 4, 0]} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        </div>
                    </>
                )}

                {activeTab === 'users' && (
                    <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50">
                        {/* Users Header */}
                        <div className="p-6 border-b border-slate-700/50">
                            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                                <h3 className="text-lg font-semibold text-white">User Management</h3>
                                <div className="flex gap-3">
                                    <div className="relative">
                                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                        <input
                                            type="text"
                                            placeholder="Search users..."
                                            value={searchQuery}
                                            onChange={(e) => setSearchQuery(e.target.value)}
                                            className="pl-10 pr-4 py-2 bg-slate-900/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-500 focus:border-amber-500 focus:ring-1 focus:ring-amber-500/20 outline-none w-64"
                                        />
                                    </div>
                                    <button className="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg transition-colors">
                                        <UserPlus size={18} />
                                        Add User
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Users Table */}
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-slate-700/50">
                                        <th className="text-left p-4 text-slate-400 font-medium text-sm">User</th>
                                        <th className="text-left p-4 text-slate-400 font-medium text-sm">Company</th>
                                        <th className="text-left p-4 text-slate-400 font-medium text-sm">Sector</th>
                                        <th className="text-left p-4 text-slate-400 font-medium text-sm">Plan</th>
                                        <th className="text-left p-4 text-slate-400 font-medium text-sm">Invoices</th>
                                        <th className="text-left p-4 text-slate-400 font-medium text-sm">Status</th>
                                        <th className="text-right p-4 text-slate-400 font-medium text-sm">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredUsers.map(user => (
                                        <tr key={user.id} className="border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors">
                                            <td className="p-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white font-bold">
                                                        {user.full_name?.charAt(0)}
                                                    </div>
                                                    <div>
                                                        <p className="text-white font-medium">{user.full_name}</p>
                                                        <p className="text-slate-400 text-sm">{user.email}</p>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="p-4 text-slate-300">{user.company_name}</td>
                                            <td className="p-4 text-slate-400">{user.business_sector}</td>
                                            <td className="p-4">
                                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                                    user.plan === 'Enterprise' ? 'bg-purple-500/10 text-purple-400' :
                                                    user.plan === 'Business' ? 'bg-blue-500/10 text-blue-400' :
                                                    'bg-slate-500/10 text-slate-400'
                                                }`}>
                                                    {user.plan}
                                                </span>
                                            </td>
                                            <td className="p-4 text-slate-300">{user.invoice_count}</td>
                                            <td className="p-4">
                                                <button
                                                    onClick={() => toggleUserStatus(user.id)}
                                                    className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                                                        user.is_active 
                                                            ? 'bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20' 
                                                            : 'bg-red-500/10 text-red-400 hover:bg-red-500/20'
                                                    }`}
                                                >
                                                    {user.is_active ? 'Active' : 'Inactive'}
                                                </button>
                                            </td>
                                            <td className="p-4">
                                                <div className="flex items-center justify-end gap-2">
                                                    <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-all">
                                                        <Eye size={16} />
                                                    </button>
                                                    <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-all">
                                                        <Edit size={16} />
                                                    </button>
                                                    <button className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all">
                                                        <Trash2 size={16} />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {activeTab === 'system' && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Database Status */}
                        <div className="bg-slate-800/50 backdrop-blur-sm p-6 rounded-xl border border-slate-700/50">
                            <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                                <Database size={20} className="text-blue-400" />
                                Database Status
                            </h3>
                            <div className="space-y-4">
                                <div className="flex justify-between items-center p-4 bg-slate-900/30 rounded-lg">
                                    <span className="text-slate-400">PostgreSQL</span>
                                    <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-medium rounded-full">Connected</span>
                                </div>
                                <div className="flex justify-between items-center p-4 bg-slate-900/30 rounded-lg">
                                    <span className="text-slate-400">Redis Cache</span>
                                    <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-medium rounded-full">Connected</span>
                                </div>
                                <div className="flex justify-between items-center p-4 bg-slate-900/30 rounded-lg">
                                    <span className="text-slate-400">ChromaDB (Vector)</span>
                                    <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-medium rounded-full">Connected</span>
                                </div>
                            </div>
                        </div>

                        {/* API Keys Status */}
                        <div className="bg-slate-800/50 backdrop-blur-sm p-6 rounded-xl border border-slate-700/50">
                            <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                                <Lock size={20} className="text-amber-400" />
                                API Keys Status
                            </h3>
                            <div className="space-y-4">
                                <div className="flex justify-between items-center p-4 bg-slate-900/30 rounded-lg">
                                    <span className="text-slate-400">OpenAI GPT</span>
                                    <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-medium rounded-full">Configured</span>
                                </div>
                                <div className="flex justify-between items-center p-4 bg-slate-900/30 rounded-lg">
                                    <span className="text-slate-400">Groq API</span>
                                    <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-medium rounded-full">Configured</span>
                                </div>
                                <div className="flex justify-between items-center p-4 bg-slate-900/30 rounded-lg">
                                    <span className="text-slate-400">Google Gemini</span>
                                    <span className="px-3 py-1 bg-amber-500/10 text-amber-400 text-xs font-medium rounded-full">Not Set</span>
                                </div>
                                <div className="flex justify-between items-center p-4 bg-slate-900/30 rounded-lg">
                                    <span className="text-slate-400">WhatsApp API</span>
                                    <span className="px-3 py-1 bg-amber-500/10 text-amber-400 text-xs font-medium rounded-full">Not Set</span>
                                </div>
                            </div>
                        </div>

                        {/* Recent Activity */}
                        <div className="lg:col-span-2 bg-slate-800/50 backdrop-blur-sm p-6 rounded-xl border border-slate-700/50">
                            <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                                <Activity size={20} className="text-purple-400" />
                                Recent System Activity
                            </h3>
                            <div className="space-y-3">
                                {[
                                    { action: 'New user registered', user: 'vikram@autoparts.com', time: '2 min ago', type: 'user' },
                                    { action: 'Invoice processed', user: 'rahul@techstart.in', time: '5 min ago', type: 'invoice' },
                                    { action: 'API rate limit warning', user: 'System', time: '12 min ago', type: 'warning' },
                                    { action: 'Database backup completed', user: 'System', time: '1 hour ago', type: 'system' },
                                    { action: 'Subsidy alert sent', user: 'priya@freshfoods.com', time: '2 hours ago', type: 'notification' },
                                ].map((activity, index) => (
                                    <div key={index} className="flex items-center justify-between p-3 bg-slate-900/30 rounded-lg">
                                        <div className="flex items-center gap-3">
                                            <div className={`w-2 h-2 rounded-full ${
                                                activity.type === 'warning' ? 'bg-amber-400' :
                                                activity.type === 'system' ? 'bg-blue-400' :
                                                'bg-emerald-400'
                                            }`} />
                                            <div>
                                                <p className="text-white text-sm">{activity.action}</p>
                                                <p className="text-slate-500 text-xs">{activity.user}</p>
                                            </div>
                                        </div>
                                        <span className="text-slate-500 text-xs">{activity.time}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'settings' && (
                    <div className="bg-slate-800/50 backdrop-blur-sm p-6 rounded-xl border border-slate-700/50">
                        <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                            <Settings size={20} className="text-slate-400" />
                            System Settings
                        </h3>
                        <p className="text-slate-400">Settings panel coming soon...</p>
                    </div>
                )}

                {activeTab === 'analytics' && (
                    <div className="bg-slate-800/50 backdrop-blur-sm p-6 rounded-xl border border-slate-700/50">
                        <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                            <TrendingUp size={20} className="text-emerald-400" />
                            Advanced Analytics
                        </h3>
                        <p className="text-slate-400">Detailed analytics coming soon...</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default SuperAdminDashboard;
