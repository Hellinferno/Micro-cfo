import React, { useState } from 'react';
import {
    Search,
    Filter,
    ArrowUpRight,
    Clock,
    CheckCircle,
    FileText,
    ChevronRight,
    Star,
    Building2,
    MapPin,
    Banknote,
    TrendingUp,
    Sparkles,
    AlertCircle,
    Download,
    Send
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Progress, Modal } from '../components/ui';
import { SubsidyBarChart } from '../components/charts';

const SubsidyExplorer = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedFilters, setSelectedFilters] = useState({
        sector: 'all',
        size: 'all',
        location: 'all'
    });
    const [selectedSubsidy, setSelectedSubsidy] = useState(null);
    const [showApplicationModal, setShowApplicationModal] = useState(false);

    // Mock subsidy data
    const subsidies = [
        {
            id: 1,
            name: 'CLCSS - Technology Upgradation',
            logo: '🏭',
            benefit: '15% Capital Subsidy',
            maxAmount: 1500000,
            matchScore: 95,
            deadline: '2024-03-31',
            eligibility: [
                'MSMEs in manufacturing sector',
                'Minimum 3 years of operation',
                'Turnover > ₹10 Lakhs',
                'Technology upgradation project'
            ],
            description: 'Credit Linked Capital Subsidy Scheme for technology upgradation of MSMEs.',
            status: 'eligible',
            sector: 'Manufacturing',
            documentsRequired: ['GST Certificate', 'ITR (3 years)', 'Project Report', 'Quotations']
        },
        {
            id: 2,
            name: 'PMEGP Scheme',
            logo: '🚀',
            benefit: 'Up to 35% Subsidy',
            maxAmount: 2500000,
            matchScore: 88,
            deadline: '2024-02-28',
            eligibility: [
                'New micro-enterprises',
                'Manufacturing or service sector',
                'Age above 18 years',
                'VIII pass for projects > ₹10 Lakhs'
            ],
            description: 'Prime Minister Employment Generation Programme for new enterprises.',
            status: 'eligible',
            sector: 'Manufacturing',
            documentsRequired: ['Aadhar Card', 'Bank Statement', 'Project Report', 'EDP Certificate']
        },
        {
            id: 3,
            name: 'CGTMSE',
            logo: '🏦',
            benefit: 'Collateral Free Loans',
            maxAmount: 20000000,
            matchScore: 92,
            deadline: 'Ongoing',
            eligibility: [
                'Micro & Small Enterprises',
                'Manufacturing or service sector',
                'No collateral required',
                'Good credit history'
            ],
            description: 'Credit Guarantee Fund Trust for Micro and Small Enterprises.',
            status: 'eligible',
            sector: 'All Sectors',
            documentsRequired: ['GST Certificate', 'Bank Statement (6 months)', 'ITR', 'Business Plan']
        },
        {
            id: 4,
            name: 'ZED Certification Scheme',
            logo: '⭐',
            benefit: '80% Certification Cost',
            maxAmount: 500000,
            matchScore: 78,
            deadline: '2024-06-30',
            eligibility: [
                'MSMEs registered under Udyam',
                'Commitment to quality improvement',
                'No pending legal cases'
            ],
            description: 'Zero Defect Zero Effect certification for MSMEs.',
            status: 'eligible',
            sector: 'Manufacturing',
            documentsRequired: ['Udyam Registration', 'Quality Documents', 'Environmental Clearance']
        },
        {
            id: 5,
            name: 'Stand-Up India',
            logo: '🌟',
            benefit: 'Loans ₹10L - ₹1Cr',
            maxAmount: 10000000,
            matchScore: 65,
            deadline: 'Ongoing',
            eligibility: [
                'SC/ST/Women entrepreneurs',
                'Greenfield enterprise',
                'Manufacturing or service sector',
                '51% shareholding by SC/ST/Women'
            ],
            description: 'Bank loans for SC/ST and women entrepreneurs.',
            status: 'partial',
            sector: 'All Sectors',
            documentsRequired: ['Caste Certificate/Gender Proof', 'Business Plan', 'Land Documents']
        },
    ];

    // Application tracker data
    const applications = [
        { id: 1, scheme: 'CLCSS', status: 'submitted', date: '2024-01-10', amount: 1200000 },
        { id: 2, scheme: 'PMEGP', status: 'under-review', date: '2023-12-15', amount: 2000000 },
        { id: 3, scheme: 'State Industrial Subsidy', status: 'approved', date: '2023-11-01', amount: 500000 },
        { id: 4, scheme: 'CGTMSE', status: 'draft', date: '2024-01-20', amount: 1500000 },
    ];

    // Timeline data for subsidies received
    const subsidyTimeline = [
        { month: 'Jul', amount: 0 },
        { month: 'Aug', amount: 0 },
        { month: 'Sep', amount: 250000 },
        { month: 'Oct', amount: 0 },
        { month: 'Nov', amount: 500000 },
        { month: 'Dec', amount: 0 },
        { month: 'Jan', amount: 0 },
    ];

    const getStatusBadge = (status) => {
        switch (status) {
            case 'draft': return <Badge variant="default">Draft</Badge>;
            case 'submitted': return <Badge variant="info">Submitted</Badge>;
            case 'under-review': return <Badge variant="warning">Under Review</Badge>;
            case 'approved': return <Badge variant="success">Approved</Badge>;
            case 'rejected': return <Badge variant="danger">Rejected</Badge>;
            default: return <Badge>Unknown</Badge>;
        }
    };

    const getMatchColor = (score) => {
        if (score >= 90) return 'text-emerald-600';
        if (score >= 70) return 'text-amber-600';
        return 'text-slate-600';
    };

    const filteredSubsidies = subsidies.filter(s => {
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            // Search across multiple fields
            const matchesName = s.name.toLowerCase().includes(query);
            const matchesSector = s.sector.toLowerCase().includes(query);
            const matchesDescription = s.description.toLowerCase().includes(query);
            const matchesBenefit = s.benefit.toLowerCase().includes(query);
            const matchesEligibility = s.eligibility.some(e => e.toLowerCase().includes(query));

            if (!matchesName && !matchesSector && !matchesDescription && !matchesBenefit && !matchesEligibility) {
                return false;
            }
        }
        // Apply sector filter
        if (selectedFilters.sector !== 'all') {
            if (!s.sector.toLowerCase().includes(selectedFilters.sector.toLowerCase())) {
                return false;
            }
        }
        return true;
    });

    return (
        <div className="p-4 lg:p-8 space-y-6 bg-slate-50 min-h-screen">
            {/* Page Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 className="text-2xl lg:text-3xl font-bold text-slate-800">Subsidy Explorer</h1>
                    <p className="text-slate-500 mt-1">Discover and apply for government schemes tailored to your business</p>
                </div>
                <div className="flex gap-3">
                    <Badge variant="success" className="py-2 px-4">
                        <Sparkles className="w-4 h-4 mr-1" />
                        Powered by Subsidy Hunter AI
                    </Badge>
                </div>
            </div>

            {/* Search & Filters */}
            <Card>
                <CardContent className="pt-6">
                    <div className="flex flex-col md:flex-row gap-4">
                        <div className="flex-1 relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
                            <input
                                type="text"
                                placeholder="What subsidies am I eligible for?"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                            />
                        </div>
                        <div className="flex gap-2">
                            <select
                                value={selectedFilters.sector}
                                onChange={(e) => setSelectedFilters({ ...selectedFilters, sector: e.target.value })}
                                className="px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 text-sm"
                            >
                                <option value="all">All Sectors</option>
                                <option value="manufacturing">Manufacturing</option>
                                <option value="services">Services</option>
                                <option value="trading">Trading</option>
                            </select>
                            <select
                                value={selectedFilters.size}
                                onChange={(e) => setSelectedFilters({ ...selectedFilters, size: e.target.value })}
                                className="px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 text-sm"
                            >
                                <option value="all">Business Size</option>
                                <option value="micro">Micro</option>
                                <option value="small">Small</option>
                                <option value="medium">Medium</option>
                            </select>
                            <Button variant="outline" icon={Filter}>
                                More Filters
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Stats Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                    <CardContent className="pt-6">
                        <div className="text-center">
                            <p className="text-3xl font-bold text-primary">{filteredSubsidies.length}</p>
                            <p className="text-sm text-slate-500">Schemes Found</p>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="text-center">
                            <p className="text-3xl font-bold text-emerald-600">₹47.5L</p>
                            <p className="text-sm text-slate-500">Max Benefit</p>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="text-center">
                            <p className="text-3xl font-bold text-blue-600">3</p>
                            <p className="text-sm text-slate-500">Applications Active</p>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="text-center">
                            <p className="text-3xl font-bold text-purple-600">₹5L</p>
                            <p className="text-sm text-slate-500">Received This Year</p>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div className="grid lg:grid-cols-3 gap-6">
                {/* Subsidy Cards */}
                <div className="lg:col-span-2 space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-semibold text-slate-800">Recommended Schemes</h2>
                        <span className="text-sm text-slate-500">Sorted by match score</span>
                    </div>

                    <div className="grid md:grid-cols-2 gap-4">
                        {filteredSubsidies.map((subsidy) => (
                            <Card
                                key={subsidy.id}
                                className="hover:shadow-lg transition-shadow cursor-pointer group"
                                onClick={() => setSelectedSubsidy(subsidy)}
                            >
                                <CardContent className="pt-6">
                                    <div className="flex items-start justify-between mb-4">
                                        <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center text-2xl">
                                            {subsidy.logo}
                                        </div>
                                        <div className={`flex items-center gap-1 ${getMatchColor(subsidy.matchScore)}`}>
                                            <Star className="w-4 h-4 fill-current" />
                                            <span className="font-bold">{subsidy.matchScore}%</span>
                                        </div>
                                    </div>

                                    <h3 className="font-semibold text-slate-800 mb-2 group-hover:text-primary transition-colors">
                                        {subsidy.name}
                                    </h3>

                                    <div className="bg-emerald-50 text-emerald-700 px-3 py-2 rounded-lg text-sm font-medium mb-3">
                                        {subsidy.benefit}
                                    </div>

                                    <div className="space-y-2 mb-4">
                                        <div className="flex items-center gap-2 text-sm text-slate-600">
                                            <Banknote className="w-4 h-4" />
                                            <span>Max: ₹{(subsidy.maxAmount / 100000).toFixed(1)} Lakhs</span>
                                        </div>
                                        <div className="flex items-center gap-2 text-sm text-slate-600">
                                            <Clock className="w-4 h-4" />
                                            <span>Deadline: {subsidy.deadline}</span>
                                        </div>
                                        <div className="flex items-center gap-2 text-sm text-slate-600">
                                            <Building2 className="w-4 h-4" />
                                            <span>{subsidy.sector}</span>
                                        </div>
                                    </div>

                                    <div className="flex gap-2">
                                        <Button
                                            size="sm"
                                            className="flex-1"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setSelectedSubsidy(subsidy);
                                                setShowApplicationModal(true);
                                            }}
                                        >
                                            Auto-Draft Application
                                        </Button>
                                        <Button
                                            size="sm"
                                            variant="ghost"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setSelectedSubsidy(subsidy);
                                            }}
                                        >
                                            <ChevronRight className="w-4 h-4" />
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>

                {/* Application Tracker & Timeline */}
                <div className="space-y-6">
                    {/* Application Tracker */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <FileText className="w-5 h-5" />
                                Application Tracker
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-0">
                            <div className="divide-y divide-slate-100">
                                {applications.map((app) => (
                                    <div key={app.id} className="p-4 hover:bg-slate-50 transition-colors">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="font-medium text-slate-800">{app.scheme}</span>
                                            {getStatusBadge(app.status)}
                                        </div>
                                        <div className="flex items-center justify-between text-sm">
                                            <span className="text-slate-500">{app.date}</span>
                                            <span className="font-medium text-slate-700">
                                                ₹{(app.amount / 100000).toFixed(1)}L
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Subsidy Timeline */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <TrendingUp className="w-5 h-5" />
                                Subsidies Received
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <SubsidyBarChart data={subsidyTimeline.map(item => ({ name: item.month, amount: item.amount }))} />
                            <div className="mt-4 p-4 bg-emerald-50 rounded-xl border border-emerald-100">
                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-emerald-700">Total Received (FY 2023-24)</span>
                                    <span className="text-lg font-bold text-emerald-800">₹7,50,000</span>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Quick Tips */}
                    <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-100">
                        <CardContent className="pt-6">
                            <div className="flex items-start gap-3">
                                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                                    <AlertCircle className="w-5 h-5 text-blue-600" />
                                </div>
                                <div>
                                    <h4 className="font-semibold text-blue-900 mb-1">Pro Tip</h4>
                                    <p className="text-sm text-blue-700">
                                        Complete your business profile to get more accurate subsidy matches.
                                        Your match score can improve by up to 20%.
                                    </p>
                                    <Button variant="ghost" size="sm" className="mt-2 text-blue-700 hover:text-blue-800 p-0">
                                        Complete Profile →
                                    </Button>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* Subsidy Detail Modal */}
            <Modal
                isOpen={selectedSubsidy && !showApplicationModal}
                onClose={() => setSelectedSubsidy(null)}
                title={selectedSubsidy?.name}
                size="lg"
            >
                {selectedSubsidy && (
                    <div className="space-y-6">
                        {/* Match Score */}
                        <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl">
                            <div>
                                <p className="text-sm text-slate-500">Your Match Score</p>
                                <p className={`text-3xl font-bold ${getMatchColor(selectedSubsidy.matchScore)}`}>
                                    {selectedSubsidy.matchScore}%
                                </p>
                            </div>
                            <div className="text-right">
                                <p className="text-sm text-slate-500">Maximum Benefit</p>
                                <p className="text-2xl font-bold text-slate-800">
                                    ₹{(selectedSubsidy.maxAmount / 100000).toFixed(1)} Lakhs
                                </p>
                            </div>
                        </div>

                        {/* Description */}
                        <div>
                            <h4 className="font-medium text-slate-800 mb-2">About this Scheme</h4>
                            <p className="text-slate-600">{selectedSubsidy.description}</p>
                        </div>

                        {/* Eligibility */}
                        <div>
                            <h4 className="font-medium text-slate-800 mb-2">Eligibility Criteria</h4>
                            <ul className="space-y-2">
                                {selectedSubsidy.eligibility.map((item, index) => (
                                    <li key={index} className="flex items-start gap-2 text-sm text-slate-600">
                                        <CheckCircle className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                                        {item}
                                    </li>
                                ))}
                            </ul>
                        </div>

                        {/* Documents Required */}
                        <div>
                            <h4 className="font-medium text-slate-800 mb-2">Documents Required</h4>
                            <div className="flex flex-wrap gap-2">
                                {selectedSubsidy.documentsRequired.map((doc, index) => (
                                    <Badge key={index} variant="default">{doc}</Badge>
                                ))}
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="flex gap-3 pt-4 border-t border-slate-100">
                            <Button
                                className="flex-1"
                                onClick={() => setShowApplicationModal(true)}
                            >
                                <Sparkles className="w-4 h-4 mr-2" />
                                Auto-Draft Application
                            </Button>
                            <Button variant="outline" icon={Download}>
                                Download Details
                            </Button>
                        </div>
                    </div>
                )}
            </Modal>

            {/* Application Draft Modal */}
            <Modal
                isOpen={showApplicationModal}
                onClose={() => {
                    setShowApplicationModal(false);
                    setSelectedSubsidy(null);
                }}
                title="Auto-Draft Application"
                description={selectedSubsidy?.name}
                size="lg"
            >
                {selectedSubsidy && (
                    <div className="space-y-6">
                        <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-200">
                            <div className="flex items-center gap-3">
                                <Sparkles className="w-5 h-5 text-emerald-600" />
                                <div>
                                    <p className="font-medium text-emerald-800">AI-Assisted Application</p>
                                    <p className="text-sm text-emerald-600">
                                        Our Subsidy Hunter AI has pre-filled 80% of your application based on your business profile.
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Pre-filled form fields */}
                        <div className="space-y-4">
                            <div>
                                <label className="text-sm font-medium text-slate-700">Business Name</label>
                                <input
                                    type="text"
                                    defaultValue="Tech Solutions Pvt Ltd"
                                    className="w-full mt-1 px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                                />
                            </div>
                            <div>
                                <label className="text-sm font-medium text-slate-700">GSTIN</label>
                                <input
                                    type="text"
                                    defaultValue="29AABCU9603R1ZM"
                                    className="w-full mt-1 px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                                />
                            </div>
                            <div>
                                <label className="text-sm font-medium text-slate-700">Udyam Registration</label>
                                <input
                                    type="text"
                                    defaultValue="UDYAM-KA-01-0012345"
                                    className="w-full mt-1 px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                                />
                            </div>
                            <div>
                                <label className="text-sm font-medium text-slate-700">Requested Amount (₹)</label>
                                <input
                                    type="number"
                                    defaultValue={selectedSubsidy.maxAmount}
                                    className="w-full mt-1 px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                                />
                            </div>
                            <div>
                                <label className="text-sm font-medium text-slate-700">Project Description</label>
                                <textarea
                                    rows={3}
                                    defaultValue="Technology upgradation project for implementing automated manufacturing systems to improve production efficiency and reduce waste."
                                    className="w-full mt-1 px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                                />
                            </div>
                        </div>

                        {/* Document Upload */}
                        <div>
                            <label className="text-sm font-medium text-slate-700 mb-2 block">Required Documents</label>
                            <div className="space-y-2">
                                {selectedSubsidy.documentsRequired.map((doc, index) => (
                                    <div key={index} className="flex items-center justify-between p-3 border border-slate-200 rounded-lg">
                                        <div className="flex items-center gap-2">
                                            <FileText className="w-4 h-4 text-slate-400" />
                                            <span className="text-sm text-slate-700">{doc}</span>
                                        </div>
                                        <Button variant="ghost" size="sm">Upload</Button>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="flex gap-3 pt-4 border-t border-slate-100">
                            <Button variant="outline" className="flex-1">
                                Save as Draft
                            </Button>
                            <Button className="flex-1" icon={Send}>
                                Submit Application
                            </Button>
                        </div>
                    </div>
                )}
            </Modal>
        </div>
    );
};

export default SubsidyExplorer;
