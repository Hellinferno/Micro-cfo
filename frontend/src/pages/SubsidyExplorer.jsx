import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Percent, Search, Filter, ExternalLink, Calendar, Building } from 'lucide-react';
import { Card, CardHeader, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

const SubsidyExplorer = () => {
    const navigate = useNavigate();
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedSector, setSelectedSector] = useState('');
    const [capex, setCapex] = useState('');
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState([]);

    const sectors = [
        'Textile', 'Manufacturing', 'Food Processing', 'Agriculture',
        'IT/Software', 'Pharmaceuticals', 'Services', 'Women Entrepreneur',
        'Green Technology'
    ];

    const handleSearch = async () => {
        setLoading(true);

        try {
            const response = await fetch('http://localhost:8000/api/v1/subsidies/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    sector: selectedSector || undefined,
                    capex: capex ? parseFloat(capex) : undefined,
                    query: searchQuery || undefined
                })
            });

            if (!response.ok) throw new Error('Search failed');

            const data = await response.json();
            setResults(data.schemes || []);
        } catch (error) {
            console.error('Error:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900">Subsidy Explorer</h1>
                        <p className="text-slate-500 mt-1">Discover government schemes for your business</p>
                    </div>
                    <Button variant="outline" onClick={() => navigate('/chat')}>
                        Ask About Subsidies
                    </Button>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <StatCard label="Total Schemes" value="248" />
                    <StatCard label="Central Schemes" value="86" />
                    <StatCard label="State Schemes" value="162" />
                    <StatCard label="Your Matches" value="12" highlight />
                </div>

                {/* Search Filters */}
                <Card>
                    <CardHeader>
                        <h2 className="text-lg font-semibold text-slate-900">Search Subsidies</h2>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div className="md:col-span-2">
                                <label className="block text-sm font-medium text-slate-700 mb-2">
                                    Search Query
                                </label>
                                <div className="relative">
                                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
                                    <input
                                        type="text"
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        placeholder="e.g., textile machinery, technology upgrade"
                                        className="input pl-10"
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">
                                    Sector
                                </label>
                                <select
                                    value={selectedSector}
                                    onChange={(e) => setSelectedSector(e.target.value)}
                                    className="input"
                                >
                                    <option value="">All Sectors</option>
                                    {sectors.map((sector) => (
                                        <option key={sector} value={sector}>{sector}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">
                                    CAPEX (₹)
                                </label>
                                <input
                                    type="number"
                                    value={capex}
                                    onChange={(e) => setCapex(e.target.value)}
                                    placeholder="e.g., 1000000"
                                    className="input"
                                />
                            </div>
                        </div>
                        <div className="mt-4 flex gap-3">
                            <Button onClick={handleSearch} disabled={loading}>
                                {loading ? 'Searching...' : 'Search Schemes'}
                            </Button>
                            <Button variant="outline" onClick={() => {
                                setSearchQuery('');
                                setSelectedSector('');
                                setCapex('');
                                setResults([]);
                            }}>
                                Reset Filters
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                {/* Results */}
                {results.length > 0 && (
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <h2 className="text-lg font-semibold text-slate-900">
                                Found {results.length} schemes
                            </h2>
                            <div className="flex items-center gap-2 text-sm text-slate-500">
                                <Filter className="w-4 h-4" />
                                Sorted by match score
                            </div>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                            {results.map((scheme, index) => (
                                <SchemeCard key={index} scheme={scheme} />
                            ))}
                        </div>
                    </div>
                )}

                {/* Featured Schemes (when no search) */}
                {results.length === 0 && !loading && (
                    <div className="space-y-6">
                        <h2 className="text-lg font-semibold text-slate-900">Featured Schemes</h2>
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                            <FeaturedSchemeCard
                                name="Technology Upgradation Fund Scheme (TUFS)"
                                benefit="Up to 25% subsidy on capital goods"
                                sector="Textile"
                                deadline="2024-03-31"
                                matchScore={95}
                            />
                            <FeaturedSchemeCard
                                name="MSME Technology Centre"
                                benefit="50% subsidy on plant & machinery"
                                sector="Manufacturing"
                                deadline="2024-02-28"
                                matchScore={88}
                            />
                            <FeaturedSchemeCard
                                name="Production Linked Incentive (PLI)"
                                benefit="4-6% incentive on incremental sales"
                                sector="Manufacturing"
                                deadline="2024-12-31"
                                matchScore={85}
                            />
                            <FeaturedSchemeCard
                                name="Digital India Initiative"
                                benefit="Support for IT infrastructure"
                                sector="IT/Software"
                                deadline="2024-06-30"
                                matchScore={82}
                            />
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

// Sub-components

const StatCard = ({ label, value, highlight }) => (
    <Card>
        <CardContent className="p-6">
            <p className="text-sm text-slate-600 mb-1">{label}</p>
            <p className={`text-2xl font-bold ${highlight ? 'text-primary-600' : 'text-slate-900'}`}>
                {value}
            </p>
        </CardContent>
    </Card>
);

const SchemeCard = ({ scheme }) => {
    const getMatchColor = (score) => {
        if (score >= 90) return 'badge-success';
        if (score >= 75) return 'badge-warning';
        return 'badge-info';
    };

    return (
        <Card className="card-hover">
            <CardContent className="p-6 space-y-4">
                <div className="flex items-start justify-between">
                    <div className="flex-1">
                        <h3 className="font-semibold text-slate-900 text-lg">{scheme.name}</h3>
                        <div className="flex items-center gap-2 mt-2">
                            <Building className="w-4 h-4 text-slate-400" />
                            <span className="text-sm text-slate-600">{scheme.ministry}</span>
                        </div>
                    </div>
                    <Badge className={getMatchColor(scheme.match_score)}>
                        {(scheme.match_score * 100).toFixed(0)}% match
                    </Badge>
                </div>

                <div className="space-y-2">
                    <div>
                        <p className="text-sm font-medium text-slate-700">Benefit</p>
                        <p className="text-slate-600">{scheme.benefit}</p>
                    </div>
                    <div>
                        <p className="text-sm font-medium text-slate-700">Eligibility</p>
                        <p className="text-slate-600">{scheme.eligibility}</p>
                    </div>
                    {scheme.max_subsidy && (
                        <div>
                            <p className="text-sm font-medium text-slate-700">Max Subsidy</p>
                            <p className="text-slate-600 font-semibold">{scheme.max_subsidy}</p>
                        </div>
                    )}
                </div>

                <div className="flex gap-3 pt-2">
                    <Button size="sm" className="flex-1">
                        Check Eligibility
                    </Button>
                    <Button size="sm" variant="outline">
                        <ExternalLink className="w-4 h-4" />
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
};

const FeaturedSchemeCard = ({ name, benefit, sector, deadline, matchScore }) => (
    <Card className="card-hover border-l-4 border-l-primary-500">
        <CardContent className="p-6 space-y-3">
            <div className="flex items-start justify-between">
                <h3 className="font-semibold text-slate-900">{name}</h3>
                <Badge className="badge-success">{matchScore}% match</Badge>
            </div>
            <p className="text-slate-600">{benefit}</p>
            <div className="flex items-center justify-between text-sm text-slate-500">
                <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    <span>Deadline: {deadline}</span>
                </div>
                <Badge variant="info">{sector}</Badge>
            </div>
            <Button size="sm" className="w-full">View Details</Button>
        </CardContent>
    </Card>
);

export default SubsidyExplorer;
