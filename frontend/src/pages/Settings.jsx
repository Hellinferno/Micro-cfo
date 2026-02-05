import React, { useState } from 'react';
import {
    User,
    Building2,
    Bell,
    Shield,
    Globe,
    Smartphone,
    Mail,
    MessageSquare,
    CreditCard,
    Download,
    Trash2,
    Eye,
    EyeOff,
    ChevronRight,
    CheckCircle,
    AlertCircle,
    Settings as SettingsIcon,
    Zap,
    Link2
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, Button, Badge } from '../components/ui';

const Settings = () => {
    const [activeTab, setActiveTab] = useState('profile');
    const [showGST, setShowGST] = useState(false);

    const tabs = [
        { id: 'profile', label: 'Business Profile', icon: Building2 },
        { id: 'agents', label: 'AI Agents', icon: Zap },
        { id: 'notifications', label: 'Notifications', icon: Bell },
        { id: 'privacy', label: 'Data & Privacy', icon: Shield },
        { id: 'integrations', label: 'Integrations', icon: Link2 },
    ];

    const agentSettings = [
        {
            name: 'Visual Auditor',
            description: 'Automatically audit uploaded invoices and bills',
            enabled: true,
            autoExecute: true,
        },
        {
            name: 'Legal Sentinel',
            description: 'Monitor regulatory changes and compliance deadlines',
            enabled: true,
            autoExecute: false,
        },
        {
            name: 'Subsidy Hunter',
            description: 'Find and match government schemes to your business',
            enabled: true,
            autoExecute: false,
        },
        {
            name: 'Negotiator',
            description: 'Generate and send payment follow-up emails',
            enabled: true,
            autoExecute: false,
        },
    ];

    const notificationChannels = [
        { id: 'telegram', label: 'Telegram', icon: MessageSquare, connected: true },
        { id: 'email', label: 'Email', icon: Mail, connected: true },
        { id: 'sms', label: 'SMS', icon: Smartphone, connected: false },
        { id: 'inapp', label: 'In-App', icon: Bell, connected: true },
    ];

    const integrations = [
        { name: 'Telegram Bot', status: 'connected', icon: MessageSquare },
        { name: 'Account Aggregator', status: 'pending', icon: CreditCard },
        { name: 'Tally', status: 'disconnected', icon: Building2 },
        { name: 'Zoho Books', status: 'disconnected', icon: Building2 },
    ];

    return (
        <div className="p-4 lg:p-8 bg-slate-50 min-h-screen">
            <div className="max-w-5xl mx-auto">
                {/* Page Header */}
                <div className="mb-6">
                    <h1 className="text-2xl lg:text-3xl font-bold text-slate-800">Settings</h1>
                    <p className="text-slate-500 mt-1">Manage your account and preferences</p>
                </div>

                <div className="flex flex-col lg:flex-row gap-6">
                    {/* Sidebar Navigation */}
                    <div className="lg:w-64 flex-shrink-0">
                        <Card>
                            <CardContent className="p-2">
                                <nav className="space-y-1">
                                    {tabs.map((tab) => (
                                        <button
                                            key={tab.id}
                                            onClick={() => setActiveTab(tab.id)}
                                            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
                                                activeTab === tab.id
                                                    ? 'bg-primary/10 text-primary'
                                                    : 'text-slate-600 hover:bg-slate-100'
                                            }`}
                                        >
                                            <tab.icon className="w-5 h-5" />
                                            <span className="font-medium">{tab.label}</span>
                                        </button>
                                    ))}
                                </nav>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Content Area */}
                    <div className="flex-1 space-y-6">
                        {/* Business Profile Tab */}
                        {activeTab === 'profile' && (
                            <>
                                <Card>
                                    <CardHeader>
                                        <CardTitle>Company Information</CardTitle>
                                    </CardHeader>
                                    <CardContent className="space-y-4">
                                        <div className="grid md:grid-cols-2 gap-4">
                                            <div>
                                                <label className="text-sm font-medium text-slate-700">Company Name</label>
                                                <input
                                                    type="text"
                                                    defaultValue="Tech Solutions Pvt Ltd"
                                                    className="w-full mt-1 px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                                                />
                                            </div>
                                            <div>
                                                <label className="text-sm font-medium text-slate-700">Business Type</label>
                                                <select className="w-full mt-1 px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50">
                                                    <option>Private Limited Company</option>
                                                    <option>LLP</option>
                                                    <option>Proprietorship</option>
                                                    <option>Partnership</option>
                                                </select>
                                            </div>
                                            <div>
                                                <label className="text-sm font-medium text-slate-700">GSTIN</label>
                                                <div className="relative">
                                                    <input
                                                        type={showGST ? 'text' : 'password'}
                                                        defaultValue="29AABCU9603R1ZM"
                                                        className="w-full mt-1 px-4 py-2 pr-10 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                                                    />
                                                    <button
                                                        onClick={() => setShowGST(!showGST)}
                                                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400"
                                                    >
                                                        {showGST ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                                    </button>
                                                </div>
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
                                                <label className="text-sm font-medium text-slate-700">Industry Sector</label>
                                                <select className="w-full mt-1 px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50">
                                                    <option>Manufacturing</option>
                                                    <option>Services</option>
                                                    <option>Trading</option>
                                                    <option>IT & Software</option>
                                                </select>
                                            </div>
                                            <div>
                                                <label className="text-sm font-medium text-slate-700">Annual Revenue</label>
                                                <select className="w-full mt-1 px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50">
                                                    <option>Below ₹1 Crore</option>
                                                    <option>₹1 - 5 Crore</option>
                                                    <option>₹5 - 10 Crore</option>
                                                    <option>₹10 - 50 Crore</option>
                                                    <option>Above ₹50 Crore</option>
                                                </select>
                                            </div>
                                        </div>
                                        <div className="pt-4 border-t border-slate-100">
                                            <Button>Save Changes</Button>
                                        </div>
                                    </CardContent>
                                </Card>

                                <Card>
                                    <CardHeader>
                                        <CardTitle>Contact Information</CardTitle>
                                    </CardHeader>
                                    <CardContent className="space-y-4">
                                        <div className="grid md:grid-cols-2 gap-4">
                                            <div>
                                                <label className="text-sm font-medium text-slate-700">Primary Email</label>
                                                <input
                                                    type="email"
                                                    defaultValue="admin@techsolutions.com"
                                                    className="w-full mt-1 px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                                                />
                                            </div>
                                            <div>
                                                <label className="text-sm font-medium text-slate-700">Phone Number</label>
                                                <input
                                                    type="tel"
                                                    defaultValue="+91 98765 43210"
                                                    className="w-full mt-1 px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                                                />
                                            </div>
                                            <div className="md:col-span-2">
                                                <label className="text-sm font-medium text-slate-700">Business Address</label>
                                                <textarea
                                                    rows={2}
                                                    defaultValue="123, Industrial Estate, Whitefield, Bangalore - 560066"
                                                    className="w-full mt-1 px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                                                />
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            </>
                        )}

                        {/* AI Agents Tab */}
                        {activeTab === 'agents' && (
                            <Card>
                                <CardHeader>
                                    <CardTitle>AI Agent Configuration</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    {agentSettings.map((agent, index) => (
                                        <div key={index} className="p-4 border border-slate-200 rounded-xl">
                                            <div className="flex items-start justify-between">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2">
                                                        <h4 className="font-semibold text-slate-800">{agent.name}</h4>
                                                        <Badge variant={agent.enabled ? 'success' : 'default'}>
                                                            {agent.enabled ? 'Active' : 'Inactive'}
                                                        </Badge>
                                                    </div>
                                                    <p className="text-sm text-slate-500 mt-1">{agent.description}</p>
                                                </div>
                                                <label className="relative inline-flex items-center cursor-pointer">
                                                    <input
                                                        type="checkbox"
                                                        defaultChecked={agent.enabled}
                                                        className="sr-only peer"
                                                    />
                                                    <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                                                </label>
                                            </div>
                                            <div className="mt-4 pt-4 border-t border-slate-100">
                                                <div className="flex items-center justify-between">
                                                    <span className="text-sm text-slate-600">Auto-execute actions</span>
                                                    <select className="px-3 py-1 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50">
                                                        <option value="manual">Manual Review</option>
                                                        <option value="auto">Auto-Execute</option>
                                                    </select>
                                                </div>
                                            </div>
                                        </div>
                                    ))}

                                    <div className="p-4 bg-blue-50 rounded-xl border border-blue-100">
                                        <div className="flex items-center gap-2 mb-2">
                                            <Globe className="w-5 h-5 text-blue-600" />
                                            <span className="font-medium text-blue-800">Language Preference</span>
                                        </div>
                                        <select className="w-full px-4 py-2 border border-blue-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary/50">
                                            <option>English</option>
                                            <option>Hindi</option>
                                            <option>Tamil</option>
                                            <option>Telugu</option>
                                            <option>Marathi</option>
                                        </select>
                                    </div>
                                </CardContent>
                            </Card>
                        )}

                        {/* Notifications Tab */}
                        {activeTab === 'notifications' && (
                            <>
                                <Card>
                                    <CardHeader>
                                        <CardTitle>Notification Channels</CardTitle>
                                    </CardHeader>
                                    <CardContent className="space-y-4">
                                        {notificationChannels.map((channel) => (
                                            <div key={channel.id} className="flex items-center justify-between p-4 border border-slate-200 rounded-xl">
                                                <div className="flex items-center gap-3">
                                                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                                                        channel.connected ? 'bg-emerald-100' : 'bg-slate-100'
                                                    }`}>
                                                        <channel.icon className={`w-5 h-5 ${
                                                            channel.connected ? 'text-emerald-600' : 'text-slate-400'
                                                        }`} />
                                                    </div>
                                                    <div>
                                                        <p className="font-medium text-slate-800">{channel.label}</p>
                                                        <p className="text-sm text-slate-500">
                                                            {channel.connected ? 'Connected' : 'Not connected'}
                                                        </p>
                                                    </div>
                                                </div>
                                                <label className="relative inline-flex items-center cursor-pointer">
                                                    <input
                                                        type="checkbox"
                                                        defaultChecked={channel.connected}
                                                        className="sr-only peer"
                                                    />
                                                    <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                                                </label>
                                            </div>
                                        ))}
                                    </CardContent>
                                </Card>

                                <Card>
                                    <CardHeader>
                                        <CardTitle>Notification Preferences</CardTitle>
                                    </CardHeader>
                                    <CardContent className="space-y-4">
                                        <div>
                                            <label className="text-sm font-medium text-slate-700">Frequency</label>
                                            <select className="w-full mt-1 px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50">
                                                <option>Real-time</option>
                                                <option>Daily digest</option>
                                                <option>Weekly summary</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="text-sm font-medium text-slate-700">Priority Filter</label>
                                            <select className="w-full mt-1 px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50">
                                                <option>All alerts</option>
                                                <option>Critical only</option>
                                                <option>Critical and warnings</option>
                                            </select>
                                        </div>
                                    </CardContent>
                                </Card>
                            </>
                        )}

                        {/* Privacy Tab */}
                        {activeTab === 'privacy' && (
                            <>
                                <Card>
                                    <CardHeader>
                                        <CardTitle>Data Management</CardTitle>
                                    </CardHeader>
                                    <CardContent className="space-y-4">
                                        <div className="flex items-center justify-between p-4 border border-slate-200 rounded-xl">
                                            <div>
                                                <h4 className="font-medium text-slate-800">Export Financial Data</h4>
                                                <p className="text-sm text-slate-500">Download all your data as CSV or PDF</p>
                                            </div>
                                            <Button variant="outline" icon={Download}>Export</Button>
                                        </div>
                                        <div className="flex items-center justify-between p-4 border border-red-200 bg-red-50 rounded-xl">
                                            <div>
                                                <h4 className="font-medium text-red-800">Delete Account</h4>
                                                <p className="text-sm text-red-600">Permanently delete your account and all data</p>
                                            </div>
                                            <Button variant="danger" icon={Trash2}>Delete</Button>
                                        </div>
                                    </CardContent>
                                </Card>

                                <Card>
                                    <CardHeader>
                                        <CardTitle>Data Retention</CardTitle>
                                    </CardHeader>
                                    <CardContent className="space-y-4">
                                        <div>
                                            <label className="text-sm font-medium text-slate-700">Document Storage Period</label>
                                            <select className="w-full mt-1 px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50">
                                                <option>1 year</option>
                                                <option>3 years</option>
                                                <option>5 years</option>
                                                <option>7 years (Recommended for compliance)</option>
                                            </select>
                                        </div>
                                        <p className="text-sm text-slate-500">
                                            Note: Financial records should be retained for at least 7 years as per tax regulations.
                                        </p>
                                    </CardContent>
                                </Card>
                            </>
                        )}

                        {/* Integrations Tab */}
                        {activeTab === 'integrations' && (
                            <Card>
                                <CardHeader>
                                    <CardTitle>Connected Services</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    {integrations.map((integration, index) => (
                                        <div key={index} className="flex items-center justify-between p-4 border border-slate-200 rounded-xl">
                                            <div className="flex items-center gap-3">
                                                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                                                    integration.status === 'connected' ? 'bg-emerald-100' :
                                                    integration.status === 'pending' ? 'bg-amber-100' : 'bg-slate-100'
                                                }`}>
                                                    <integration.icon className={`w-5 h-5 ${
                                                        integration.status === 'connected' ? 'text-emerald-600' :
                                                        integration.status === 'pending' ? 'text-amber-600' : 'text-slate-400'
                                                    }`} />
                                                </div>
                                                <div>
                                                    <p className="font-medium text-slate-800">{integration.name}</p>
                                                    <Badge 
                                                        variant={
                                                            integration.status === 'connected' ? 'success' :
                                                            integration.status === 'pending' ? 'warning' : 'default'
                                                        }
                                                        size="sm"
                                                    >
                                                        {integration.status}
                                                    </Badge>
                                                </div>
                                            </div>
                                            <Button 
                                                variant={integration.status === 'connected' ? 'outline' : 'primary'}
                                                size="sm"
                                            >
                                                {integration.status === 'connected' ? 'Disconnect' : 'Connect'}
                                            </Button>
                                        </div>
                                    ))}
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Settings;
