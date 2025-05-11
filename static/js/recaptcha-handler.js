/**
 * reCAPTCHA Handler for Traffic Violation System
 * 
 * Provides functionality for integrating Google reCAPTCHA v2 with forms
 * without modifying server-side views.
 * 
 * Optimized for low bandwidth environments.
 */

// Configuration
const RECAPTCHA_CONFIG = {
    // Get site key from meta tag with no fallback - we want to fail clearly if not set
    siteKey: document.querySelector('meta[name="recaptcha-site-key"]')?.content || '',
    theme: 'light',
    size: 'normal',
    // Forms to protect with reCAPTCHA (selector patterns)
    protectedForms: [
        // Authentication forms
        'form.auth-form',
        'form#registrationForm',
        'form[action*="password_reset"]',
        'form[action*="password_change"]',
        'form[action*="verification"]',
        // Other sensitive forms
        'form.sensitive-form',
        'form[data-protected="true"]'
    ],
    loadingText: 'Loading security verification...',
    errorMessages: {
        notVerified: 'Please complete the reCAPTCHA verification.',
        networkError: 'Network error. Please try again.',
        alreadyVerified: 'Already verified.'
    },
    // Fallback settings
    fallbackSettings: {
        maxRetries: 3,           // Number of load attempts before showing fallback
        timeout: 10000,          // Timeout in ms before showing fallback (10 seconds)
        enableFallback: true,    // Whether to allow fallback (form submission without reCAPTCHA)
        fallbackMessage: 'Security verification could not be loaded. You may continue without it.',
        fallbackWarning: 'Warning: Continuing without verification increases vulnerability to automated submissions.'
    },
    domainConfig: {
        currentDomain: window.location.hostname,
        allowedDomains: ['localhost', '127.0.0.1', 'onrender.com']
    }
};

// Global state
const reCAPTCHAState = {
    isLoaded: false,
    isLoading: false,
    verifiedForms: new Set(),
    callbacks: {},
    initialized: false,
    loadAttempts: 0,
    fallbackActivated: new Set(),
    domainValidated: false
};

/**
 * Dynamically load the Google reCAPTCHA script
 * Only loads once regardless of how many times it's called
 */
function loadReCaptchaScript() {
    if (reCAPTCHAState.isLoaded || reCAPTCHAState.isLoading) {
        return Promise.resolve();
    }
    
    reCAPTCHAState.isLoading = true;
    reCAPTCHAState.loadAttempts++;
    
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'https://www.google.com/recaptcha/api.js?onload=onReCaptchaLoaded&render=explicit';
        script.async = true;
        script.defer = true;
        
        // Set timeout for script loading
        const timeoutId = setTimeout(() => {
            if (!reCAPTCHAState.isLoaded) {
                reCAPTCHAState.isLoading = false;
                reject(new Error('reCAPTCHA script load timeout'));
            }
        }, RECAPTCHA_CONFIG.fallbackSettings.timeout);
        
        script.onload = () => {
            clearTimeout(timeoutId);
            resolve();
        };
        
        script.onerror = () => {
            clearTimeout(timeoutId);
            reCAPTCHAState.isLoading = false;
            reject(new Error('Failed to load reCAPTCHA script'));
        };
        
        document.head.appendChild(script);
    });
}

/**
 * Callback when Google reCAPTCHA API is loaded
 * This is called automatically by the Google reCAPTCHA API
 */
window.onReCaptchaLoaded = function() {
    reCAPTCHAState.isLoaded = true;
    reCAPTCHAState.isLoading = false;
    
    // Initialize reCAPTCHA on forms if they're already in the DOM
    if (!reCAPTCHAState.initialized) {
        initializeReCaptcha();
    }
};

/**
 * Find all protected forms and add reCAPTCHA to them
 */
function initializeReCaptcha() {
    if (reCAPTCHAState.initialized) return;
    
    // Find all forms that need protection
    const forms = findProtectedForms();
    
    // Add reCAPTCHA to each form
    forms.forEach(addReCaptchaToForm);
    
    reCAPTCHAState.initialized = true;
}

/**
 * Find all forms that should be protected with reCAPTCHA
 */
function findProtectedForms() {
    const forms = [];
    
    // Use each selector pattern to find matching forms
    RECAPTCHA_CONFIG.protectedForms.forEach(selector => {
        const foundForms = document.querySelectorAll(selector);
        foundForms.forEach(form => forms.push(form));
    });
    
    // Remove duplicates
    return [...new Set(forms)];
}

/**
 * Add reCAPTCHA container and verification to a form
 * @param {HTMLFormElement} form - The form to add reCAPTCHA to
 */
function addReCaptchaToForm(form) {
    // Skip if form already has reCAPTCHA
    if (form.querySelector('.g-recaptcha') || form.hasAttribute('data-recaptcha-id')) {
        return;
    }
    
    // Create container for reCAPTCHA with center alignment
    const container = document.createElement('div');
    container.className = 'recaptcha-container mb-3 d-flex justify-content-center';
    
    // Create placeholder text with center alignment
    const placeholder = document.createElement('div');
    placeholder.className = 'recaptcha-placeholder text-center';
    placeholder.innerHTML = `<div class="text-muted small py-2">${RECAPTCHA_CONFIG.loadingText}</div>`;
    container.appendChild(placeholder);
    
    // Find the right place to insert the reCAPTCHA container
    // Look for common form patterns to determine the ideal position
    
    // Priority 1: Look for a designated recaptcha placement marker
    const recaptchaPlaceholder = form.querySelector('.recaptcha-placeholder-slot, [data-recaptcha-slot]');
    if (recaptchaPlaceholder) {
        // Replace the placeholder with our container
        recaptchaPlaceholder.parentNode.replaceChild(container, recaptchaPlaceholder);
    } 
    // Priority 2: Look for terms and conditions or checkbox section
    else {
        const termsSection = form.querySelector('.form-check, .terms, .terms-section');
        if (termsSection && termsSection.parentNode) {
            // Insert after terms and conditions checkbox
            if (termsSection.nextSibling) {
                termsSection.parentNode.insertBefore(container, termsSection.nextSibling);
            } else {
                termsSection.parentNode.appendChild(container);
            }
        } 
        // Priority 3: Insert before the submit button with clearance
        else {
            const submitButton = form.querySelector('button[type="submit"], input[type="submit"], .btn-primary');
            if (submitButton && submitButton.parentNode) {
                // Create a wrapper if needed for better spacing
                const spacingWrapper = document.createElement('div');
                spacingWrapper.className = 'mt-3 mb-3';
                spacingWrapper.appendChild(container);
                
                submitButton.parentNode.insertBefore(spacingWrapper, submitButton);
            } else {
                // If no submit button found, append to end of form
                form.appendChild(container);
            }
        }
    }
    
    // Intercept form submission to verify reCAPTCHA
    form.addEventListener('submit', handleFormSubmit);
    
    // Lazy load reCAPTCHA when user interacts with the form
    const formInputs = form.querySelectorAll('input, select, textarea');
    const interactionHandler = function() {
        renderReCaptchaInForm(form, container);
        // Remove event listeners after first interaction
        formInputs.forEach(input => {
            input.removeEventListener('focus', interactionHandler);
            input.removeEventListener('click', interactionHandler);
        });
    };
    
    formInputs.forEach(input => {
        input.addEventListener('focus', interactionHandler);
        input.addEventListener('click', interactionHandler);
    });
    
    // Also initialize immediately if form has any filled inputs
    const hasFilledInputs = Array.from(formInputs).some(input => 
        input.value && input.type !== 'hidden' && input.type !== 'submit'
    );
    
    if (hasFilledInputs) {
        renderReCaptchaInForm(form, container);
    }
    
    // For testing and development, always render immediately
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        renderReCaptchaInForm(form, container);
    }
    
    // Force immediate load for placeholder slots
    if (recaptchaPlaceholder) {
        renderReCaptchaInForm(form, container);
    }
}

/**
 * Create and show a fallback option when reCAPTCHA fails to load
 * @param {HTMLFormElement} form - The form element
 * @param {HTMLElement} container - The container for the reCAPTCHA
 */
function showFallbackOption(form, container) {
    if (!RECAPTCHA_CONFIG.fallbackSettings.enableFallback) {
        return;
    }
    
    // Check if fallback already activated for this form
    const formId = generateFormId(form);
    if (reCAPTCHAState.fallbackActivated.has(formId)) {
        return;
    }
    
    // Mark form as using fallback
    reCAPTCHAState.fallbackActivated.add(formId);
    
    // Create fallback UI with centered content
    container.innerHTML = `
        <div class="alert alert-warning small mb-2 text-center" style="max-width: 320px; margin: 0 auto;">
            <div class="d-flex align-items-start mb-2 justify-content-center">
                <span class="material-icons fs-6 me-2 mt-1">warning</span>
                <div>
                    <strong>${RECAPTCHA_CONFIG.fallbackSettings.fallbackMessage}</strong>
                    <p class="mb-0 small text-muted">${RECAPTCHA_CONFIG.fallbackSettings.fallbackWarning}</p>
                </div>
            </div>
            <div class="d-grid">
                <button type="button" class="btn btn-sm btn-outline-secondary recaptcha-fallback-button">
                    <span class="material-icons fs-6 me-1">security</span>
                    I'm not a robot - Continue
                </button>
            </div>
        </div>
    `;
    
    // Add click handler for fallback button
    const fallbackButton = container.querySelector('.recaptcha-fallback-button');
    if (fallbackButton) {
        fallbackButton.addEventListener('click', () => {
            // Mark this form as verified to allow submission
            reCAPTCHAState.verifiedForms.add(formId);
            
            // Add verification indicator
            container.innerHTML = `
                <div class="alert alert-success small mb-2 d-flex align-items-center justify-content-center" style="max-width: 300px; margin: 0 auto;">
                    <span class="material-icons fs-6 me-2">check_circle</span>
                    <div>Verification bypassed</div>
                </div>
            `;
            
            // Allow form to be submitted
            form.querySelector('button[type="submit"]')?.focus();
        });
    }
}

/**
 * Render the reCAPTCHA widget inside a form
 * @param {HTMLFormElement} form - The form to add reCAPTCHA to
 * @param {HTMLElement} container - The container for the widget
 */
function renderReCaptchaInForm(form, container) {
    // Don't render if already done
    if (form.hasAttribute('data-recaptcha-id')) {
        return;
    }
    
    // Load script if not already loaded
    loadReCaptchaScript()
        .then(() => {
            if (!window.grecaptcha || !window.grecaptcha.render) {
                // Wait for the grecaptcha to be available
                const checkInterval = setInterval(() => {
                    if (window.grecaptcha && window.grecaptcha.render) {
                        clearInterval(checkInterval);
                        renderWidget();
                    }
                }, 100);
                return;
            }
            renderWidget();
        })
        .catch(error => {
            console.error('Error loading reCAPTCHA:', error);
            container.innerHTML = `
                <div class="alert alert-warning small py-2 text-center">
                    <span class="material-icons fs-6">warning</span>
                    Security verification could not be loaded. Please refresh the page.
                </div>
            `;
            
            // Check if we should show fallback
            if (reCAPTCHAState.loadAttempts >= RECAPTCHA_CONFIG.fallbackSettings.maxRetries) {
                showFallbackOption(form, container);
            } else {
                // Show error with retry button
                container.innerHTML = `
                    <div class="alert alert-warning small py-2">
                        <div class="d-flex align-items-center mb-2">
                            <span class="material-icons fs-6 me-2">warning</span>
                            <div>Security verification could not be loaded.</div>
                        </div>
                        <div class="d-grid">
                            <button type="button" class="btn btn-sm btn-outline-secondary recaptcha-retry-button">
                                <span class="material-icons fs-6 me-1">refresh</span>
                                Retry Loading
                            </button>
                        </div>
                    </div>
                `;
                
                // Add click handler for retry button
                const retryButton = container.querySelector('.recaptcha-retry-button');
                if (retryButton) {
                    retryButton.addEventListener('click', () => {
                        container.innerHTML = `<div class="text-muted small py-2">${RECAPTCHA_CONFIG.loadingText}</div>`;
                        renderReCaptchaInForm(form, container);
                    });
                }
            }
        });
    
    function renderWidget() {
        // Remove placeholder
        container.innerHTML = '';
        
        // Create centered element for the widget
        const widgetContainer = document.createElement('div');
        widgetContainer.className = 'g-recaptcha-wrapper'; // Add a wrapper for styling
        container.appendChild(widgetContainer);
        
        // Callback when user completes the reCAPTCHA
        const formId = generateFormId(form);
        reCAPTCHAState.callbacks[formId] = function(response) {
            if (response) {
                reCAPTCHAState.verifiedForms.add(formId);
                
                // Add hidden input with response token
                let hiddenInput = form.querySelector('input[name="g-recaptcha-response"]');
                if (!hiddenInput) {
                    hiddenInput = document.createElement('input');
                    hiddenInput.type = 'hidden';
                    hiddenInput.name = 'g-recaptcha-response';
                    form.appendChild(hiddenInput);
                }
                hiddenInput.value = response;
            }
        };
        
        try {
            // Render the widget
            const widgetId = window.grecaptcha.render(widgetContainer, {
                sitekey: RECAPTCHA_CONFIG.siteKey,
                theme: RECAPTCHA_CONFIG.theme,
                size: RECAPTCHA_CONFIG.size,
                callback: reCAPTCHAState.callbacks[formId]
            });
            
            form.setAttribute('data-recaptcha-id', widgetId);
            
            // Add a success indicator for when verification completes
            const verificationIndicator = document.createElement('div');
            verificationIndicator.className = 'recaptcha-verification-status mt-2 text-center small d-none';
            container.appendChild(verificationIndicator);
            
            // Monitor verification status to show a success indicator
            const originalCallback = reCAPTCHAState.callbacks[formId];
            reCAPTCHAState.callbacks[formId] = function(response) {
                // Call original callback
                if (originalCallback) {
                    originalCallback(response);
                }
                
                // Show success indicator
                if (response) {
                    verificationIndicator.className = 'recaptcha-verification-status mt-2 text-center small text-success';
                    verificationIndicator.innerHTML = '<span class="material-icons fs-6">check_circle</span> Verification successful';
                    
                    // Focus on submit button if available
                    setTimeout(() => {
                        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
                        if (submitBtn) {
                            submitBtn.focus();
                        }
                    }, 500);
                }
            };
            
        } catch (error) {
            console.error('Error rendering reCAPTCHA:', error);
            container.innerHTML = `
                <div class="alert alert-warning small py-2 text-center">
                    <span class="material-icons fs-6">warning</span>
                    Could not initialize security verification. Please refresh the page.
                </div>
            `;
        }
    }
}

/**
 * Generate a unique ID for a form
 * @param {HTMLFormElement} form - The form element
 * @returns {string} A unique ID for the form
 */
function generateFormId(form) {
    if (!form.id) {
        form.id = 'recaptcha-form-' + Math.random().toString(36).substring(2, 10);
    }
    return form.id;
}

/**
 * Handle form submission
 * @param {Event} event - The form submission event
 */
function handleFormSubmit(event) {
    const form = event.target;
    const formId = generateFormId(form);
    
    // Skip verification for forms that don't have reCAPTCHA rendered yet
    if (!form.hasAttribute('data-recaptcha-id')) {
        return;
    }
    
    // Skip verification if fallback was activated for this form
    if (reCAPTCHAState.fallbackActivated.has(formId) && reCAPTCHAState.verifiedForms.has(formId)) {
        return;
    }
    
    // Check if this form has been verified
    if (!reCAPTCHAState.verifiedForms.has(formId)) {
        event.preventDefault();
        
        // Show error message
        let errorContainer = form.querySelector('.recaptcha-error');
        if (!errorContainer) {
            errorContainer = document.createElement('div');
            errorContainer.className = 'recaptcha-error alert alert-danger small py-2 mt-2 text-center';
            errorContainer.style.maxWidth = '320px';
            errorContainer.style.margin = '0 auto';
            
            const recaptchaContainer = form.querySelector('.recaptcha-container');
            if (recaptchaContainer) {
                recaptchaContainer.appendChild(errorContainer);
            }
        }
        
        errorContainer.innerHTML = `
            <div class="d-flex align-items-center justify-content-center">
                <span class="material-icons fs-6 me-2">error</span>
                <span>${RECAPTCHA_CONFIG.errorMessages.notVerified}</span>
            </div>
        `;
        
        // Scroll to the error
        errorContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Hide error message after 5 seconds
        setTimeout(() => {
            errorContainer.style.display = 'none';
        }, 5000);
        
        // Focus on the reCAPTCHA widget
        try {
            const widgetId = parseInt(form.getAttribute('data-recaptcha-id'));
            window.grecaptcha.reset(widgetId);
        } catch (error) {
            console.error('Error resetting reCAPTCHA:', error);
        }
    }
}

/**
 * Reset all reCAPTCHA widgets and state
 */
function resetAllCaptchas() {
    reCAPTCHAState.verifiedForms.clear();
    
    try {
        if (window.grecaptcha && window.grecaptcha.reset) {
            const forms = findProtectedForms();
            forms.forEach(form => {
                if (form.hasAttribute('data-recaptcha-id')) {
                    const widgetId = parseInt(form.getAttribute('data-recaptcha-id'));
                    window.grecaptcha.reset(widgetId);
                }
            });
        }
    } catch (error) {
        console.error('Error resetting reCAPTCHA widgets:', error);
    }
}

/**
 * Check if the browser has network connectivity
 * @returns {boolean} True if online, false if offline
 */
function isOnline() {
    return navigator.onLine;
}

/**
 * Monitor network status and update reCAPTCHA accordingly
 */
function setupNetworkMonitoring() {
    window.addEventListener('online', () => {
        // Refresh reCAPTCHA when network comes back online
        const forms = findProtectedForms();
        forms.forEach(form => {
            const container = form.querySelector('.recaptcha-container');
            if (container) {
                renderReCaptchaInForm(form, container);
            }
        });
    });
    
    window.addEventListener('offline', () => {
        // When offline, enable fallback for all forms
        if (RECAPTCHA_CONFIG.fallbackSettings.enableFallback) {
            const forms = findProtectedForms();
            forms.forEach(form => {
                const container = form.querySelector('.recaptcha-container');
                if (container) {
                    showFallbackOption(form, container);
                }
            });
        }
    });
}

// Initialize when DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize reCAPTCHA with a small delay to prevent blocking page render
    setTimeout(initializeReCaptcha, 500);
    
    // Setup network status monitoring
    setupNetworkMonitoring();
});

// Reinitialize on AJAX navigation or content changes
document.addEventListener('contentChanged', function() {
    initializeReCaptcha();
});

// Export for global access
window.ReCaptchaHandler = {
    initialize: initializeReCaptcha,
    reset: resetAllCaptchas,
    bypass: function(formId) {
        // Allow programmatic bypass of reCAPTCHA for a specific form
        if (formId) {
            reCAPTCHAState.verifiedForms.add(formId);
            return true;
        }
        return false;
    }
};

/**
 * reCAPTCHA Handler for Forms
 * This script handles reCAPTCHA validation for protected forms
 */

// Track if reCAPTCHA has been validated
let recaptchaValidated = false;

// reCAPTCHA callback when the captcha is successfully completed
function onRecaptchaSuccess() {
    console.log('reCAPTCHA validated successfully');
    recaptchaValidated = true;
    document.querySelector('.recaptcha-message').textContent = '';
}

// reCAPTCHA callback when the captcha token expires
function onRecaptchaExpired() {
    console.log('reCAPTCHA validation expired');
    recaptchaValidated = false;
    document.querySelector('.recaptcha-message').textContent = 'reCAPTCHA verification expired. Please verify again.';
}

// reCAPTCHA callback when there's an error with the captcha
function onRecaptchaError() {
    console.log('reCAPTCHA validation error');
    recaptchaValidated = false;
    document.querySelector('.recaptcha-message').textContent = 'Error loading reCAPTCHA. Please refresh and try again.';
}

// Initialize protected forms when the document is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeProtectedForms();
});

// Function to initialize all forms that need protection
function initializeProtectedForms() {
    const protectedForms = document.querySelectorAll('form.protect-form');
    
    protectedForms.forEach(form => {
        form.addEventListener('submit', function(event) {
            // Check if this form has a reCAPTCHA
            const captchaElement = this.querySelector('.g-recaptcha');
            if (!captchaElement) {
                return; // No reCAPTCHA present, proceed normally
            }
            
            // Check if reCAPTCHA has been completed
            const recaptchaResponse = grecaptcha?.getResponse();
            
            if (!recaptchaResponse) {
                event.preventDefault(); // Stop the form from submitting
                
                // Show error message
                const messageElement = this.querySelector('.recaptcha-message');
                if (messageElement) {
                    messageElement.textContent = 'Please complete the reCAPTCHA verification.';
                }
                
                // Show error in SweetAlert if available
                if (window.Swal) {
                    Swal.fire({
                        icon: 'warning',
                        title: 'Verification Required',
                        text: 'Please complete the reCAPTCHA verification to proceed.',
                        confirmButtonText: 'OK'
                    });
                } else {
                    alert('Please complete the reCAPTCHA verification to proceed.');
                }
                
                return false;
            }
            
            // reCAPTCHA validated, allow form submission
            return true;
        });
    });
}

/**
 * Check if the current domain is valid for reCAPTCHA
 */
function validateDomain() {
    const { currentDomain, allowedDomains } = RECAPTCHA_CONFIG.domainConfig;
    
    console.log('Validating domain:', currentDomain);
    console.log('Allowed domains:', allowedDomains);
    
    // If we're running locally, always validate
    if (currentDomain === 'localhost' || currentDomain === '127.0.0.1') {
        console.log('Local development detected, domain validated');
        reCAPTCHAState.domainValidated = true;
        return true;
    }
    
    // If domain includes onrender.com, always validate (for Render hosting)
    if (currentDomain.includes('onrender.com')) {
        console.log('Render hosting detected, domain validated');
        reCAPTCHAState.domainValidated = true;
        return true;
    }
    
    // If no allowed domains are configured, assume it's valid
    if (!allowedDomains || allowedDomains.length === 0) {
        console.log('No allowed domains configured, assuming valid');
        reCAPTCHAState.domainValidated = true;
        return true;
    }
    
    // Check if current domain is in the allowed list
    const isValid = allowedDomains.some(domain => 
        currentDomain === domain || 
        (domain.startsWith('*.') && currentDomain.endsWith(domain.substring(1)))
    );
    
    if (isValid) {
        console.log('Domain validated successfully');
    } else {
        console.error('Domain validation failed. Current domain not in allowed list.');
    }
    
    reCAPTCHAState.domainValidated = isValid;
    return isValid;
} 