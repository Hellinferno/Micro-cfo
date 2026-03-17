import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import {
    TrendingUp,
    TrendingDown,
    DollarSign,
    FileText,
    Shield,
    Percent,
    ArrowUpRight,
    ArrowDownRight,
    Bell,
    Search,
    Plus
} from 'lucide-react';
import { Card, CardHeader, CardContent } from './components/ui/Card';
import { Button } from './components/ui/Button';
import { Badge } from './components/ui/Badge';

const Dashboard = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [data, setData] = useState({
        metrics: {
            totalInvoices: 0,
            totalAmount: 0,
            complianceScore: 0,
            subsidiesFound: 0,
            pendingNegotiations: 0,
            monthlyGrowth: 0
        },
        recentInvoices: [],
        complianceAlerts: [],
        subsidyMatches: []
    });

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                setLoading(true);
                // Fetch complete dashboard summary
                const response = await api.get('/api/v1/dashboard/summary');

                if (response.data.success) {
                    setData(response.data.data);
                }
            } catch (err) {
                console.error('Failed to fetch dashboard data:', err);
                setError('Failed to load dashboard data. Please try again.');

                // Use mock data as fallback
                setData({
                    metrics: {
                        totalInvoices: 0,
                        totalAmount: 0,
                        complianceScore: 100,
                        subsidiesFound: 0,
                        pendingNegotiations: 0,
                        monthlyGrowth: 0
                    },
                    recentInvoices: [],
                    complianceAlerts: [{
                        id: 'error_1',
                        type: 'warning',
                        message: 'Unable to load data. Please check your connection.',
                        date: new Date().toISOString().split('T')[0]
                    }],
                    subsidyMatches: []
                });
            } finally {
                setLoading(false);
            }
        };

        fetchDashboardData();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            </div>
        );
    }

    return (
        <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-8">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900">Dashboard</h1>
                    <p className="text-slate-500 mt-1">Welcome back! Here's your financial overview</p>
                </div>
                <div className="flex items-center gap-3">
                    <Button variant="outline" onClick={() => navigate('/scanner')}>
                        <Plus className="w-4 h-4 mr-2" />
                        Upload Invoice
                    </Button>
                    <Button onClick={() => navigate('/chat')}>
                        Ask MicroCFO
                    </Button>
                </div>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <MetricCard
                    title="Total Invoices"
                    value={data.metrics.totalInvoices}
                    change={data.metrics.monthlyGrowth}
                    icon={FileText}
                    color="primary"
                />
                <MetricCard
                    title="Total Amount"
                    value={`₹${(data.metrics.totalAmount / 100000).toFixed(1)}L`}
                    change={15.2}
                    icon={DollarSign}
                    color="success"
                />
                <MetricCard
                    title="Compliance Score"
                    value={`${data.metrics.complianceScore}%`}
                    change={3.2}
                    icon={Shield}
                    color="info"
                />
                <MetricCard
                    title="Subsidies Found"
                    value={data.metrics.subsidiesFound}
                    change={-2.1}
                    icon={Percent}
                    color="warning"
                />
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Recent Invoices */}
                <div className="lg:col-span-2">
                    <Card>
                        <CardHeader>
                            <div className="flex items-center justify-between">
                                <h2 className="text-lg font-semibold text-slate-900">Recent Invoices</h2>
                                <Button variant="outline" size="sm" onClick={() => navigate('/history')}>
                                    View All
                                </Button>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {data.recentInvoices.map((invoice) => (
                                    <InvoiceRow key={invoice.id} invoice={invoice} />
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Compliance Alerts */}
                <div>
                    <Card>
                        <CardHeader>
                            <h2 className="text-lg font-semibold text-slate-900">Compliance Alerts</h2>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {data.complianceAlerts.map((alert) => (
                                <AlertItem key={alert.id} alert={alert} />
                            ))}
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* Subsidy Matches */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-semibold text-slate-900">Recommended Subsidies</h2>
                        <Button variant="outline" size="sm" onClick={() => navigate('/subsidies')}>
                            Explore All
                        </Button>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {data.subsidyMatches.map((subsidy) => (
                            <SubsidyCard key={subsidy.id} subsidy={subsidy} />
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Quick Actions */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <QuickActionCard
                    icon={FileText}
                    title="Scan Invoice"
                    description="Upload and analyze invoices"
                    onClick={() => navigate('/scanner')}
                />
                <QuickActionCard
                    icon={Shield}
                    title="Check Compliance"
                    description="Verify GST & ITC eligibility"
                    onClick={() => navigate('/compliance')}
                />
                <QuickActionCard
                    icon={Percent}
                    title="Find Subsidies"
                    description="Discover government schemes"
                    onClick={() => navigate('/subsidies')}
                />
                <QuickActionCard
                    icon={DollarSign}
                    title="Negotiate"
                    description="Draft vendor communications"
                    onClick={() => navigate('/negotiation')}
                />
            </div>
        </div>
    );
};

// Sub-components

const MetricCard = ({ title, value, change, icon: Icon, color }) => {
    const isPositive = change >= 0;
    const colorClasses = {
        primary: 'bg-primary-50 text-primary-600',
        success: 'bg-green-50 text-green-600',
        info: 'bg-blue-50 text-blue-600',
        warning: 'bg-yellow-50 text-yellow-600'
    };

    return (
        <Card className="card-hover">
            <CardContent className="p-6">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm font-medium text-slate-600">{title}</p>
                        <p className="text-2xl font-bold text-slate-900 mt-2">{value}</p>
                        <div className={`flex items-center mt-2 text-sm ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                            {isPositive ? <ArrowUpRight className="w-4 h-4 mr-1" /> : <ArrowDownRight className="w-4 h-4 mr-1" />}
                            <span className="font-medium">{Math.abs(change)}%</span>
                            <span className="text-slate-500 ml-1">vs last month</span>
                        </div>
                    </div>
                    <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
                        <Icon className="w-6 h-6" />
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};

const InvoiceRow = ({ invoice }) => {
    const statusColors = {
        processed: 'badge-success',
        flagged: 'badge-danger',
        pending: 'badge-warning'
    };

    return (
        <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors">
            <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
                    <FileText className="w-5 h-5 text-primary-600" />
                </div>
                <div>
                    <p className="font-medium text-slate-900">{invoice.vendor}</p>
                    <p className="text-sm text-slate-500">{invoice.category}</p>
                </div>
            </div>
            <div className="text-right">
                <p className="font-semibold text-slate-900">₹{invoice.amount.toLocaleString('en-IN')}</p>
                <p className="text-sm text-slate-500">{invoice.date}</p>
            </div>
            <Badge className={statusColors[invoice.status]}>
                {invoice.status}
            </Badge>
        </div>
    );
};

const AlertItem = ({ alert }) => {
    const typeColors = {
        warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
        info: 'bg-blue-50 border-blue-200 text-blue-800',
        success: 'bg-green-50 border-green-200 text-green-800'
    };

    const typeIcons = {
        warning: '⚠️',
        info: 'ℹ️',
        success: '✅'
    };

    return (
        <div className={`p-3 rounded-lg border ${typeColors[alert.type]}`}>
            <div className="flex items-start gap-2">
                <span className="text-lg">{typeIcons[alert.type]}</span>
                <div className="flex-1">
                    <p className="text-sm font-medium">{alert.message}</p>
                    <p className="text-xs mt-1 opacity-75">{alert.date}</p>
                </div>
            </div>
        </div>
    );
};

const SubsidyCard = ({ subsidy }) => {
    return (
        <div className="p-4 border border-slate-200 rounded-lg hover:border-primary-300 hover:shadow-sm transition-all">
            <div className="flex items-start justify-between mb-2">
                <h3 className="font-semibold text-slate-900">{subsidy.name}</h3>
                <Badge className="badge-success">{subsidy.matchScore}% match</Badge>
            </div>
            <p className="text-sm text-slate-600 mb-3">{subsidy.benefit}</p>
            <div className="flex items-center justify-between">
                <p className="text-xs text-slate-500">Deadline: {subsidy.deadline}</p>
                <Button size="sm" variant="outline">
                    Apply
                </Button>
            </div>
        </div>
    );
};

const QuickActionCard = ({ icon: Icon, title, description, onClick }) => {
    return (
        <button
            onClick={onClick}
            className="p-4 bg-white border border-slate-200 rounded-lg hover:border-primary-300 hover:shadow-md transition-all text-left group"
        >
            <Icon className="w-8 h-8 text-primary-600 mb-3 group-hover:scale-110 transition-transform" />
            <h3 className="font-semibold text-slate-900">{title}</h3>
            <p className="text-sm text-slate-500 mt-1">{description}</p>
        </button>
    );
};

export default Dashboard;
