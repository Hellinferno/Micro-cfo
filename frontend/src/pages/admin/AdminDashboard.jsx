import React, { useState, useEffect } from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    AreaChart, Area
} from 'recharts';
import {
    Users, FileText, CheckCircle, AlertTriangle, Download, Filter,
    Search, MoreHorizontal, ArrowUpRight, ArrowDownRight, RefreshCw
} from 'lucide-react';
import api from '../../services/api';

const AdminDashboard = () => {
    const [stats, setStats] = useState(null);
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedUsers, setSelectedUsers] = useState([]);
    const [filterStatus, setFilterStatus] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');

    // Mock Chart Data (replace with API data later)
    const chartData = [
        { name: 'Jan', invoices: 65, amount: 24000 },
        { name: 'Feb', invoices: 59, amount: 18000 },
        { name: 'Mar', invoices: 80, amount: 45000 },
        { name: 'Apr', invoices: 81, amount: 32000 },
        { name: 'May', invoices: 96, amount: 56000 },
        { name: 'Jun', invoices: 120, amount: 75000 },
    ];

    // Fetch data on mount
    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            // Parallel fetch for speed using admin API
            const [statsRes, usersRes] = await Promise.all([
                api.admin.getOverview(),
                api.admin.getUsers()
            ]);
            setStats(statsRes);
            setUsers(usersRes);
        } catch (error) {
            console.error("Admin Access Denied", error);
            // Fallback mock data if API fails (for demo)
            setStats({
                total_users: 124,
                active_users_24h: 18,
                total_invoices_processed: 892,
                system_health: '98%'
            });
            setUsers([
                { id: 1, full_name: 'Rahul Sharma', email: 'rahul@techstart.in', company_name: 'TechStart', business_sector: 'IT Services', invoice_count: 45, is_active: true },
                { id: 2, full_name: 'Priya Patel', email: 'priya@freshfoods.com', company_name: 'Fresh Foods', business_sector: 'Retail', invoice_count: 12, is_active: true },
                { id: 3, full_name: 'Amit Kumar', email: 'amit@logistics.co', company_name: 'Fast Logistics', business_sector: 'Transport', invoice_count: 78, is_active: false },
                { id: 4, full_name: 'Sneha Gupta', email: 'sneha@creative.io', company_name: 'Creative Studio', business_sector: 'Design', invoice_count: 23, is_active: true },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const toggleUserStatus = async (userId) => {
        try {
            const { apiFetch } = await import('../../services/api');
            await apiFetch(`/api/v1/admin/users/${userId}/toggle-status`, { method: 'PATCH' });
            fetchData();
        } catch (error) {
            alert("Failed to update user status");
        }
    };

    const toggleSelectAll = () => {
        if (selectedUsers.length === filteredUsers.length) {
            setSelectedUsers([]);
        } else {
            setSelectedUsers(filteredUsers.map(u => u.id));
        }
    };

    const toggleSelectUser = (id) => {
        if (selectedUsers.includes(id)) {
            setSelectedUsers(selectedUsers.filter(uId => uId !== id));
        } else {
            setSelectedUsers([...selectedUsers, id]);
        }
    };

    const filteredUsers = users.filter(user => {
        const matchesStatus = filterStatus === 'all' ||
            (filterStatus === 'active' ? user.is_active : !user.is_active);
        const matchesSearch = user.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            user.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            user.email.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesStatus && matchesSearch;
    });

    if (loading && !stats) return (
        <div className="flex items-center justify-center min-h-screen bg-slate-50">
            <div className="animate-pulse text-primary font-semibold">Loading Dashboard...</div>
        </div>
    );

    return (
        <div className="p-6 bg-slate-50 min-h-screen font-sans">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                        🛡️ Admin Command Center
                    </h1>
                    <p className="text-slate-500 text-sm mt-1">Overview of system performance and user activity</p>
                </div>
                <div className="mt-4 md:mt-0 flex gap-3">
                    <button onClick={fetchData} className="p-2 text-slate-500 hover:text-primary hover:bg-white rounded-lg border border-transparent hover:border-slate-200 transition-all">
                        <RefreshCw size={20} />
                    </button>
                    <button className="flex items-center gap-2 bg-corporate text-white px-4 py-2 rounded-lg hover:bg-slate-700 transition-colors shadow-lg shadow-slate-900/10">
                        <Download size={18} />
                        Export Report
                    </button>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <StatCard
                    icon={Users}
                    title="Total Users"
                    value={stats?.total_users}
                    trend="+12%"
                    trendUp={true}
                    color="text-blue-600"
                    bg="bg-blue-50"
                />
                <StatCard
                    icon={CheckCircle}
                    title="Active (24h)"
                    value={stats?.active_users_24h}
                    trend="-5%"
                    trendUp={false}
                    color="text-emerald-600"
                    bg="bg-emerald-50"
                />
                <StatCard
                    icon={FileText}
                    title="Invoices Processed"
                    value={stats?.total_invoices_processed}
                    trend="+28%"
                    trendUp={true}
                    color="text-purple-600"
                    bg="bg-purple-50"
                />
                <StatCard
                    icon={AlertTriangle}
                    title="System Health"
                    value={stats?.system_health}
                    subValue="All Systems Operational"
                    color="text-amber-600"
                    bg="bg-amber-50"
                />
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                <div className="lg:col-span-2 bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="font-semibold text-slate-800">Transaction Volume</h3>
                        <select className="text-sm border-none bg-slate-50 rounded-md p-1 focus:ring-0 text-slate-500 cursor-pointer">
                            <option>Last 6 Months</option>
                            <option>Last Year</option>
                        </select>
                    </div>
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={chartData}>
                                <defs>
                                    <linearGradient id="colorAmount" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#10B981" stopOpacity={0.1} />
                                        <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12 }} />
                                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12 }} />
                                <Tooltip
                                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="amount"
                                    stroke="#10B981"
                                    strokeWidth={3}
                                    fillOpacity={1}
                                    fill="url(#colorAmount)"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                    <h3 className="font-semibold text-slate-800 mb-6">User Growth</h3>
                    {/* Placeholder for simple line chart or list */}
                    <div className="space-y-4">
                        {[1, 2, 3].map((_, i) => (
                            <div key={i} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                                <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-xs font-bold text-slate-600">
                                        JD
                                    </div>
                                    <div>
                                        <div className="text-sm font-medium">New User Signup</div>
                                        <div className="text-xs text-slate-400">2 mins ago</div>
                                    </div>
                                </div>
                                <span className="text-xs font-medium text-emerald-600">+Free Plan</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Filtering & Actions Bar */}
            <div className="flex flex-col md:flex-row gap-4 justify-between items-center mb-4">
                <div className="flex gap-2 w-full md:w-auto">
                    <div className="relative flex-1 md:w-64">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
                        <input
                            type="text"
                            placeholder="Search users..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
                        />
                    </div>
                    <div className="relative">
                        <select
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value)}
                            className="appearance-none pl-9 pr-8 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-primary outline-none cursor-pointer"
                        >
                            <option value="all">All Status</option>
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                        </select>
                        <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
                    </div>
                </div>

                {selectedUsers.length > 0 && (
                    <div className="flex items-center gap-3 bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-sm animate-fade-in">
                        <span className="text-sm font-medium text-slate-700">{selectedUsers.length} selected</span>
                        <div className="h-4 w-px bg-slate-200"></div>
                        <button className="text-xs font-medium text-red-600 hover:text-red-700">Deactivate</button>
                        <button className="text-xs font-medium text-emerald-600 hover:text-emerald-700">Approve</button>
                    </div>
                )}
            </div>

            {/* User Management Table */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-slate-100">
                        <thead className="bg-slate-50/50">
                            <tr>
                                <th className="px-6 py-4 text-left">
                                    <input
                                        type="checkbox"
                                        checked={selectedUsers.length === filteredUsers.length && filteredUsers.length > 0}
                                        onChange={toggleSelectAll}
                                        className="rounded border-slate-300 text-primary focus:ring-primary"
                                    />
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">User / Company</th>
                                <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Sector</th>
                                <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Processed</th>
                                <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-right text-xs font-bold text-slate-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-slate-50">
                            {filteredUsers.map((user) => (
                                <tr key={user.id} className={`hover:bg-slate-50/50 transition-colors ${selectedUsers.includes(user.id) ? 'bg-primary/5' : ''}`}>
                                    <td className="px-6 py-4">
                                        <input
                                            type="checkbox"
                                            checked={selectedUsers.includes(user.id)}
                                            onChange={() => toggleSelectUser(user.id)}
                                            className="rounded border-slate-300 text-primary focus:ring-primary"
                                        />
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center">
                                            <div className="h-8 w-8 rounded-full bg-slate-100 flex items-center justify-center text-xs font-bold text-slate-500 mr-3">
                                                {user.full_name?.charAt(0) || 'U'}
                                            </div>
                                            <div>
                                                <div className="text-sm font-semibold text-slate-900">{user.full_name || 'N/A'}</div>
                                                <div className="text-xs text-slate-500">{user.email}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className="px-2 py-1 text-xs font-medium bg-slate-100 text-slate-600 rounded-md">
                                            {user.business_sector || 'General'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600 font-mono">
                                        {user.invoice_count}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 py-1 text-xs leading-5 font-semibold rounded-full ${user.is_active
                                            ? 'bg-emerald-100 text-emerald-700 border border-emerald-200'
                                            : 'bg-red-100 text-red-700 border border-red-200'
                                            }`}>
                                            {user.is_active ? 'Active' : 'Banned'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <button className="text-slate-400 hover:text-slate-600 p-1">
                                            <MoreHorizontal size={18} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

const StatCard = ({ icon: Icon, title, value, subValue, trend, trendUp, color, bg }) => (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex items-start justify-between">
        <div>
            <p className="text-sm font-medium text-slate-500 mb-1">{title}</p>
            <h3 className="text-2xl font-bold text-slate-800">{value}</h3>
            {subValue && <p className="text-xs text-slate-400 mt-1">{subValue}</p>}
            {trend && (
                <div className={`flex items-center mt-2 text-xs font-medium ${trendUp ? 'text-emerald-600' : 'text-red-600'}`}>
                    {trendUp ? <ArrowUpRight size={14} className="mr-1" /> : <ArrowDownRight size={14} className="mr-1" />}
                    {trend} vs last month
                </div>
            )}
        </div>
        <div className={`p-3 rounded-lg ${bg} ${color}`}>
            <Icon size={20} />
        </div>
    </div>
);

export default AdminDashboard;
