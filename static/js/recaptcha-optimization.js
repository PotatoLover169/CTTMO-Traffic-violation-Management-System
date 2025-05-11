/**
 * reCAPTCHA Optimization for Low Bandwidth - Traffic Violation System
 * 
 * This script provides optimizations for loading reCAPTCHA in low bandwidth environments
 * It uses various techniques to reduce the impact on page load time and user experience
 * 
 * Optimizations include:
 * 1. Connection speed detection and adaptive loading
 * 2. Preconnect hints to Google domains
 * 3. Session-based verification to reduce reCAPTCHA calls
 * 4. Low bandwidth mode with simplified UI
 */

(function() {
    // Configuration
    const OPTIMIZATION_CONFIG = {
        // Enable adaptive loading based on connection speed
        adaptiveLoading: true,
        // Threshold in Mbps for low bandwidth mode
        lowBandwidthThreshold: 0.5,
        // Enable session-based verification (remembers verified status)
        sessionBasedVerification: true,
        // Session verification expiry time in minutes
        sessionExpiryMinutes: 30,
        // Enable simplified UI for low bandwidth
        simplifiedLowBandwidthUI: true
    };
    
    // Storage for connection information
    let connectionInfo = {
        isLowBandwidth: false,
        speed: null,
        lastChecked: null
    };
    
    /**
     * Check the user's connection speed and set bandwidth mode
     * @returns {Promise} Resolves with connection info
     */
    function checkConnectionSpeed() {
        return new Promise(resolve => {
            // Try to use Network Information API if available
            if (navigator.connection) {
                const connection = navigator.connection;
                
                if (connection.downlink) {
                    connectionInfo.speed = connection.downlink; // Mbps
                    connectionInfo.isLowBandwidth = connection.downlink <= OPTIMIZATION_CONFIG.lowBandwidthThreshold;
                    connectionInfo.lastChecked = new Date().getTime();
                    
                    // Store in session storage
                    try {
                        sessionStorage.setItem('recaptcha_connection_info', JSON.stringify(connectionInfo));
                    } catch (e) {
                        console.warn('Session storage not available for reCAPTCHA optimization');
                    }
                    
                    return resolve(connectionInfo);
                }
                
                // Check connection type as fallback
                if (connection.type) {
                    connectionInfo.isLowBandwidth = 
                        connection.type === 'cellular' || 
                        connection.type === '2g' || 
                        connection.type === 'slow-2g';
                    
                    return resolve(connectionInfo);
                }
            }
            
            // Try to load from session storage if available
            try {
                const stored = sessionStorage.getItem('recaptcha_connection_info');
                if (stored) {
                    const parsed = JSON.parse(stored);
                    // Only use stored info if it's recent (within last 5 minutes)
                    if (parsed.lastChecked && new Date().getTime() - parsed.lastChecked < 5 * 60 * 1000) {
                        connectionInfo = parsed;
                        return resolve(connectionInfo);
                    }
                }
            } catch (e) {
                console.warn('Failed to read session storage for connection info');
            }
            
            // Default to assuming medium bandwidth if we can't detect
            connectionInfo.isLowBandwidth = false;
            resolve(connectionInfo);
        });
    }
    
    /**
     * Add preconnect hints to Google domains to speed up reCAPTCHA loading
     */
    function addPreconnectHints() {
        const googleDomains = [
            'https://www.google.com',
            'https://www.gstatic.com',
            'https://fonts.gstatic.com',
            'https://fonts.googleapis.com'
        ];
        
        googleDomains.forEach(domain => {
            const link = document.createElement('link');
            link.rel = 'preconnect';
            link.href = domain;
            link.crossOrigin = 'anonymous';
            document.head.appendChild(link);
        });
    }
    
    /**
     * Create and store a session token for verified users
     * This helps reduce the need to complete reCAPTCHA frequently
     * @param {string} formId - The ID of the form that was verified
     */
    function storeSessionVerification(formId) {
        if (!OPTIMIZATION_CONFIG.sessionBasedVerification) return;
        
        try {
            // Get or create session data
            let sessionData = {};
            const stored = sessionStorage.getItem('recaptcha_verification');
            if (stored) {
                sessionData = JSON.parse(stored);
            }
            
            // Add this form to verified forms
            sessionData[formId] = {
                timestamp: new Date().getTime(),
                expires: new Date().getTime() + (OPTIMIZATION_CONFIG.sessionExpiryMinutes * 60 * 1000)
            };
            
            // Store updated session data
            sessionStorage.setItem('recaptcha_verification', JSON.stringify(sessionData));
        } catch (e) {
            console.warn('Session storage not available for reCAPTCHA verification');
        }
    }
    
    /**
     * Check if a form has been verified in the current session
     * @param {string} formId - The ID of the form to check
     * @returns {boolean} True if the form has valid session verification
     */
    function hasSessionVerification(formId) {
        if (!OPTIMIZATION_CONFIG.sessionBasedVerification) return false;
        
        try {
            const stored = sessionStorage.getItem('recaptcha_verification');
            if (!stored) return false;
            
            const sessionData = JSON.parse(stored);
            const formData = sessionData[formId];
            
            if (!formData) return false;
            
            // Check if verification has expired
            const now = new Date().getTime();
            return formData.expires > now;
        } catch (e) {
            return false;
        }
    }
    
    /**
     * Apply optimization settings based on connection speed
     */
    function applyOptimizations() {
        // Always add preconnect hints
        addPreconnectHints();
        
        // Check connection speed and apply optimizations
        if (OPTIMIZATION_CONFIG.adaptiveLoading) {
            checkConnectionSpeed().then(info => {
                if (info.isLowBandwidth && OPTIMIZATION_CONFIG.simplifiedLowBandwidthUI) {
                    // Apply low bandwidth optimizations
                    document.documentElement.classList.add('recaptcha-low-bandwidth');
                    
                    // If reCAPTCHA handler is available, configure it for low bandwidth
                    if (window.RECAPTCHA_CONFIG) {
                        // Use compact size for reCAPTCHA
                        window.RECAPTCHA_CONFIG.size = 'compact';
                        
                        // Enable more generous fallback options
                        if (window.RECAPTCHA_CONFIG.fallbackSettings) {
                            window.RECAPTCHA_CONFIG.fallbackSettings.maxRetries = 2;
                            window.RECAPTCHA_CONFIG.fallbackSettings.timeout = 15000;
                        }
                    }
                }
            });
        }
        
        // If reCAPTCHA handler is available, extend it with our optimization functions
        if (window.ReCaptchaHandler) {
            // Store verification status in session when verified
            const originalCallbacks = window.reCAPTCHAState?.callbacks || {};
            if (window.reCAPTCHAState) {
                for (const formId in originalCallbacks) {
                    const originalCallback = originalCallbacks[formId];
                    window.reCAPTCHAState.callbacks[formId] = function(response) {
                        // Call original callback
                        if (originalCallback) {
                            originalCallback(response);
                        }
                        
                        // Store session verification
                        if (response) {
                            storeSessionVerification(formId);
                        }
                    };
                }
            }
            
            // Add session verification check to ReCaptchaHandler
            const originalHandleFormSubmit = window.handleFormSubmit;
            if (originalHandleFormSubmit) {
                window.handleFormSubmit = function(event) {
                    const form = event.target;
                    const formId = form.id || 'recaptcha-form-' + Math.random().toString(36).substring(2, 10);
                    
                    // Check for session verification
                    if (hasSessionVerification(formId)) {
                        // Add the form to verified forms
                        if (window.reCAPTCHAState) {
                            window.reCAPTCHAState.verifiedForms.add(formId);
                        }
                        return;
                    }
                    
                    // Call original handler
                    return originalHandleFormSubmit(event);
                };
            }
        }
    }
    
    // Apply optimizations when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyOptimizations);
    } else {
        applyOptimizations();
    }
    
    // Add styles for low bandwidth mode
    const style = document.createElement('style');
    style.innerHTML = `
        /* Low bandwidth optimizations */
        .recaptcha-low-bandwidth .recaptcha-container {
            transition: none !important;
        }
        
        .recaptcha-low-bandwidth .g-recaptcha {
            transform: scale(0.85);
            transform-origin: left top;
        }
        
        /* Hide animations and transitions in low bandwidth mode */
        .recaptcha-low-bandwidth .recaptcha-container > div {
            animation: none !important;
        }
        
        /* Simplified UI for low bandwidth */
        .recaptcha-low-bandwidth .recaptcha-placeholder {
            border: none;
            background: none;
        }
    `;
    document.head.appendChild(style);
    
    // Export public API
    window.RecaptchaOptimization = {
        checkConnectionSpeed: checkConnectionSpeed,
        isLowBandwidth: () => connectionInfo.isLowBandwidth,
        storeSessionVerification: storeSessionVerification,
        hasSessionVerification: hasSessionVerification
    };
})(); 