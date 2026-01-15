import React from 'react';
import { Search, Filter, Download, Eye } from 'lucide-react';

const History = () => {
    const invoices = [
        { id: 'INV-001', date: '2024-01-24', vendor: 'ABC Machinery Pvt Ltd', amount: '₹5,90,000', status: 'Audit Passed', badgeColor: 'bg-emerald-100 text-emerald-700' },
        { id: 'INV-002', date: '2024-01-20', vendor: 'Tech Solutions Inc', amount: '₹25,000', status: 'Pending', badgeColor: 'bg-amber-100 text-amber-700' },
        { id: 'INV-003', date: '2024-01-15', vendor: 'Office Supplies Co', amount: '₹12,400', status: 'Audit Passed', badgeColor: 'bg-emerald-100 text-emerald-700' },
        { id: 'INV-004', date: '2024-01-10', vendor: 'Raw Materials Ltd', amount: '₹1,20,000', status: 'Rejected', badgeColor: 'bg-red-100 text-red-700' },
    ];

    return (
        <div className="p-6 lg:p-10 space-y-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800">Invoice History</h1>
                    <p className="text-slate-500 text-sm">Track all your uploaded bills and their audit status.</p>
                </div>
                <div className="flex space-x-2">
                    <button className="flex items-center space-x-2 px-4 py-2 bg-white border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 text-sm font-medium">
                        <Filter size={16} />
                        <span>Filter</span>
                    </button>
                    <button className="flex items-center space-x-2 px-4 py-2 bg-white border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 text-sm font-medium">
                        <Download size={16} />
                        <span>Export</span>
                    </button>
                </div>
            </div>

            {/* Search Bar */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
                <input
                    type="text"
                    placeholder="Search invoices by vendor, ID or amount..."
                    className="w-full pl-10 pr-4 py-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all shadow-sm"
                />
            </div>

            {/* Table */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-slate-50 border-b border-slate-200">
                                <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Invoice ID</th>
                                <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Date</th>
                                <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Vendor</th>
                                <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Amount</th>
                                <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                                <th className="p-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {invoices.map((inv) => (
                                <tr key={inv.id} className="hover:bg-slate-50 transition-colors">
                                    <td className="p-4 font-medium text-slate-700">{inv.id}</td>
                                    <td className="p-4 text-slate-500">{inv.date}</td>
                                    <td className="p-4 text-slate-800 font-medium">{inv.vendor}</td>
                                    <td className="p-4 text-slate-600 font-mono">{inv.amount}</td>
                                    <td className="p-4">
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${inv.badgeColor}`}>
                                            {inv.status}
                                        </span>
                                    </td>
                                    <td className="p-4 text-slate-400 hover:text-primary cursor-pointer">
                                        <Eye size={18} />
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

export default History;
