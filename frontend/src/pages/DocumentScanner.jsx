import React, { useState, useRef, useCallback } from 'react';
import { 
    Upload, 
    Camera, 
    FileText, 
    X, 
    CheckCircle, 
    AlertTriangle, 
    XCircle,
    Loader2,
    FileCheck,
    Edit3,
    MessageSquare,
    Download
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Modal, Progress } from '../components/ui';

const DocumentScanner = () => {
    const [dragActive, setDragActive] = useState(false);
    const [files, setFiles] = useState([]);
    const [processing, setProcessing] = useState(false);
    const [processingProgress, setProcessingProgress] = useState(0);
    const [currentResult, setCurrentResult] = useState(null);
    const [showResultModal, setShowResultModal] = useState(false);
    const [recentAudits, setRecentAudits] = useState([
        {
            id: 1,
            fileName: 'Invoice_ABC_Corp_001.pdf',
            vendor: 'ABC Corp',
            amount: 45000,
            date: '2024-01-15',
            status: 'compliant',
            gstNumber: '29AABCU9603R1ZM',
        },
        {
            id: 2,
            fileName: 'Bill_XYZ_Ltd_055.jpg',
            vendor: 'XYZ Ltd',
            amount: 78500,
            date: '2024-01-14',
            status: 'warning',
            gstNumber: '27AAACX0417E1Z3',
            flags: ['Amount mismatch detected'],
        },
        {
            id: 3,
            fileName: 'Receipt_DEF_Inc_012.png',
            vendor: 'DEF Inc',
            amount: 12300,
            date: '2024-01-13',
            status: 'non-compliant',
            gstNumber: 'Invalid',
            flags: ['Invalid GST number', 'Missing date'],
        },
    ]);

    const fileInputRef = useRef(null);
    const cameraInputRef = useRef(null);

    const handleDrag = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFiles(e.dataTransfer.files);
        }
    }, []);

    const handleFiles = (fileList) => {
        const newFiles = Array.from(fileList).filter(file => {
            const validTypes = ['image/jpeg', 'image/png', 'application/pdf'];
            const maxSize = 10 * 1024 * 1024; // 10MB
            return validTypes.includes(file.type) && file.size <= maxSize;
        });

        setFiles(prev => [...prev, ...newFiles.map(file => ({
            file,
            id: Date.now() + Math.random(),
            preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : null,
            status: 'pending'
        }))]);
    };

    const removeFile = (id) => {
        setFiles(prev => prev.filter(f => f.id !== id));
    };

    const processDocuments = async () => {
        setProcessing(true);
        setProcessingProgress(0);

        // Simulate processing
        for (let i = 0; i <= 100; i += 10) {
            await new Promise(resolve => setTimeout(resolve, 300));
            setProcessingProgress(i);
        }

        // Mock result
        const mockResult = {
            fileName: files[0]?.file?.name || 'Document.pdf',
            vendor: 'Tech Solutions Pvt Ltd',
            amount: 87500,
            taxAmount: 15750,
            invoiceDate: '2024-01-20',
            invoiceNumber: 'INV-2024-0125',
            gstNumber: '29AABCU9603R1ZM',
            lineItems: [
                { description: 'Software License', quantity: 5, rate: 15000, amount: 75000 },
                { description: 'Support Services', quantity: 1, rate: 12500, amount: 12500 },
            ],
            status: 'compliant',
            complianceFlags: [],
            aiSummary: 'This invoice appears to be compliant with GST regulations. All required fields are present and the calculations are correct.',
        };

        setCurrentResult(mockResult);
        setShowResultModal(true);
        setProcessing(false);
        setProcessingProgress(0);

        // Add to recent audits
        setRecentAudits(prev => [{
            id: Date.now(),
            fileName: mockResult.fileName,
            vendor: mockResult.vendor,
            amount: mockResult.amount,
            date: mockResult.invoiceDate,
            status: mockResult.status,
            gstNumber: mockResult.gstNumber,
        }, ...prev.slice(0, 4)]);

        // Clear files
        setFiles([]);
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'compliant':
                return <CheckCircle className="w-5 h-5 text-emerald-500" />;
            case 'warning':
                return <AlertTriangle className="w-5 h-5 text-amber-500" />;
            case 'non-compliant':
                return <XCircle className="w-5 h-5 text-red-500" />;
            default:
                return null;
        }
    };

    const getStatusBadge = (status) => {
        switch (status) {
            case 'compliant':
                return <Badge variant="success">Compliant</Badge>;
            case 'warning':
                return <Badge variant="warning">Warning</Badge>;
            case 'non-compliant':
                return <Badge variant="danger">Non-Compliant</Badge>;
            default:
                return <Badge>Pending</Badge>;
        }
    };

    return (
        <div className="p-4 lg:p-8 space-y-6 bg-slate-50 min-h-screen">
            {/* Page Header */}
            <div>
                <h1 className="text-2xl lg:text-3xl font-bold text-slate-800">Document Scanner</h1>
                <p className="text-slate-500 mt-1">Upload invoices and bills for AI-powered compliance audit</p>
            </div>

            <div className="grid lg:grid-cols-3 gap-6">
                {/* Upload Section */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Drop Zone */}
                    <Card>
                        <CardContent className="p-0">
                            <div
                                className={`relative p-8 border-2 border-dashed rounded-xl transition-all ${
                                    dragActive 
                                        ? 'border-primary bg-primary/5' 
                                        : 'border-slate-300 hover:border-primary/50'
                                }`}
                                onDragEnter={handleDrag}
                                onDragLeave={handleDrag}
                                onDragOver={handleDrag}
                                onDrop={handleDrop}
                            >
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".jpg,.jpeg,.png,.pdf"
                                    multiple
                                    onChange={(e) => handleFiles(e.target.files)}
                                    className="hidden"
                                />
                                <input
                                    ref={cameraInputRef}
                                    type="file"
                                    accept="image/*"
                                    capture="environment"
                                    onChange={(e) => handleFiles(e.target.files)}
                                    className="hidden"
                                />

                                <div className="text-center">
                                    <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                                        <Upload className="w-8 h-8 text-primary" />
                                    </div>
                                    <h3 className="text-lg font-semibold text-slate-800 mb-2">
                                        Drop your documents here
                                    </h3>
                                    <p className="text-slate-500 mb-6">
                                        or choose an option below to upload
                                    </p>

                                    <div className="flex flex-col sm:flex-row gap-3 justify-center">
                                        <Button 
                                            onClick={() => fileInputRef.current?.click()}
                                            icon={FileText}
                                        >
                                            Browse Files
                                        </Button>
                                        <Button 
                                            variant="outline"
                                            onClick={() => cameraInputRef.current?.click()}
                                            icon={Camera}
                                        >
                                            Take Photo
                                        </Button>
                                    </div>

                                    <p className="text-xs text-slate-400 mt-4">
                                        Supported formats: JPG, PNG, PDF (max 10MB)
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* File Preview */}
                    {files.length > 0 && (
                        <Card>
                            <CardHeader>
                                <CardTitle>Selected Documents ({files.length})</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-3">
                                    {files.map((item) => (
                                        <div 
                                            key={item.id}
                                            className="flex items-center gap-4 p-3 bg-slate-50 rounded-lg"
                                        >
                                            {item.preview ? (
                                                <img 
                                                    src={item.preview} 
                                                    alt="Preview"
                                                    className="w-16 h-16 object-cover rounded-lg"
                                                />
                                            ) : (
                                                <div className="w-16 h-16 bg-slate-200 rounded-lg flex items-center justify-center">
                                                    <FileText className="w-8 h-8 text-slate-400" />
                                                </div>
                                            )}
                                            <div className="flex-1 min-w-0">
                                                <p className="font-medium text-slate-800 truncate">
                                                    {item.file.name}
                                                </p>
                                                <p className="text-sm text-slate-500">
                                                    {(item.file.size / 1024).toFixed(1)} KB
                                                </p>
                                            </div>
                                            <button
                                                onClick={() => removeFile(item.id)}
                                                className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
                                            >
                                                <X className="w-5 h-5 text-slate-400" />
                                            </button>
                                        </div>
                                    ))}
                                </div>

                                <div className="mt-4 pt-4 border-t border-slate-100">
                                    <Button 
                                        className="w-full"
                                        onClick={processDocuments}
                                        disabled={processing}
                                        loading={processing}
                                    >
                                        {processing ? 'Processing...' : 'Start Audit'}
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* Processing Modal */}
                    {processing && (
                        <Card>
                            <CardContent className="py-8">
                                <div className="text-center">
                                    <Loader2 className="w-12 h-12 text-primary mx-auto mb-4 animate-spin" />
                                    <h3 className="text-lg font-semibold text-slate-800 mb-2">
                                        Visual Auditor is analyzing...
                                    </h3>
                                    <p className="text-slate-500 mb-6">
                                        Extracting data and checking compliance
                                    </p>
                                    <Progress value={processingProgress} className="max-w-xs mx-auto" />
                                    <p className="text-sm text-slate-400 mt-2">{processingProgress}%</p>
                                </div>
                            </CardContent>
                        </Card>
                    )}
                </div>

                {/* Recent Audits */}
                <div className="space-y-6">
                    <Card>
                        <CardHeader>
                            <CardTitle>Recent Audits</CardTitle>
                        </CardHeader>
                        <CardContent className="p-0">
                            <div className="divide-y divide-slate-100">
                                {recentAudits.map((audit) => (
                                    <div 
                                        key={audit.id}
                                        className="p-4 hover:bg-slate-50 transition-colors cursor-pointer"
                                    >
                                        <div className="flex items-start gap-3">
                                            {getStatusIcon(audit.status)}
                                            <div className="flex-1 min-w-0">
                                                <p className="font-medium text-slate-800 truncate text-sm">
                                                    {audit.vendor}
                                                </p>
                                                <p className="text-xs text-slate-500 truncate">
                                                    {audit.fileName}
                                                </p>
                                                <div className="flex items-center gap-2 mt-2">
                                                    <span className="text-sm font-semibold text-slate-800">
                                                        ₹{audit.amount.toLocaleString()}
                                                    </span>
                                                    {getStatusBadge(audit.status)}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Telegram Integration */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Telegram Integration</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-center">
                                <div className="w-32 h-32 bg-slate-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                                    <MessageSquare className="w-12 h-12 text-slate-400" />
                                </div>
                                <p className="text-sm text-slate-500 mb-4">
                                    Connect Telegram to receive audit alerts and upload documents on the go
                                </p>
                                <Button variant="outline" className="w-full">
                                    Connect Telegram
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* Result Modal */}
            <Modal
                isOpen={showResultModal}
                onClose={() => setShowResultModal(false)}
                title="Audit Result"
                description={currentResult?.fileName}
                size="lg"
            >
                {currentResult && (
                    <div className="space-y-6">
                        {/* Status Banner */}
                        <div className={`p-4 rounded-xl ${
                            currentResult.status === 'compliant' 
                                ? 'bg-emerald-50 border border-emerald-200' 
                                : currentResult.status === 'warning'
                                ? 'bg-amber-50 border border-amber-200'
                                : 'bg-red-50 border border-red-200'
                        }`}>
                            <div className="flex items-center gap-3">
                                {getStatusIcon(currentResult.status)}
                                <div>
                                    <p className={`font-semibold ${
                                        currentResult.status === 'compliant' 
                                            ? 'text-emerald-800' 
                                            : currentResult.status === 'warning'
                                            ? 'text-amber-800'
                                            : 'text-red-800'
                                    }`}>
                                        {currentResult.status === 'compliant' 
                                            ? '✅ Document is Compliant' 
                                            : currentResult.status === 'warning'
                                            ? '⚠️ Review Required'
                                            : '❌ Non-Compliant'}
                                    </p>
                                    <p className="text-sm text-slate-600 mt-1">
                                        {currentResult.aiSummary}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Extracted Data */}
                        <div className="grid md:grid-cols-2 gap-4">
                            <div className="space-y-3">
                                <div>
                                    <p className="text-xs text-slate-500">Vendor Name</p>
                                    <p className="font-medium text-slate-800">{currentResult.vendor}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-slate-500">Invoice Number</p>
                                    <p className="font-medium text-slate-800">{currentResult.invoiceNumber}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-slate-500">Invoice Date</p>
                                    <p className="font-medium text-slate-800">{currentResult.invoiceDate}</p>
                                </div>
                            </div>
                            <div className="space-y-3">
                                <div>
                                    <p className="text-xs text-slate-500">GST Number</p>
                                    <p className="font-medium text-slate-800">{currentResult.gstNumber}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-slate-500">Total Amount</p>
                                    <p className="font-medium text-slate-800">₹{currentResult.amount.toLocaleString()}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-slate-500">Tax Amount</p>
                                    <p className="font-medium text-slate-800">₹{currentResult.taxAmount.toLocaleString()}</p>
                                </div>
                            </div>
                        </div>

                        {/* Line Items */}
                        <div>
                            <h4 className="font-medium text-slate-800 mb-3">Line Items</h4>
                            <div className="border border-slate-200 rounded-lg overflow-hidden">
                                <table className="w-full text-sm">
                                    <thead className="bg-slate-50">
                                        <tr>
                                            <th className="px-4 py-2 text-left text-slate-600">Description</th>
                                            <th className="px-4 py-2 text-right text-slate-600">Qty</th>
                                            <th className="px-4 py-2 text-right text-slate-600">Rate</th>
                                            <th className="px-4 py-2 text-right text-slate-600">Amount</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {currentResult.lineItems.map((item, index) => (
                                            <tr key={index} className="border-t border-slate-100">
                                                <td className="px-4 py-2 text-slate-800">{item.description}</td>
                                                <td className="px-4 py-2 text-right text-slate-600">{item.quantity}</td>
                                                <td className="px-4 py-2 text-right text-slate-600">₹{item.rate.toLocaleString()}</td>
                                                <td className="px-4 py-2 text-right font-medium text-slate-800">₹{item.amount.toLocaleString()}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-slate-100">
                            <Button icon={Edit3} variant="outline" className="flex-1">
                                Edit Data
                            </Button>
                            <Button icon={Download} variant="outline" className="flex-1">
                                Download Report
                            </Button>
                            <Button icon={FileCheck} className="flex-1">
                                Save to Ledger
                            </Button>
                        </div>
                    </div>
                )}
            </Modal>
        </div>
    );
};

export default DocumentScanner;
