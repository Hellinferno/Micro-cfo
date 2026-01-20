import React, { useState, useEffect } from 'react';
import { api } from '../../services/api'; // Assuming you have an api service wrapper

const AdminDashboard = () => {
    const [stats, setStats] = useState(null);
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);

    // Fetch data on mount
    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            // Parallel fetch for speed
            const [statsRes, usersRes] = await Promise.all([
                api.get('/api/v1/admin/overview'),
                api.get('/api/v1/admin/users')
            ]);
            setStats(statsRes.data);
            setUsers(usersRes.data);
        } catch (error) {
            console.error("Admin Access Denied", error);
        } finally {
            setLoading(false);
        }
    };

    const toggleUserStatus = async (userId) => {
        try {
            await api.patch(`/api/v1/admin/users/${userId}/toggle-status`);
            fetchData(); // Refresh list
        } catch (error) {
            alert("Failed to update user status");
        }
    };

    if (loading) return <div className="p-8">Loading Admin Panel...</div>;

    return (
        <div className="p-6 bg-gray-50 min-h-screen">
            <h1 className="text-3xl font-bold text-gray-900 mb-8">🛡️ Super Admin Dashboard</h1>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <StatCard title="Total Users" value={stats?.total_users} color="bg-blue-500" />
                <StatCard title="Active (24h)" value={stats?.active_users_24h} color="bg-green-500" />
                <StatCard title="Invoices Processed" value={stats?.total_invoices_processed} color="bg-purple-500" />
                <StatCard title="System Health" value={stats?.system_health} color="bg-gray-800" />
            </div>

            {/* User Management Table */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200">
                    <h2 className="text-xl font-semibold text-gray-800">User Management</h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User / Company</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Sector</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Invoices</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {users.map((user) => (
                                <tr key={user.id}>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-medium text-gray-900">{user.full_name || 'N/A'}</div>
                                        <div className="text-sm text-gray-500">{user.email}</div>
                                        <div className="text-xs text-gray-400">{user.company_name}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {user.business_sector || '-'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {user.invoice_count}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                            {user.is_active ? 'Active' : 'Banned'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                        <button
                                            onClick={() => toggleUserStatus(user.id)}
                                            className={`${user.is_active ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'}`}
                                        >
                                            {user.is_active ? 'Deactivate' : 'Activate'}
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

const StatCard = ({ title, value, color }) => (
    <div className={`${color} rounded-lg p-5 text-white shadow-lg`}>
        <div className="text-sm opacity-80 uppercase font-semibold">{title}</div>
        <div className="text-3xl font-bold mt-1">{value}</div>
    </div>
);

export default AdminDashboard;
