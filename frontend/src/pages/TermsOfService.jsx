import React from 'react';

const TermsOfService = () => {
    return (
        <div className="max-w-4xl mx-auto p-8 bg-white shadow-sm mt-10 mb-10 prose">
            <h1>Terms of Service</h1>
            <p className="text-gray-500">Last Updated: January 2026</p>

            <h2>1. Acceptance of Terms</h2>
            <p>By accessing and using MicroCFO ("the Service"), you agree to be bound by these Terms. If you do not agree, do not use the Service.</p>

            <h2>2. Nature of Service (AI Disclaimer)</h2>
            <p>MicroCFO is an Artificial Intelligence-based tool designed to assist with financial operations. <strong>It is NOT a Chartered Accountant, Lawyer, or Financial Advisor.</strong></p>
            <ul>
                <li>Outputs are generated based on patterns and data provided.</li>
                <li>You must verify all invoices, legal summaries, and negotiation drafts independently.</li>
                <li>We are not liable for tax penalties, legal disputes, or financial losses resulting from reliance on the Service.</li>
            </ul>

            <h2>3. Data Privacy & Encryption</h2>
            <p>We take your financial data security seriously. All sensitive data (invoices, GST numbers) is encrypted at rest using AES-256 encryption. However, no method of transmission over the internet is 100% secure.</p>

            <h2>4. User Responsibilities</h2>
            <p>You agree not to:</p>
            <ul>
                <li>Upload illegal or fraudulent documents.</li>
                <li>Reverse engineer the AI models.</li>
                <li>Use the service to harass vendors (via the Negotiation agent).</li>
            </ul>

            <h2>5. Governing Law</h2>
            <p>These terms are governed by the laws of India. Any disputes are subject to the exclusive jurisdiction of the courts in [Your City], India.</p>
        </div>
    );
};

export default TermsOfService;
