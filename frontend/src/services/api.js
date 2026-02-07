/**
 * API Service Layer for MicroCFO Frontend
 * Handles all communication with FastAPI backend
 */

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_V1_PREFIX = '/api/v1';

/**
 * Base fetch wrapper with error handling
 */
async function apiFetch(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;

    const defaultHeaders = {
        'Accept': 'application/json',
    };

    // Add Content-Type for JSON requests (not for FormData)
    if (options.body && !(options.body instanceof FormData)) {
        defaultHeaders['Content-Type'] = 'application/json';
    }

    // Get auth token from localStorage
    const token = localStorage.getItem('auth_token');
    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }

    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers,
        },
    };

    try {
        const response = await fetch(url, config);

        // Handle non-JSON responses
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return { success: true };
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || data.detail || `HTTP ${response.status}`);
        }

        return data;
    } catch (error) {
        console.error(`API Error [${endpoint}]:`, error);
        throw error;
    }
}

/**
 * Visual Auditor (Agent A) API
 */
export const visualAuditorAPI = {
    /**
     * Upload and scan invoice document
     * @param {File} file - The invoice file (PDF, PNG, JPG)
     * @param {boolean} processImmediately - Whether to process immediately
     * @returns {Promise<Object>} Upload response with invoice data
     */
    async uploadDocument(file, processImmediately = true) {
        const formData = new FormData();
        formData.append('file', file);

        return apiFetch(`${API_V1_PREFIX}/invoices/analyze`, {
            method: 'POST',
            body: formData,
        });
    },

    /**
     * Scan invoice with image URL or base64
     * @param {string} imageUrl - URL or base64 encoded image
     * @param {boolean} useMock - Use mock data for testing
     * @returns {Promise<Object>} Invoice scan results
     */
    async scanInvoice(imageUrl, useMock = false) {
        return apiFetch(`${API_V1_PREFIX}/invoices/analyze-url`, {
            method: 'POST',
            body: JSON.stringify({ image_url: imageUrl }),
        });
    },

    /**
     * Health check for Visual Auditor
     */
    async health() {
        return apiFetch('/health');
    },
};

/**
 * Legal Sentinel (Agent B) API
 */
export const legalSentinelAPI = {
    /**
     * Check legal compliance
     * @param {string} query - Legal query
     * @param {string} userContext - Optional user context
     * @returns {Promise<Object>} Compliance check results
     */
    async checkCompliance(query, userContext = null) {
        return apiFetch(`${API_V1_PREFIX}/compliance/query`, {
            method: 'POST',
            body: JSON.stringify({
                query,
                user_context: userContext || '',
            }),
        });
    },

    /**
     * Legacy: Search compliance (alias for checkCompliance)
     */
    async searchCompliance(query, userProfile = null) {
        return this.checkCompliance(query, userProfile ? JSON.stringify(userProfile) : null);
    },

    /**
     * Assess legal risk for invoice
     * @param {Object} invoiceData - Invoice data
     * @param {Object} userProfile - User business profile
     * @returns {Promise<Object>} Risk assessment
     */
    async assessRisk(invoiceData, userProfile = null) {
        return apiFetch(`${API_V1_PREFIX}/agents/legal-sentinel/assess-risk`, {
            method: 'POST',
            body: JSON.stringify({
                invoice_data: invoiceData,
                user_profile: userProfile,
            }),
        });
    },
};

/**
 * Subsidy Hunter (Agent C) API
 */
export const subsidyHunterAPI = {

    /**
     * Legacy: Search subsidies with text query (parses sector from query)
     */
    async searchSubsidies(query, userProfile = null) {
        // Robust keyword mapping to backend sectors
        const sectorKeywords = {
            'women_entrepreneur': ['women', 'woman', 'female', 'girl', 'lady', 'widow', 'housewife'],
            'rural_business': ['rural', 'village', 'panchayat', 'farm', 'agri', 'agriculture'], // Agri also maps here if specific rural business context
            'textile': ['textile', 'garment', 'apparel', 'fabric', 'yarn', 'spinning', 'weaving', 'clothing', 'knitwear'],
            'food_processing': ['food', 'dairy', 'milk', 'bakery', 'beverage', 'snack', 'meat', 'processing', 'cold chain', 'sugar'],
            'pharma': ['pharma', 'drug', 'medicine', 'medical', 'biotech', 'chemical'],
            'it': ['it', 'software', 'tech', 'computer', 'digital', 'saas', 'app', 'web', 'data'],
            'manufacturing': ['manufacturing', 'factory', 'plant', 'machinery', 'production', 'industrial', 'engineering'],
            'services': ['service', 'consulting', 'tourism', 'hotel', 'hospital', 'logistics', 'education', 'training'],
            'technology': ['hardware', 'electronic', 'device', 'gadget', 'semiconductor']
        };

        const lowerQuery = query.toLowerCase();
        let detectedSector = null;

        // Find best matching sector (prioritize top formatting)
        for (const [sector, keywords] of Object.entries(sectorKeywords)) {
            if (keywords.some(keyword => lowerQuery.includes(keyword))) {
                detectedSector = sector;
                break;
            }
        }

        // If no specific sector detected, use the relevant part of the query
        if (!detectedSector) {
            // Remove common words to find the core subject
            const commonWords = ['subsidy', 'subsidies', 'scheme', 'schemes', 'benefit', 'loan', 'grant', 'for', 'in', 'startup', 'business', 'start', 'i', 'want', 'need', 'give', 'me', 'help'];
            const words = lowerQuery.split(/\s+/).filter(w => !commonWords.includes(w) && w.length > 2);

            if (words.length > 0) {
                detectedSector = words.join(' ');
            } else {
                detectedSector = 'manufacturing'; // Detailed fallback if query is just "give me subsidy"
            }
        }


        // Extract state (Indian context)
        const states = [
            'maharashtra', 'gujarat', 'karnataka', 'tamil nadu', 'telangana', 'delhi',
            'uttar pradesh', 'haryana', 'rajasthan', 'madhya pradesh', 'punjab', 'west bengal',
            'bihar', 'odisha', 'andhra pradesh'
        ];

        let detectedState = null;
        for (const state of states) {
            if (lowerQuery.includes(state)) {
                detectedState = state;
                break;
            }
        }

        // Extract amount (supports "1 crore", "50 lakhs", "100000")
        let capexAmount = 1000000; // Default 10L

        // Try to parse natural language numbers
        const croreMatch = lowerQuery.match(/(\d+(?:\.\d+)?)\s*cr(?:ore)?s?/);
        const lakhMatch = lowerQuery.match(/(\d+(?:\.\d+)?)\s*lakh?s?/);

        if (croreMatch) {
            capexAmount = parseFloat(croreMatch[1]) * 10000000;
        } else if (lakhMatch) {
            capexAmount = parseFloat(lakhMatch[1]) * 100000;
        } else {
            // Fallback to raw numbers
            const numMatch = query.match(/(\d+(?:,\d{3})*(?:\.\d+)?)/);
            if (numMatch) {
                const val = parseFloat(numMatch[0].replace(/,/g, ''));
                // Simple heuristic: if user types "50000", they usually mean literal amount. 
                // If they type tiny number like "50", they might mean lakhs, but safer to assume literal if no unit specified.
                capexAmount = val;
            }
        }

        console.log(`[Frontend] Parsed Query: "${query}" -> Sector: ${detectedSector}, State: ${detectedState}, Amount: ${capexAmount}`);
        return this.findSubsidies(detectedSector, capexAmount, detectedState);
    },

    /**
     * Find subsidies for invoice
     * @param {Object} invoiceData - Invoice data
     * @param {Object} userProfile - User business profile
     * @returns {Promise<Object>} Matching subsidies
     */
    async findForInvoice(invoiceData, userProfile = null) {
        return apiFetch(`${API_V1_PREFIX}/agents/subsidy-hunter/find-for-invoice`, {
            method: 'POST',
            body: JSON.stringify({
                invoice_data: invoiceData,
                user_profile: userProfile,
            }),
        });
    },

    // --- Core Agent Methods ---

    /**
     * Find subsidies by sector and amount
     * @param {string} sector - Industry sector
     * @param {number} capexAmount - Investment amount
     * @param {string} state - State name (optional)
     */
    async findSubsidies(sector, capexAmount, state = null) {
        const body = {
            sector,
            capex_amount: capexAmount,
        };
        if (state) body.state = state;

        return apiFetch(`${API_V1_PREFIX}/subsidies/search`, {
            method: 'POST',
            body: JSON.stringify(body),
        });
    },
};

/**
 * Negotiator (Agent D) API
 */
export const negotiatorAPI = {
    /**
     * Generate negotiation email
     * @param {Object} invoiceData - Invoice data
     * @param {Object} negotiationContext - Negotiation context
     * @returns {Promise<Object>} Generated email
     */
    async generateEmail(invoiceData, negotiationContext) {
        return apiFetch(`${API_V1_PREFIX}/agents/negotiator/generate-email`, {
            method: 'POST',
            body: JSON.stringify({
                invoice_data: invoiceData,
                negotiation_context: negotiationContext,
            }),
        });
    },
};

/**
 * Async Task Management API
 */
export const tasksAPI = {
    /**
     * Submit invoice for async scanning
     * @param {File} file - Invoice file
     * @returns {Promise<Object>} Task submission response
     */
    async submitInvoiceScan(file) {
        const formData = new FormData();
        formData.append('file', file);

        return apiFetch('/api/tasks/invoice/scan', {
            method: 'POST',
            body: formData,
        });
    },

    /**
     * Submit legal search task
     * @param {string} query - Legal query
     * @param {Object} userProfile - User profile
     * @returns {Promise<Object>} Task submission response
     */
    async submitLegalSearch(query, userProfile = null) {
        return apiFetch('/api/tasks/legal/search', {
            method: 'POST',
            body: JSON.stringify({
                query,
                user_profile: userProfile,
            }),
        });
    },

    /**
     * Submit subsidy search task
     * @param {string} query - Subsidy query
     * @param {Object} userProfile - User profile
     * @returns {Promise<Object>} Task submission response
     */
    async submitSubsidySearch(query, userProfile = null) {
        return apiFetch('/api/tasks/subsidy/search', {
            method: 'POST',
            body: JSON.stringify({
                query,
                user_profile: userProfile,
            }),
        });
    },

    /**
     * Get task status
     * @param {string} taskId - Task ID
     * @returns {Promise<Object>} Task status
     */
    async getTaskStatus(taskId) {
        return apiFetch(`/api/tasks/status/${taskId}`);
    },

    /**
     * Get task result
     * @param {string} taskId - Task ID
     * @returns {Promise<Object>} Task result
     */
    async getTaskResult(taskId) {
        return apiFetch(`/api/tasks/result/${taskId}`);
    },

    /**
     * Cancel task
     * @param {string} taskId - Task ID
     * @returns {Promise<Object>} Cancellation response
     */
    async cancelTask(taskId) {
        return apiFetch(`/api/tasks/cancel/${taskId}`, {
            method: 'DELETE',
        });
    },

    /**
     * Poll task until completion
     * @param {string} taskId - Task ID
     * @param {Function} onProgress - Progress callback
     * @param {number} pollInterval - Polling interval in ms
     * @returns {Promise<Object>} Final task result
     */
    async pollTask(taskId, onProgress = null, pollInterval = 2000) {
        return new Promise((resolve, reject) => {
            const poll = async () => {
                try {
                    const status = await this.getTaskStatus(taskId);

                    // Call progress callback
                    if (onProgress) {
                        onProgress(status);
                    }

                    // Check if task is complete
                    if (status.status === 'success') {
                        resolve(status.result);
                    } else if (status.status === 'failed') {
                        reject(new Error(status.error || 'Task failed'));
                    } else {
                        // Continue polling
                        setTimeout(poll, pollInterval);
                    }
                } catch (error) {
                    reject(error);
                }
            };

            poll();
        });
    },
};

/**
 * Authentication API
 */
export const authAPI = {
    /**
     * Login user
     * @param {string} username - Username
     * @param {string} password - Password
     * @returns {Promise<Object>} Login response with token
     */
    async login(username, password) {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const response = await apiFetch(`${API_V1_PREFIX}/auth/login`, {
            method: 'POST',
            body: formData,
        });

        // Store token
        if (response.access_token) {
            localStorage.setItem('auth_token', response.access_token);
        }

        return response;
    },

    /**
     * Register new user
     * @param {Object} userData - User registration data
     * @returns {Promise<Object>} Registration response
     */
    async register(userData) {
        return apiFetch(`${API_V1_PREFIX}/auth/register`, {
            method: 'POST',
            body: JSON.stringify(userData),
        });
    },

    /**
     * Logout user
     */
    logout() {
        localStorage.removeItem('auth_token');
    },

    /**
     * Get current user
     * @returns {Promise<Object>} User data
     */
    async getCurrentUser() {
        return apiFetch(`${API_V1_PREFIX}/auth/me`);
    },
};

/**
 * WebSocket Connection Manager
 */
export class WebSocketManager {
    constructor() {
        this.ws = null;
        this.listeners = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
    }

    /**
     * Connect to WebSocket
     * @param {string} userId - User ID
     */
    connect(userId) {
        const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/ws/${userId}`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.emit('connected');
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.emit('message', data);

                // Emit specific event types
                if (data.type) {
                    this.emit(data.type, data);
                }
            } catch (error) {
                console.error('WebSocket message parse error:', error);
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.emit('error', error);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.emit('disconnected');

            // Attempt reconnection
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                setTimeout(() => {
                    console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
                    this.connect(userId);
                }, this.reconnectDelay * this.reconnectAttempts);
            }
        };
    }

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    /**
     * Send message
     * @param {Object} data - Message data
     */
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket not connected');
        }
    }

    /**
     * Add event listener
     * @param {string} event - Event name
     * @param {Function} callback - Callback function
     */
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    /**
     * Remove event listener
     * @param {string} event - Event name
     * @param {Function} callback - Callback function
     */
    off(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    /**
     * Emit event to listeners
     * @param {string} event - Event name
     * @param {*} data - Event data
     */
    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in ${event} listener:`, error);
                }
            });
        }
    }
}

/**
 * Admin API
 */
export const adminAPI = {
    /**
     * Get admin dashboard overview
     * @returns {Promise<Object>} Dashboard statistics
     */
    async getOverview() {
        return apiFetch(`${API_V1_PREFIX}/admin/overview`);
    },

    /**
     * Get all users
     * @returns {Promise<Array>} List of users
     */
    async getUsers() {
        return apiFetch(`${API_V1_PREFIX}/admin/users`);
    },

    /**
     * Get audit logs
     * @param {Object} filters - Filter parameters
     * @returns {Promise<Array>} Audit logs
     */
    async getAuditLogs(filters = {}) {
        const params = new URLSearchParams(filters);
        return apiFetch(`${API_V1_PREFIX}/admin/audit-logs?${params}`);
    },

    /**
     * Get system metrics
     * @returns {Promise<Object>} System metrics
     */
    async getMetrics() {
        return apiFetch(`${API_V1_PREFIX}/admin/metrics`);
    },
};

/**
 * Health Check API
 */
export const healthAPI = {
    /**
     * Check server health
     * @returns {Promise<Object>} Health status
     */
    async check() {
        return apiFetch('/health');
    },

    /**
     * Check API v1 status
     * @returns {Promise<Object>} API status
     */
    async apiStatus() {
        return apiFetch(`${API_V1_PREFIX}/status`);
    },
};

// Export apiFetch for direct use
export { apiFetch };

// Export default API object
export default {
    visualAuditor: visualAuditorAPI,
    legalSentinel: legalSentinelAPI,
    subsidyHunter: subsidyHunterAPI,
    negotiator: negotiatorAPI,
    tasks: tasksAPI,
    auth: authAPI,
    admin: adminAPI,
    health: healthAPI,
    WebSocketManager,
};
