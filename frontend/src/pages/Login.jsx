import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const Login = () => {
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [isRegisterMode, setIsRegisterMode] = useState(false);
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        full_name: '',
        company_name: '',
        phone_number: ''
    });

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
        setError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            const endpoint = isRegisterMode ? '/api/v1/auth/register' : '/api/v1/auth/login';

            // Prepare request data
            const requestData = isRegisterMode
                ? {
                    email: formData.email,
                    password: formData.password,
                    full_name: formData.full_name,
                    company_name: formData.company_name,
                    phone_number: formData.phone_number || undefined
                }
                : {
                    email: formData.email,
                    password: formData.password
                };

            const response = await api.post(endpoint, requestData);

            if (response.data.access_token) {
                // Store token in localStorage
                localStorage.setItem('token', response.data.access_token);

                // Store user info
                if (response.data.user) {
                    localStorage.setItem('user', JSON.stringify(response.data.user));
                }

                // Navigate to dashboard
                navigate('/');
            }
        } catch (err) {
            console.error('Authentication error:', err);
            const errorMessage = err.response?.data?.detail ||
                err.response?.data?.message ||
                'Authentication failed. Please try again.';
            setError(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    const toggleMode = () => {
        setIsRegisterMode(!isRegisterMode);
        setError('');
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
            <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-8 space-y-6">
                {/* Logo */}
                <div className="flex justify-center mb-2">
                    <div className="bg-primary/10 p-3 rounded-xl">
                        <svg className="w-10 h-10 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
                        </svg>
                    </div>
                </div>

                {/* Header */}
                <div className="text-center">
                    <h1 className="text-2xl font-bold text-slate-900">
                        {isRegisterMode ? 'Create Account' : 'Welcome Back'}
                    </h1>
                    <p className="text-slate-500 mt-2">
                        {isRegisterMode
                            ? 'Start your AI-powered financial compliance journey'
                            : 'Sign in to access your financial dashboard'}
                    </p>
                </div>

                {/* Error Message */}
                {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                        {error}
                    </div>
                )}

                {/* Form */}
                <form onSubmit={handleSubmit} className="space-y-4">
                    {isRegisterMode && (
                        <>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">
                                    Full Name
                                </label>
                                <input
                                    type="text"
                                    name="full_name"
                                    value={formData.full_name}
                                    onChange={handleInputChange}
                                    required
                                    className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all"
                                    placeholder="John Doe"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">
                                    Company Name
                                </label>
                                <input
                                    type="text"
                                    name="company_name"
                                    value={formData.company_name}
                                    onChange={handleInputChange}
                                    required
                                    className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all"
                                    placeholder="ABC Enterprises Pvt Ltd"
                                />
                            </div>
                        </>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                            Email
                        </label>
                        <input
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={handleInputChange}
                            required
                            className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all"
                            placeholder="you@example.com"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                            Password
                        </label>
                        <input
                            type="password"
                            name="password"
                            value={formData.password}
                            onChange={handleInputChange}
                            required
                            minLength={isRegisterMode ? 8 : 6}
                            className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all"
                            placeholder={isRegisterMode ? "Min. 8 characters" : "Enter your password"}
                        />
                        {isRegisterMode && (
                            <p className="text-xs text-slate-500 mt-1">
                                Must be at least 8 characters long
                            </p>
                        )}
                    </div>

                    {isRegisterMode && (
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">
                                Phone Number (Optional)
                            </label>
                            <input
                                type="tel"
                                name="phone_number"
                                value={formData.phone_number}
                                onChange={handleInputChange}
                                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all"
                                placeholder="+91 98765 43210"
                            />
                        </div>
                    )}

                    {!isRegisterMode && (
                        <div className="flex items-center justify-between">
                            <label className="flex items-center">
                                <input
                                    type="checkbox"
                                    className="w-4 h-4 text-primary border-slate-300 rounded focus:ring-primary"
                                />
                                <span className="ml-2 text-sm text-slate-600">Remember me</span>
                            </label>
                            <button
                                type="button"
                                className="text-sm text-primary hover:underline"
                                onClick={() => alert('Password reset feature coming soon!')}
                            >
                                Forgot password?
                            </button>
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full bg-primary hover:bg-primary-dark disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded-xl shadow-lg shadow-primary/30 transform active:scale-95 transition-all duration-200 flex items-center justify-center"
                    >
                        {isLoading ? (
                            <>
                                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                {isRegisterMode ? 'Creating Account...' : 'Signing In...'}
                            </>
                        ) : (
                            isRegisterMode ? 'Create Account' : 'Sign In'
                        )}
                    </button>
                </form>

                {/* Toggle Mode */}
                <div className="text-center">
                    <p className="text-sm text-slate-600">
                        {isRegisterMode ? 'Already have an account?' : "Don't have an account?"}{' '}
                        <button
                            type="button"
                            onClick={toggleMode}
                            className="text-primary font-semibold hover:underline"
                        >
                            {isRegisterMode ? 'Sign In' : 'Register'}
                        </button>
                    </p>
                </div>

                {/* Terms */}
                <p className="text-xs text-slate-400 text-center mt-6">
                    By continuing, you agree to our{' '}
                    <button
                        onClick={() => navigate('/terms')}
                        className="text-primary hover:underline"
                    >
                        Terms of Service
                    </button>{' '}
                    and{' '}
                    <button
                        onClick={() => navigate('/privacy')}
                        className="text-primary hover:underline"
                    >
                        Privacy Policy
                    </button>
                </p>
            </div>
        </div>
    );
};

export default Login;
