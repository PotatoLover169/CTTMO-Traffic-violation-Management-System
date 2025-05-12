/**
 * reCAPTCHA Bypass Script
 * 
 * This script creates a complete mock of the reCAPTCHA API to bypass validation
 * without modifying server-side code. Use only in development environments.
 */

// Create a complete mock of the reCAPTCHA API
window.grecaptcha = {
    ready: function(callback) {
        if (typeof callback === 'function') {
            setTimeout(callback, 0);
        }
    },
    execute: function() {
        return new Promise(function(resolve) {
            resolve("recaptcha-bypass-token");
        });
    },
    render: function() {
        return 1; // Return a dummy widget ID
    },
    reset: function() {},
    getResponse: function() {
        return "recaptcha-bypass-token";
    }
};

// Create a validateRecaptcha function that always returns true
window.validateRecaptcha = function() {
    console.log("reCAPTCHA validation bypassed");
    return true;
};

// Prevent any JSON parsing errors in recaptcha-handler.js
const originalJSONParse = JSON.parse;
JSON.parse = function(text) {
    try {
        return originalJSONParse(text);
    } catch (e) {
        console.warn('Prevented JSON parse error:', e);
        if (text && typeof text === 'string' && text.includes('reCAPTCHA')) {
            // Return a dummy reCAPTCHA configuration object
            return {
                "success": true,
                "action": "submit",
                "score": 0.9,
                "hostname": window.location.hostname
            };
        }
        // Re-throw for non-reCAPTCHA related errors
        throw e;
    }
};

// Define reCAPTCHA callback functions
window.onRecaptchaSuccess = function() {
    console.log('reCAPTCHA validated successfully (bypass)');
};

window.onRecaptchaExpired = function() {
    console.log('reCAPTCHA expiration bypassed');
};

window.onRecaptchaError = function() {
    console.log('reCAPTCHA error bypassed');
};

// When the DOM is loaded, mark all forms to bypass reCAPTCHA validation
document.addEventListener('DOMContentLoaded', function() {
    // Find all forms and add data-novalidate-recaptcha attribute
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.setAttribute('data-novalidate-recaptcha', 'true');
        console.log('Form marked to bypass reCAPTCHA:', form);
    });
    
    // Remove any existing reCAPTCHA containers
    const recaptchaContainers = document.querySelectorAll('.recaptcha-container, .g-recaptcha');
    recaptchaContainers.forEach(function(container) {
        container.remove();
        console.log('Removed reCAPTCHA container');
    });
    
    console.log('reCAPTCHA bypass initialized successfully');
}); 