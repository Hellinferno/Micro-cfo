import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, Camera, FileText, CheckCircle, AlertCircle, XCircle, Loader } from 'lucide-react';
import { Card, CardHeader, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import InvoiceDrawer from '../components/Chat/InvoiceDrawer';

const DocumentScanner = () => {
    const navigate = useNavigate();
    const [dragActive, setDragActive] = useState(false);
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [analyzing, setAnalyzing] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [showDetails, setShowDetails] = useState(false);

    const handleDrag = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFile(e.dataTransfer.files[0]);
        }
    }, []);

    const handleChange = (e) => {
        e.preventDefault();
        if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0]);
        }
    };

    const handleFile = (selectedFile) => {
        // Validate file type
        const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf'];
        if (!allowedTypes.includes(selectedFile.type)) {
            setError('Please upload a PNG, JPG, or PDF file');
            return;
        }

        // Validate file size (max 10MB)
        if (selectedFile.size > 10 * 1024 * 1024) {
            setError('File size must be less than 10MB');
            return;
        }

        setFile(selectedFile);
        setError(null);

        // Create preview for images
        if (selectedFile.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onloadend = () => {
                setPreview(reader.result);
            };
            reader.readAsDataURL(selectedFile);
        }
    };

    const handleAnalyze = async () => {
        if (!file) return;

        setAnalyzing(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('http://localhost:8000/api/v1/invoices/analyze', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to analyze invoice');
            }

            const data = await response.json();
            setResult(data);
            setShowDetails(true);
        } catch (err) {
            setError(err.message || 'Failed to analyze invoice. Please try again.');
            console.error('Analysis error:', err);
        } finally {
            setAnalyzing(false);
        }
    };

    const handleReset = () => {
        setFile(null);
        setPreview(null);
        setResult(null);
        setError(null);
        setShowDetails(false);
    };

    return (
        <div className="min-h-screen bg-slate-50 p-6 lg:p-8">
            <div className="max-w-4xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900">Document Scanner</h1>
                        <p className="text-slate-500 mt-1">Upload invoices for AI-powered analysis</p>
                    </div>
                    <Button variant="outline" onClick={() => navigate('/history')}>
                        View History
                    </Button>
                </div>

                {/* Features */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <FeatureCard
                        icon={FileText}
                        title="Data Extraction"
                        description="Extract vendor, amounts, dates, and line items automatically"
                    />
                    <FeatureCard
                        icon={CheckCircle}
                        title="Fraud Detection"
                        description="Detect tampering, handwriting, and inconsistencies"
                    />
                    <FeatureCard
                        icon={AlertCircle}
                        title="Compliance Check"
                        description="Verify ITC eligibility and flag compliance issues"
                    />
                </div>

                {/* Upload Area */}
                <Card>
                    <CardContent className="p-8">
                        {!file ? (
                            <div
                                className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors ${dragActive
                                        ? 'border-primary-500 bg-primary-50'
                                        : 'border-slate-300 hover:border-primary-400 hover:bg-slate-50'
                                    }`}
                                onDragEnter={handleDrag}
                                onDragLeave={handleDrag}
                                onDragOver={handleDrag}
                                onDrop={handleDrop}
                            >
                                <Upload className="w-16 h-16 text-slate-400 mx-auto mb-4" />
                                <h3 className="text-lg font-semibold text-slate-900 mb-2">
                                    Drop your invoice here
                                </h3>
                                <p className="text-slate-500 mb-4">
                                    Supports PNG, JPG, and PDF (max 10MB)
                                </p>
                                <div className="flex items-center justify-center gap-4">
                                    <Button onClick={() => document.getElementById('file-upload')?.click()}>
                                        Browse Files
                                    </Button>
                                    <Button variant="outline">
                                        <Camera className="w-4 h-4 mr-2" />
                                        Take Photo
                                    </Button>
                                </div>
                                <input
                                    id="file-upload"
                                    type="file"
                                    accept="image/png,image/jpeg,image/jpg,application/pdf"
                                    onChange={handleChange}
                                    className="hidden"
                                />
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {/* File Preview */}
                                <div className="flex items-center gap-4 p-4 bg-slate-50 rounded-lg">
                                    {preview ? (
                                        <img src={preview} alt="Preview" className="w-20 h-20 object-cover rounded" />
                                    ) : (
                                        <div className="w-20 h-20 bg-slate-200 rounded flex items-center justify-center">
                                            <FileText className="w-10 h-10 text-slate-400" />
                                        </div>
                                    )}
                                    <div className="flex-1">
                                        <p className="font-medium text-slate-900">{file.name}</p>
                                        <p className="text-sm text-slate-500">
                                            {(file.size / 1024 / 1024).toFixed(2)} MB
                                        </p>
                                    </div>
                                    <Button variant="outline" size="sm" onClick={handleReset}>
                                        <XCircle className="w-4 h-4" />
                                    </Button>
                                </div>

                                {/* Analyze Button */}
                                <Button
                                    onClick={handleAnalyze}
                                    disabled={analyzing}
                                    className="w-full"
                                    size="lg"
                                >
                                    {analyzing ? (
                                        <>
                                            <Loader className="w-5 h-5 mr-2 animate-spin" />
                                            Analyzing Invoice...
                                        </>
                                    ) : (
                                        <>
                                            <FileText className="w-5 h-5 mr-2" />
                                            Analyze Invoice
                                        </>
                                    )}
                                </Button>
                            </div>
                        )}

                        {/* Error Message */}
                        {error && (
                            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                                <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                                <div>
                                    <p className="font-medium text-red-900">Error</p>
                                    <p className="text-sm text-red-700">{error}</p>
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Analysis Result */}
                {result && (
                    <Card>
                        <CardHeader>
                            <div className="flex items-center justify-between">
                                <h2 className="text-lg font-semibold text-slate-900">Analysis Results</h2>
                                <Badge variant={result.is_valid_business_expense ? 'success' : 'danger'}>
                                    {result.is_valid_business_expense ? 'Valid Business Expense' : 'Review Required'}
                                </Badge>
                            </div>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {/* Summary */}
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <SummaryItem label="Vendor" value={result.vendor_name} />
                                <SummaryItem label="Amount" value={`₹${result.total_amount.toLocaleString('en-IN')}`} />
                                <SummaryItem label="Tax" value={`₹${result.tax_amount.toLocaleString('en-IN')}`} />
                                <SummaryItem label="Confidence" value={`${(result.confidence_score * 100).toFixed(0)}%`} />
                            </div>

                            {/* Compliance Status */}
                            <div>
                                <h3 className="font-semibold text-slate-900 mb-2">Compliance Status</h3>
                                <div className="space-y-2">
                                    {result.compliance_flags && result.compliance_flags.length > 0 ? (
                                        result.compliance_flags.map((flag, index) => (
                                            <div key={index} className="flex items-center gap-2 text-sm text-red-700 bg-red-50 p-2 rounded">
                                                <AlertCircle className="w-4 h-4" />
                                                <span>{flag}</span>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 p-2 rounded">
                                            <CheckCircle className="w-4 h-4" />
                                            <span>No compliance issues detected</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Subsidy Alerts */}
                            {result.subsidy_alerts && result.subsidy_alerts.length > 0 && (
                                <div>
                                    <h3 className="font-semibold text-slate-900 mb-2">Subsidy Opportunities</h3>
                                    {result.subsidy_alerts.map((alert, index) => (
                                        <div key={index} className="flex items-center gap-2 text-sm text-green-700 bg-green-50 p-2 rounded mb-2">
                                            <CheckCircle className="w-4 h-4" />
                                            <span>{alert}</span>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Actions */}
                            <div className="flex gap-3 pt-4">
                                <Button onClick={() => setShowDetails(true)} className="flex-1">
                                    View Full Details
                                </Button>
                                <Button variant="outline" onClick={() => navigate('/compliance')}>
                                    Check Compliance
                                </Button>
                                <Button variant="outline" onClick={() => navigate('/subsidies')}>
                                    Explore Subsidies
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                )}
            </div>

            {/* Invoice Details Drawer */}
            {showDetails && result && (
                <InvoiceDrawer
                    invoice={result}
                    onClose={() => setShowDetails(false)}
                />
            )}
        </div>
    );
};

// Sub-components

const FeatureCard = ({ icon: Icon, title, description }) => (
    <div className="p-4 bg-white rounded-lg border border-slate-200">
        <Icon className="w-8 h-8 text-primary-600 mb-3" />
        <h3 className="font-semibold text-slate-900 mb-1">{title}</h3>
        <p className="text-sm text-slate-500">{description}</p>
    </div>
);

const SummaryItem = ({ label, value }) => (
    <div className="p-3 bg-slate-50 rounded-lg">
        <p className="text-xs text-slate-500 mb-1">{label}</p>
        <p className="font-semibold text-slate-900">{value}</p>
    </div>
);

export default DocumentScanner;
