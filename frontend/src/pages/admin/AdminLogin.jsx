import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Eye, EyeOff, AlertCircle, Loader2 } from 'lucide-react';

const AdminLogin = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        username: '',
        password: ''
    });
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    // Hardcoded admin credentials (in production, verify against backend)
    const ADMIN_CREDENTIALS = {
        username: 'hellinferno',
        password: '8920680344'
    };

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
        setError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 800));

        if (formData.username === ADMIN_CREDENTIALS.username && 
            formData.password === ADMIN_CREDENTIALS.password) {
            // Store admin session
            localStorage.setItem('adminAuth', JSON.stringify({
                username: formData.username,
                role: 'admin',
                loginTime: new Date().toISOString()
            }));
            navigate('/admin/dashboard');
        } else {
            setError('Invalid username or password');
        }
        setLoading(false);
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4">
            {/* Background Pattern */}
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiMyMDI1MmIiIGZpbGwtb3BhY2l0eT0iMC40Ij48cGF0aCBkPSJNMzYgMzRoLTJ2LTRoMnY0em0wLTZ2LTRoLTJ2NGgyem0tNiA2aC00djJoNHYtMnptMC02djRoLTR2LTJoMnYtMmgyem0wLTZ2NGgtMnYyaC0ydi0yaC0ydjJoLTJ2LTJoMnYtMmgydi0yaDJ2MmgyeiIvPjwvZz48L2c+PC9zdmc+')] opacity-20"></div>
            
            <div className="relative bg-slate-800/50 backdrop-blur-xl rounded-2xl shadow-2xl w-full max-w-md p-8 border border-slate-700/50">
                {/* Logo */}
                <div className="flex justify-center mb-6">
                    <div className="bg-gradient-to-br from-amber-500 to-orange-600 p-4 rounded-2xl shadow-lg shadow-amber-500/20">
                        <Shield className="w-10 h-10 text-white" />
                    </div>
                </div>

                <div className="text-center mb-8">
                    <h1 className="text-2xl font-bold text-white">Admin Portal</h1>
                    <p className="text-slate-400 mt-2">Secure access to MicroCFO administration</p>
                </div>

                {error && (
                    <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3 text-red-400">
                        <AlertCircle size={20} />
                        <span className="text-sm">{error}</span>
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Username
                        </label>
                        <input
                            type="text"
                            name="username"
                            value={formData.username}
                            onChange={handleChange}
                            placeholder="Enter admin username"
                            className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600/50 rounded-xl text-white placeholder-slate-500 focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 outline-none transition-all"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Password
                        </label>
                        <div className="relative">
                            <input
                                type={showPassword ? 'text' : 'password'}
                                name="password"
                                value={formData.password}
                                onChange={handleChange}
                                placeholder="Enter admin password"
                                className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600/50 rounded-xl text-white placeholder-slate-500 focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 outline-none transition-all pr-12"
                                required
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition-colors"
                            >
                                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                            </button>
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white font-bold py-3.5 px-4 rounded-xl shadow-lg shadow-amber-500/30 transform active:scale-[0.98] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                        {loading ? (
                            <>
                                <Loader2 size={20} className="animate-spin" />
                                Authenticating...
                            </>
                        ) : (
                            <>
                                <Shield size={20} />
                                Access Admin Panel
                            </>
                        )}
                    </button>
                </form>

                <div className="mt-8 pt-6 border-t border-slate-700/50">
                    <p className="text-center text-sm text-slate-500">
                        🔒 This area is restricted to authorized personnel only.
                    </p>
                </div>

                {/* Back to main site */}
                <div className="mt-4 text-center">
                    <button 
                        onClick={() => navigate('/')}
                        className="text-slate-400 hover:text-white text-sm transition-colors"
                    >
                        ← Back to MicroCFO
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AdminLogin;
