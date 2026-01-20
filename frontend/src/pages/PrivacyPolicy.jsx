import React from 'react';

const PrivacyPolicy = () => {
    return (
        <div className="max-w-4xl mx-auto p-8 bg-white shadow-sm mt-10 mb-10 prose">
            <h1>Privacy Policy</h1>
            <p className="text-gray-500">Last Updated: January 2026</p>

            <h2>1. Information We Collect</h2>
            <ul>
                <li><strong>Personal Information:</strong> Name, Email, Phone Number.</li>
                <li><strong>Business Information:</strong> GSTIN, Company Name, Turnover Tier.</li>
                <li><strong>Financial Data:</strong> Invoices, Vendor Lists, Bank Statements (uploaded by you).</li>
            </ul>

            <h2>2. How We Use Your Data</h2>
            <p>We use your data strictly to:</p>
            <ul>
                <li>Provide AI analysis (e.g., Invoice OCR, Legal Compliance checks).</li>
                <li>Improve our AI models (anonymized data only).</li>
                <li>Comply with Indian legal obligations.</li>
            </ul>

            <h2>3. Data Storage</h2>
            <p>Your data is stored on secure servers located within India (AWS Mumbai Region), complying with the Digital Personal Data Protection Act, 2023 (DPDP Act).</p>

            <h2>4. Third-Party Sharing</h2>
            <p>We do not sell your data. We share data only with:</p>
            <ul>
                <li><strong>AI Providers:</strong> Google (Gemini) / OpenAI for processing (data is transient).</li>
                <li><strong>Cloud Providers:</strong> AWS for encrypted storage.</li>
            </ul>

            <h2>5. Your Rights</h2>
            <p>You may request deletion of your data at any time by contacting admin@microcfo.com.</p>
        </div>
    );
};

export default PrivacyPolicy;
