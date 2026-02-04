import React, { useState } from 'react';
import { 
    Eye, 
    Scale, 
    Search, 
    Mail, 
    Upload, 
    Camera, 
    FileCheck, 
    TrendingUp,
    AlertTriangle,
    CheckCircle,
    Clock,
    ArrowUpRight,
    ArrowDownRight,
    Bell,
    Calendar,
    ChevronRight
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Progress } from '../components/ui';
import { HealthScoreGauge, CashFlowChart } from '../components/charts';

const Dashboard = () => {
    const [healthScore] = useState(72);

    // Mock data for AI agents
    const agents = [
        {
            name: 'Visual Auditor',
            icon: Eye,
            color: 'bg-blue-500',
            status: 'Active',
            metric: '12 documents processed today',
            lastActivity: '2 minutes ago',
        },
        {
            name: 'Legal Sentinel',
            icon: Scale,
            color: 'bg-purple-500',
            status: 'Active',
            metric: '3 alerts this week',
            lastActivity: '1 hour ago',
        },
        {
            name: 'Subsidy Hunter',
            icon: Search,
            color: 'bg-emerald-500',
            status: 'Active',
            metric: '5 opportunities found',
            lastActivity: '30 minutes ago',
        },
        {
            name: 'Negotiator',
            icon: Mail,
            color: 'bg-orange-500',
            status: 'Active',
            metric: '8 emails sent this month',
            lastActivity: '4 hours ago',
        },
    ];

    // Mock data for alerts
    const alerts = [
        {
            id: 1,
            title: 'GST Filing Due',
            description: 'GSTR-3B due in 5 days',
            priority: 'critical',
            time: '2 hours ago',
        },
        {
            id: 2,
            title: 'New Subsidy Match',
            description: 'PMEGP scheme - 95% match score',
            priority: 'info',
            time: '4 hours ago',
        },
        {
            id: 3,
            title: 'Invoice Anomaly Detected',
            description: 'Unusual amount in invoice #INV-2024-089',
            priority: 'warning',
            time: '6 hours ago',
        },
        {
            id: 4,
            title: 'Payment Received',
            description: '₹45,000 from ABC Corp',
            priority: 'success',
            time: '1 day ago',
        },
    ];

    // Mock data for cash flow
    const cashFlowData = [
        { date: 'Jan', inflow: 120000, outflow: 80000 },
        { date: 'Feb', inflow: 150000, outflow: 95000 },
        { date: 'Mar', inflow: 180000, outflow: 110000 },
        { date: 'Apr', inflow: 140000, outflow: 120000 },
        { date: 'May', inflow: 200000, outflow: 130000 },
        { date: 'Jun', inflow: 170000, outflow: 100000 },
    ];

    // Health score breakdown
    const healthBreakdown = [
        { label: 'Compliance', value: 85, color: 'bg-emerald-500' },
        { label: 'Cash Flow', value: 65, color: 'bg-amber-500' },
        { label: 'Subsidies', value: 70, color: 'bg-blue-500' },
    ];

    const getPriorityColor = (priority) => {
        switch (priority) {
            case 'critical': return 'danger';
            case 'warning': return 'warning';
            case 'success': return 'success';
            default: return 'info';
        }
    };

    const getPriorityIcon = (priority) => {
        switch (priority) {
            case 'critical': return <AlertTriangle className="w-4 h-4 text-red-500" />;
            case 'warning': return <Clock className="w-4 h-4 text-amber-500" />;
            case 'success': return <CheckCircle className="w-4 h-4 text-emerald-500" />;
            default: return <Bell className="w-4 h-4 text-blue-500" />;
        }
    };

    return (
        <div className="p-4 lg:p-8 space-y-6 bg-slate-50 min-h-screen">
            {/* Page Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 className="text-2xl lg:text-3xl font-bold text-slate-800">Dashboard</h1>
                    <p className="text-slate-500 mt-1">Welcome back! Here's your financial health overview.</p>
                </div>
                <div className="flex gap-3">
                    <Button variant="outline" icon={Calendar}>
                        This Month
                    </Button>
                    <Button icon={Bell}>
                        3 New Alerts
                    </Button>
                </div>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <button className="flex flex-col items-center justify-center p-4 bg-white rounded-xl border border-slate-200 hover:border-primary hover:shadow-md transition-all group">
                    <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mb-3 group-hover:bg-primary group-hover:text-white transition-all">
                        <Upload className="w-6 h-6 text-primary group-hover:text-white" />
                    </div>
                    <span className="text-sm font-medium text-slate-700">Upload Invoice</span>
                </button>
                <button className="flex flex-col items-center justify-center p-4 bg-white rounded-xl border border-slate-200 hover:border-primary hover:shadow-md transition-all group">
                    <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-3 group-hover:bg-blue-500 transition-all">
                        <Camera className="w-6 h-6 text-blue-500 group-hover:text-white" />
                    </div>
                    <span className="text-sm font-medium text-slate-700">Scan Document</span>
                </button>
                <button className="flex flex-col items-center justify-center p-4 bg-white rounded-xl border border-slate-200 hover:border-primary hover:shadow-md transition-all group">
                    <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mb-3 group-hover:bg-purple-500 transition-all">
                        <Search className="w-6 h-6 text-purple-500 group-hover:text-white" />
                    </div>
                    <span className="text-sm font-medium text-slate-700">Check Eligibility</span>
                </button>
                <button className="flex flex-col items-center justify-center p-4 bg-white rounded-xl border border-slate-200 hover:border-primary hover:shadow-md transition-all group">
                    <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center mb-3 group-hover:bg-emerald-500 transition-all">
                        <FileCheck className="w-6 h-6 text-emerald-500 group-hover:text-white" />
                    </div>
                    <span className="text-sm font-medium text-slate-700">Compliance Report</span>
                </button>
            </div>

            {/* Main Grid */}
            <div className="grid lg:grid-cols-3 gap-6">
                {/* Financial Health Score */}
                <Card className="lg:row-span-2">
                    <CardHeader>
                        <CardTitle>Financial Health Score</CardTitle>
                    </CardHeader>
                    <CardContent className="flex flex-col items-center">
                        <HealthScoreGauge score={healthScore} size={200} />
                        
                        <div className="w-full mt-6 space-y-4">
                            {healthBreakdown.map((item, index) => (
                                <div key={index}>
                                    <div className="flex justify-between text-sm mb-1">
                                        <span className="text-slate-600">{item.label}</span>
                                        <span className="font-medium text-slate-800">{item.value}%</span>
                                    </div>
                                    <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                                        <div 
                                            className={`h-full rounded-full ${item.color} transition-all duration-500`}
                                            style={{ width: `${item.value}%` }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="w-full mt-6 p-4 bg-emerald-50 rounded-xl border border-emerald-100">
                            <div className="flex items-center gap-2 text-emerald-700">
                                <TrendingUp className="w-5 h-5" />
                                <span className="font-medium">+5% improvement</span>
                            </div>
                            <p className="text-sm text-emerald-600 mt-1">compared to last month</p>
                        </div>
                    </CardContent>
                </Card>

                {/* AI Agent Activity */}
                <Card className="lg:col-span-2">
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle>AI Agent Activity</CardTitle>
                        <Button variant="ghost" size="sm">
                            View All
                            <ChevronRight className="w-4 h-4 ml-1" />
                        </Button>
                    </CardHeader>
                    <CardContent>
                        <div className="grid sm:grid-cols-2 gap-4">
                            {agents.map((agent, index) => (
                                <div 
                                    key={index} 
                                    className="p-4 bg-slate-50 rounded-xl border border-slate-100 hover:border-slate-200 transition-all"
                                >
                                    <div className="flex items-start gap-3">
                                        <div className={`w-10 h-10 ${agent.color} rounded-lg flex items-center justify-center flex-shrink-0`}>
                                            <agent.icon className="w-5 h-5 text-white" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2">
                                                <h4 className="font-medium text-slate-800 truncate">{agent.name}</h4>
                                                <Badge variant="success" size="sm" dot>{agent.status}</Badge>
                                            </div>
                                            <p className="text-sm text-slate-600 mt-1">{agent.metric}</p>
                                            <p className="text-xs text-slate-400 mt-2">{agent.lastActivity}</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* Real-Time Alerts */}
                <Card className="lg:col-span-2">
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle>Recent Alerts</CardTitle>
                        <Badge variant="danger">3 New</Badge>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {alerts.map((alert) => (
                                <div 
                                    key={alert.id}
                                    className="flex items-start gap-3 p-3 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer group"
                                >
                                    <div className="mt-0.5">
                                        {getPriorityIcon(alert.priority)}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2">
                                            <h4 className="font-medium text-slate-800 truncate">{alert.title}</h4>
                                            <Badge variant={getPriorityColor(alert.priority)} size="sm">
                                                {alert.priority}
                                            </Badge>
                                        </div>
                                        <p className="text-sm text-slate-500 mt-0.5">{alert.description}</p>
                                    </div>
                                    <span className="text-xs text-slate-400 flex-shrink-0">{alert.time}</span>
                                    <ChevronRight className="w-4 h-4 text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity" />
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Cash Flow Projection */}
            <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                        <CardTitle>Cash Flow Projection</CardTitle>
                        <p className="text-sm text-slate-500 mt-1">30/60/90 day forecast</p>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-emerald-500" />
                            <span className="text-sm text-slate-600">Inflow</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-red-500" />
                            <span className="text-sm text-slate-600">Outflow</span>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <CashFlowChart data={cashFlowData} />
                    
                    {/* Summary Stats */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-100">
                        <div className="text-center">
                            <p className="text-sm text-slate-500">Net Cash Flow</p>
                            <p className="text-xl font-bold text-emerald-600 mt-1">+₹1,70,000</p>
                        </div>
                        <div className="text-center">
                            <p className="text-sm text-slate-500">Pending Receivables</p>
                            <p className="text-xl font-bold text-slate-800 mt-1">₹2,45,000</p>
                        </div>
                        <div className="text-center">
                            <p className="text-sm text-slate-500">Pending Payables</p>
                            <p className="text-xl font-bold text-slate-800 mt-1">₹1,20,000</p>
                        </div>
                        <div className="text-center">
                            <p className="text-sm text-slate-500">Cash Runway</p>
                            <p className="text-xl font-bold text-blue-600 mt-1">45 Days</p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Bottom Stats */}
            <div className="grid md:grid-cols-3 gap-6">
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Penalties Avoided</p>
                                <p className="text-2xl font-bold text-emerald-600 mt-1">₹45,000</p>
                            </div>
                            <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center">
                                <ArrowDownRight className="w-6 h-6 text-emerald-600" />
                            </div>
                        </div>
                        <p className="text-xs text-slate-400 mt-4">3 penalties avoided this quarter</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Subsidies Claimed</p>
                                <p className="text-2xl font-bold text-blue-600 mt-1">₹2,50,000</p>
                            </div>
                            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                                <ArrowUpRight className="w-6 h-6 text-blue-600" />
                            </div>
                        </div>
                        <p className="text-xs text-slate-400 mt-4">2 schemes approved this year</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Documents Processed</p>
                                <p className="text-2xl font-bold text-purple-600 mt-1">156</p>
                            </div>
                            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                                <FileCheck className="w-6 h-6 text-purple-600" />
                            </div>
                        </div>
                        <p className="text-xs text-slate-400 mt-4">98% accuracy rate</p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default Dashboard;
