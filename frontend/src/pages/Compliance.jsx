import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Search, AlertCircle, CheckCircle, BookOpen } from 'lucide-react';
import { Card, CardHeader, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

const Compliance = () => {
    const navigate = useNavigate();
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [history, setHistory] = useState([
        { id: 1, query: 'Can I claim ITC on office supplies?', risk: 'LOW', date: '2024-01-15' },
        { id: 2, query: 'GST filing deadline for Q4?', risk: 'MEDIUM', date: '2024-01-14' },
        { id: 3, query: 'Blocked credits under Section 17(5)', risk: 'HIGH', date: '2024-01-13' }
    ]);

    const handleQuery = async () => {
        if (!query.trim()) return;

        setLoading(true);
        setResult(null);

        try {
            const response = await fetch('http://localhost:8000/api/v1/compliance/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    user_context: {
                        turnover_tier: '3-5 crore',
                        sector: 'Manufacturing'
                    }
                })
            });

            if (!response.ok) throw new Error('Failed to get compliance response');

            const data = await response.json();
            setResult(data);

            // Add to history
            setHistory(prev => [{
                id: Date.now(),
                query: query,
                risk: data.risk_level,
                date: new Date().toISOString().split('T')[0]
            }, ...prev]);

        } catch (error) {
            console.error('Error:', error);
        } finally {
            setLoading(false);
        }
    };

    const getRiskColor = (risk) => {
        const colors = {
            LOW: 'badge-success',
            MEDIUM: 'badge-warning',
            HIGH: 'badge-danger',
            CRITICAL: 'badge-danger'
        };
        return colors[risk] || 'badge-default';
    };

    return (
        <div className="min-h-screen bg-slate-50 p-6 lg:p-8">
            <div className="max-w-6xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900">Compliance Center</h1>
                        <p className="text-slate-500 mt-1">Legal Sentinel - AI-powered compliance guidance</p>
                    </div>
                    <Button variant="outline" onClick={() => navigate('/history')}>
                        View History
                    </Button>
                </div>

                {/* Quick Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card>
                        <CardContent className="p-6">
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-green-100 rounded-lg">
                                    <CheckCircle className="w-6 h-6 text-green-600" />
                                </div>
                                <div>
                                    <p className="text-sm text-slate-600">Compliance Score</p>
                                    <p className="text-2xl font-bold text-slate-900">94%</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="p-6">
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-blue-100 rounded-lg">
                                    <BookOpen className="w-6 h-6 text-blue-600" />
                                </div>
                                <div>
                                    <p className="text-sm text-slate-600">Laws Monitored</p>
                                    <p className="text-2xl font-bold text-slate-900">12</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="p-6">
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-yellow-100 rounded-lg">
                                    <AlertCircle className="w-6 h-6 text-yellow-600" />
                                </div>
                                <div>
                                    <p className="text-sm text-slate-600">Active Alerts</p>
                                    <p className="text-2xl font-bold text-slate-900">3</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Query Input */}
                <Card>
                    <CardHeader>
                        <h2 className="text-lg font-semibold text-slate-900">Ask a Compliance Question</h2>
                    </CardHeader>
                    <CardContent>
                        <div className="flex gap-3">
                            <div className="flex-1 relative">
                                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
                                <input
                                    type="text"
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && handleQuery()}
                                    placeholder="e.g., Can I claim ITC on food expenses?"
                                    className="input pl-10"
                                />
                            </div>
                            <Button onClick={handleQuery} disabled={loading || !query.trim()}>
                                {loading ? 'Checking...' : 'Check Compliance'}
                            </Button>
                        </div>

                        {/* Sample Questions */}
                        <div className="mt-4 flex flex-wrap gap-2">
                            <span className="text-sm text-slate-500">Try:</span>
                            <Button
                                size="sm"
                                variant="outline"
                                onClick={() => setQuery('What are the blocked credits under Section 17(5)?')}
                            >
                                Section 17(5) blocked credits
                            </Button>
                            <Button
                                size="sm"
                                variant="outline"
                                onClick={() => setQuery('ITC eligibility for capital goods')}
                            >
                                ITC on capital goods
                            </Button>
                            <Button
                                size="sm"
                                variant="outline"
                                onClick={() => setQuery('GST filing deadlines for MSME')}
                            >
                                GST filing deadlines
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                {/* Result */}
                {result && (
                    <Card>
                        <CardHeader>
                            <div className="flex items-center justify-between">
                                <h2 className="text-lg font-semibold text-slate-900">Compliance Assessment</h2>
                                <Badge className={getRiskColor(result.risk_level)}>
                                    Risk: {result.risk_level}
                                </Badge>
                            </div>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <p className="text-slate-700 leading-relaxed">{result.explanation}</p>

                            {/* Relevant Sections */}
                            {result.relevant_sections && result.relevant_sections.length > 0 && (
                                <div>
                                    <h3 className="font-semibold text-slate-900 mb-2">Relevant Sections</h3>
                                    <div className="space-y-2">
                                        {result.relevant_sections.map((section, index) => (
                                            <div key={index} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                                                <div className="flex items-start justify-between mb-1">
                                                    <div>
                                                        <p className="font-semibold text-slate-900">{section.section_number}</p>
                                                        <p className="text-sm text-slate-600">{section.act_name}</p>
                                                    </div>
                                                    <Badge variant="info">{(section.relevance_score * 100).toFixed(0)}% relevant</Badge>
                                                </div>
                                                <p className="text-sm text-slate-700 mt-2">{section.description}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Recommended Action */}
                            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                                <div className="flex items-start gap-3">
                                    <Shield className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                                    <div>
                                        <p className="font-semibold text-blue-900 mb-1">Recommended Action</p>
                                        <p className="text-sm text-blue-700">{result.compliant_action}</p>
                                    </div>
                                </div>
                            </div>

                            {/* Warnings */}
                            {result.warnings && result.warnings.length > 0 && (
                                <div className="space-y-2">
                                    {result.warnings.map((warning, index) => (
                                        <div key={index} className="flex items-center gap-2 text-sm text-yellow-700 bg-yellow-50 p-2 rounded">
                                            <AlertCircle className="w-4 h-4" />
                                            <span>{warning}</span>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Actions */}
                            <div className="flex gap-3 pt-4">
                                <Button variant="outline">Save Answer</Button>
                                <Button variant="outline">Export PDF</Button>
                                <Button onClick={() => navigate('/chat')}>Ask Follow-up</Button>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Query History */}
                <Card>
                    <CardHeader>
                        <h2 className="text-lg font-semibold text-slate-900">Recent Queries</h2>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {history.map((item) => (
                                <div
                                    key={item.id}
                                    className="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                                    onClick={() => setQuery(item.query)}
                                >
                                    <div className="flex-1">
                                        <p className="text-sm font-medium text-slate-900">{item.query}</p>
                                        <p className="text-xs text-slate-500 mt-1">{item.date}</p>
                                    </div>
                                    <Badge className={getRiskColor(item.risk)}>{item.risk}</Badge>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default Compliance;
