/**
 * API Service
 * Centralized API client with authentication
 */

import axios from 'axios';

// Create axios instance
const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Request interceptor - Add auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor - Handle errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Token expired or invalid
            localStorage.removeItem('token');
            window.location.href = '/login';
        }

        if (error.response?.status === 403) {
            // Access denied
            console.error('Access denied');
        }

        if (error.response?.status === 500) {
            // Server error
            console.error('Server error:', error.response.data);
        }

        return Promise.reject(error);
    }
);

// API methods
export const apiService = {
    // Health check
    health: () => api.get('/api/v1/health'),

    // Chat
    chat: {
        sendMessage: (message, agent = 'auto', context = []) =>
            api.post('/api/v1/chat/message', { message, agent, context }),
        getConversation: (id) => api.get(`/api/v1/chat/conversation/${id}`),
        listConversations: (params) => api.get('/api/v1/chat/conversations', { params }),
        deleteConversation: (id) => api.delete(`/api/v1/chat/conversation/${id}`),
        clearConversation: () => api.post('/api/v1/chat/clear'),
        getAgents: () => api.get('/api/v1/chat/agents')
    },

    // Invoices
    invoices: {
        analyze: (file) => {
            const formData = new FormData();
            formData.append('file', file);
            return api.post('/api/v1/invoices/analyze', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
        },
        analyzeUrl: (imageUrl) => api.post('/api/v1/invoices/analyze-url', { image_url: imageUrl }),
        analyzeBase64: (imageData, contentType) =>
            api.post('/api/v1/invoices/analyze-base64', null, {
                params: { image_data: imageData, content_type: contentType }
            }),
        get: (id) => api.get(`/api/v1/invoices/${id}`),
        list: (params) => api.get('/api/v1/invoices', { params })
    },

    // Compliance
    compliance: {
        query: (query, userContext) =>
            api.post('/api/v1/compliance/query', { query, user_context: userContext }),
        searchSections: (query, act, limit) =>
            api.get('/api/v1/compliance/sections', { params: { query, act, limit } }),
        getHistory: (params) => api.get('/api/v1/compliance/history', { params }),
        subscribeToMonitoring: (sectors, acts) =>
            api.post('/api/v1/compliance/monitor/subscribe', { sectors, acts })
    },

    // Subsidies
    subsidies: {
        search: (params) => api.post('/api/v1/subsidies/search', params),
        getScheme: (id) => api.get(`/api/v1/subsidies/scheme/${id}`),
        getCategories: () => api.get('/api/v1/subsidies/categories'),
        getRecent: (limit) => api.get('/api/v1/subsidies/recent', { params: { limit } }),
        refresh: () => api.post('/api/v1/subsidies/refresh')
    },

    // Negotiation
    negotiation: {
        generate: (data) => api.post('/api/v1/negotiation/generate', data),
        analyzeIntent: (params) => api.post('/api/v1/negotiation/analyze-intent', params),
        getTemplates: () => api.get('/api/v1/negotiation/templates'),
        getHistory: (params) => api.get('/api/v1/negotiation/history', { params })
    }
};

export default api;
