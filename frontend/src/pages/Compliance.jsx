import React, { useState } from 'react';
import { 
    Calendar, 
    AlertTriangle, 
    CheckCircle, 
    Clock, 
    FileText,
    ExternalLink,
    Filter,
    ChevronRight,
    AlertCircle,
    Shield,
    Scale,
    TrendingUp,
    Bell
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Progress } from '../components/ui';
import { CompliancePieChart } from '../components/charts';

const Compliance = () => {
    const [selectedMonth, setSelectedMonth] = useState('January 2024');
    const [filterType, setFilterType] = useState('all');

    // Calendar data
    const calendarDays = Array.from({ length: 31 }, (_, i) => {
        const day = i + 1;
        const deadlines = {
            5: { type: 'gst', title: 'GSTR-1 Due', priority: 'warning' },
            11: { type: 'gst', title: 'GSTR-3B Due', priority: 'critical' },
            15: { type: 'tds', title: 'TDS Payment', priority: 'warning' },
            20: { type: 'gst', title: 'GSTR-3B Filing', priority: 'critical' },
            25: { type: 'labour', title: 'PF Filing', priority: 'info' },
        };
        return { day, deadline: deadlines[day] };
    });

    // Compliance checklist
    const checklist = [
        { id: 1, title: 'GSTR-1 (December)', status: 'filed', dueDate: '2024-01-11' },
        { id: 2, title: 'GSTR-3B (December)', status: 'filed', dueDate: '2024-01-20' },
        { id: 3, title: 'TDS Return Q3', status: 'pending', dueDate: '2024-01-31' },
        { id: 4, title: 'Annual ROC Filing', status: 'pending', dueDate: '2024-02-28' },
        { id: 5, title: 'PF Monthly Return', status: 'overdue', dueDate: '2024-01-15' },
        { id: 6, title: 'Professional Tax', status: 'filed', dueDate: '2024-01-10' },
    ];

    // Regulatory updates from Legal Sentinel
    const regulatoryUpdates = [
        {
            id: 1,
            title: 'New GST E-Invoice Limit from April 2024',
            summary: 'E-invoicing mandatory for businesses with turnover > ₹5 Cr. Implement before March 31st.',
            impactLevel: 'high',
            actionRequired: true,
            source: 'GST Council Notification',
            date: '2024-01-15',
        },
        {
            id: 2,
            title: 'MCA Annual Return Filing Deadline Extended',
            summary: 'Form AOC-4 and MGT-7 deadline extended to February 28, 2024.',
            impactLevel: 'medium',
            actionRequired: false,
            source: 'MCA Circular',
            date: '2024-01-12',
        },
        {
            id: 3,
            title: 'EPFO Wage Ceiling Increase',
            summary: 'PF wage ceiling increased to ₹21,000. Review payroll calculations.',
            impactLevel: 'high',
            actionRequired: true,
            source: 'EPFO Notification',
            date: '2024-01-10',
        },
        {
            id: 4,
            title: 'New Labour Code Implementation Update',
            summary: 'Four labour codes expected to be implemented from April 1, 2024.',
            impactLevel: 'high',
            actionRequired: true,
            source: 'Ministry of Labour',
            date: '2024-01-08',
        },
    ];

    // Penalty risk data
    const penaltyRisks = [
        { category: 'GST', risk: 'low', potentialPenalty: 5000, reason: 'Late filing penalty waived' },
        { category: 'TDS', risk: 'medium', potentialPenalty: 25000, reason: 'Return pending for Q3' },
        { category: 'MCA', risk: 'low', potentialPenalty: 0, reason: 'All filings up to date' },
        { category: 'Labour Laws', risk: 'high', potentialPenalty: 15000, reason: 'PF return overdue' },
    ];

    // Pie chart data
    const complianceData = [
        { name: 'Compliant', value: 8 },
        { name: 'Pending', value: 3 },
        { name: 'Overdue', value: 1 },
    ];

    const getStatusIcon = (status) => {
        switch (status) {
            case 'filed': return <CheckCircle className="w-5 h-5 text-emerald-500" />;
            case 'pending': return <Clock className="w-5 h-5 text-amber-500" />;
            case 'overdue': return <AlertTriangle className="w-5 h-5 text-red-500" />;
            default: return null;
        }
    };

    const getStatusBadge = (status) => {
        switch (status) {
            case 'filed': return <Badge variant="success">Filed</Badge>;
            case 'pending': return <Badge variant="warning">Pending</Badge>;
            case 'overdue': return <Badge variant="danger">Overdue</Badge>;
            default: return <Badge>Unknown</Badge>;
        }
    };

    const getImpactBadge = (level) => {
        switch (level) {
            case 'high': return <Badge variant="danger">High Impact</Badge>;
            case 'medium': return <Badge variant="warning">Medium Impact</Badge>;
            case 'low': return <Badge variant="info">Low Impact</Badge>;
            default: return null;
        }
    };

    const getRiskColor = (risk) => {
        switch (risk) {
            case 'high': return 'text-red-600 bg-red-100';
            case 'medium': return 'text-amber-600 bg-amber-100';
            case 'low': return 'text-emerald-600 bg-emerald-100';
            default: return 'text-slate-600 bg-slate-100';
        }
    };

    const totalPenaltyRisk = penaltyRisks.reduce((sum, item) => sum + item.potentialPenalty, 0);

    return (
        <div className="p-4 lg:p-8 space-y-6 bg-slate-50 min-h-screen">
            {/* Page Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 className="text-2xl lg:text-3xl font-bold text-slate-800">Compliance Dashboard</h1>
                    <p className="text-slate-500 mt-1">Monitor regulatory health and upcoming deadlines</p>
                </div>
                <div className="flex gap-3">
                    <Button variant="outline" icon={Filter}>
                        Filter
                    </Button>
                    <Button icon={Bell}>
                        Set Reminders
                    </Button>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                                <CheckCircle className="w-5 h-5 text-emerald-600" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-slate-800">8</p>
                                <p className="text-xs text-slate-500">Filed</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
                                <Clock className="w-5 h-5 text-amber-600" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-slate-800">3</p>
                                <p className="text-xs text-slate-500">Pending</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                                <AlertTriangle className="w-5 h-5 text-red-600" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-slate-800">1</p>
                                <p className="text-xs text-slate-500">Overdue</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                                <Scale className="w-5 h-5 text-blue-600" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-slate-800">85%</p>
                                <p className="text-xs text-slate-500">Score</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div className="grid lg:grid-cols-3 gap-6">
                {/* Compliance Calendar */}
                <Card className="lg:col-span-2">
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle className="flex items-center gap-2">
                            <Calendar className="w-5 h-5" />
                            Compliance Calendar
                        </CardTitle>
                        <select 
                            value={selectedMonth}
                            onChange={(e) => setSelectedMonth(e.target.value)}
                            className="text-sm border border-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary/50"
                        >
                            <option>January 2024</option>
                            <option>February 2024</option>
                            <option>March 2024</option>
                        </select>
                    </CardHeader>
                    <CardContent>
                        {/* Filter Pills */}
                        <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
                            {['all', 'gst', 'tds', 'mca', 'labour'].map((type) => (
                                <button
                                    key={type}
                                    onClick={() => setFilterType(type)}
                                    className={`px-3 py-1 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
                                        filterType === type
                                            ? 'bg-primary text-white'
                                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                                    }`}
                                >
                                    {type.toUpperCase()}
                                </button>
                            ))}
                        </div>

                        {/* Calendar Grid */}
                        <div className="grid grid-cols-7 gap-1">
                            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
                                <div key={day} className="p-2 text-center text-xs font-medium text-slate-500">
                                    {day}
                                </div>
                            ))}
                            {/* Empty cells for alignment (January 2024 starts on Monday) */}
                            <div className="p-2" />
                            {calendarDays.map(({ day, deadline }) => (
                                <div
                                    key={day}
                                    className={`p-2 text-center rounded-lg relative ${
                                        deadline 
                                            ? deadline.priority === 'critical' 
                                                ? 'bg-red-100 text-red-800'
                                                : deadline.priority === 'warning'
                                                ? 'bg-amber-100 text-amber-800'
                                                : 'bg-blue-100 text-blue-800'
                                            : 'hover:bg-slate-100'
                                    }`}
                                    title={deadline?.title}
                                >
                                    <span className="text-sm">{day}</span>
                                    {deadline && (
                                        <div className="absolute bottom-1 left-1/2 transform -translate-x-1/2">
                                            <div className={`w-1.5 h-1.5 rounded-full ${
                                                deadline.priority === 'critical' ? 'bg-red-500' :
                                                deadline.priority === 'warning' ? 'bg-amber-500' : 'bg-blue-500'
                                            }`} />
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>

                        {/* Legend */}
                        <div className="flex gap-4 mt-4 pt-4 border-t border-slate-100">
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-red-500" />
                                <span className="text-xs text-slate-600">Critical</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-amber-500" />
                                <span className="text-xs text-slate-600">Warning</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-blue-500" />
                                <span className="text-xs text-slate-600">Info</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Compliance Overview */}
                <Card>
                    <CardHeader>
                        <CardTitle>Compliance Overview</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <CompliancePieChart data={complianceData} />
                        <div className="mt-4 space-y-2">
                            <div className="flex items-center justify-between text-sm">
                                <span className="text-slate-600">Compliance Rate</span>
                                <span className="font-semibold text-slate-800">85%</span>
                            </div>
                            <Progress value={85} variant="success" />
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div className="grid lg:grid-cols-2 gap-6">
                {/* Document Checklist */}
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle className="flex items-center gap-2">
                            <FileText className="w-5 h-5" />
                            Filing Checklist
                        </CardTitle>
                        <Button variant="ghost" size="sm">View All</Button>
                    </CardHeader>
                    <CardContent className="p-0">
                        <div className="divide-y divide-slate-100">
                            {checklist.map((item) => (
                                <div 
                                    key={item.id}
                                    className="flex items-center gap-4 p-4 hover:bg-slate-50 transition-colors"
                                >
                                    {getStatusIcon(item.status)}
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium text-slate-800 truncate">{item.title}</p>
                                        <p className="text-xs text-slate-500">Due: {item.dueDate}</p>
                                    </div>
                                    {getStatusBadge(item.status)}
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* Penalty Risk Meter */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <AlertCircle className="w-5 h-5" />
                            Penalty Risk Assessment
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-center mb-6">
                            <p className="text-sm text-slate-500">Total Potential Penalty</p>
                            <p className="text-3xl font-bold text-red-600">₹{totalPenaltyRisk.toLocaleString()}</p>
                        </div>

                        <div className="space-y-3">
                            {penaltyRisks.map((item, index) => (
                                <div key={index} className="flex items-center gap-4 p-3 bg-slate-50 rounded-lg">
                                    <div className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor(item.risk)}`}>
                                        {item.risk.toUpperCase()}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium text-slate-800">{item.category}</p>
                                        <p className="text-xs text-slate-500 truncate">{item.reason}</p>
                                    </div>
                                    <p className="font-semibold text-slate-800">
                                        ₹{item.potentialPenalty.toLocaleString()}
                                    </p>
                                </div>
                            ))}
                        </div>

                        <Button className="w-full mt-4" variant="outline">
                            View Recommended Actions
                        </Button>
                    </CardContent>
                </Card>
            </div>

            {/* Regulatory Updates */}
            <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                        <Scale className="w-5 h-5" />
                        Legislative Updates
                        <Badge variant="info">Powered by Legal Sentinel</Badge>
                    </CardTitle>
                    <Button variant="ghost" size="sm">View All</Button>
                </CardHeader>
                <CardContent>
                    <div className="grid md:grid-cols-2 gap-4">
                        {regulatoryUpdates.map((update) => (
                            <div 
                                key={update.id}
                                className="p-4 border border-slate-200 rounded-xl hover:shadow-md transition-all group"
                            >
                                <div className="flex items-start justify-between mb-3">
                                    {getImpactBadge(update.impactLevel)}
                                    {update.actionRequired && (
                                        <Badge variant="warning">Action Required</Badge>
                                    )}
                                </div>
                                <h4 className="font-semibold text-slate-800 mb-2 group-hover:text-primary transition-colors">
                                    {update.title}
                                </h4>
                                <p className="text-sm text-slate-600 mb-3 line-clamp-2">
                                    {update.summary}
                                </p>
                                <div className="flex items-center justify-between">
                                    <div className="text-xs text-slate-400">
                                        <span>{update.source}</span>
                                        <span className="mx-2">•</span>
                                        <span>{update.date}</span>
                                    </div>
                                    <button className="text-primary hover:text-primary-dark text-sm font-medium flex items-center gap-1">
                                        Read More
                                        <ExternalLink className="w-3 h-3" />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};

export default Compliance;
