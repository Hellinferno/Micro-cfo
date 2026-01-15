import React from 'react';
import { ArrowUpRight } from 'lucide-react';

const Subsidies = () => {
    const schemes = [
        { title: 'CLCSS for Technology Upgradation', benefit: '15% Capital Subsidy', maxLimit: '₹15 Lakhs', eligibility: 'Technological upgradation with approved machinery' },
        { title: 'PMEGP Scheme', benefit: 'Up to 35% Subsidy', maxLimit: '₹25 Lakhs', eligibility: 'New micro-enterprises in manufacturing sector' },
        { title: 'CGTMSE', benefit: 'Collateral Free Loans', maxLimit: '₹2 Crores', eligibility: 'MSEs without collateral security' },
    ];

    return (
        <div className="p-6 lg:p-10 space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-slate-800">Available Subsidies</h1>
                <p className="text-slate-500 text-sm">Government schemes tailored to your business profile.</p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {schemes.map((scheme, index) => (
                    <div key={index} className="bg-white rounded-xl p-6 shadow-sm border border-slate-200 hover:shadow-md transition-shadow group">
                        <div className="flex justify-between items-start mb-4">
                            <div className="bg-emerald-50 text-emerald-600 p-3 rounded-lg font-bold text-lg">
                                {scheme.benefit}
                            </div>
                            <button className="text-slate-400 group-hover:text-primary transition-colors">
                                <ArrowUpRight size={20} />
                            </button>
                        </div>
                        <h3 className="font-bold text-slate-800 text-lg mb-2">{scheme.title}</h3>
                        <p className="text-slate-500 text-sm mb-4 line-clamp-2">{scheme.eligibility}</p>

                        <div className="flex justify-between items-center pt-4 border-t border-slate-100">
                            <div className="text-xs text-slate-400">
                                Max Limit: <span className="font-medium text-slate-600">{scheme.maxLimit}</span>
                            </div>
                            <button className="text-sm font-medium text-emerald-600 hover:text-emerald-700">View Details</button>
                        </div>
                    </div>
                ))}
            </div>

            <div className="bg-indigo-50 rounded-xl p-6 border border-indigo-100 flex flex-col md:flex-row items-center justify-between">
                <div className="mb-4 md:mb-0">
                    <h3 className="font-bold text-indigo-900">Need Expert Guidance?</h3>
                    <p className="text-indigo-600 text-sm">Consult with our CA partners to secure your funding.</p>
                </div>
                <button className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-lg text-sm font-medium transition-colors">
                    Book Consultation
                </button>
            </div>
        </div>
    );
};

export default Subsidies;
