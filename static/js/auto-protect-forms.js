/**
 * Auto-Protect Forms - Utility script for Traffic Violation System
 * 
 * This script automatically identifies sensitive forms in the application
 * and adds the data-protected attribute to them so that they are protected
 * by the reCAPTCHA handler.
 */

(function() {
    // Configuration
    const SENSITIVE_FORM_PATTERNS = {
        // Form action patterns that indicate sensitive forms
        actionPatterns: [
            '/login',
            '/register',
            '/password',
            '/reset',
            '/verification',
            '/auth',
            '/profile',
            '/account',
            '/payment',
            '/transaction',
            '/violation',
            '/upload'
        ],
        
        // Form input patterns that indicate sensitive forms
        inputPatterns: {
            password: ['password', 'new_password', 'confirm_password', 'current_password'],
            credentials: ['username', 'email', 'license_number', 'phone_number', 'ssn'],
            payment: ['card_number', 'cvv', 'expiry', 'payment_method', 'transaction_id'],
            personal: ['first_name', 'last_name', 'address', 'birthdate']
        },
        
        // Minimum number of sensitive inputs to auto-protect a form
        minSensitiveInputs: 2
    };
    
    /**
     * Check if a form should be protected based on action URL
     * @param {HTMLFormElement} form - The form to check
     * @returns {boolean} True if the form should be protected
     */
    function isActionSensitive(form) {
        const action = form.getAttribute('action') || window.location.pathname;
        
        return SENSITIVE_FORM_PATTERNS.actionPatterns.some(pattern => 
            action.toLowerCase().includes(pattern)
        );
    }
    
    /**
     * Check if a form contains sensitive inputs
     * @param {HTMLFormElement} form - The form to check
     * @returns {boolean} True if the form has sensitive inputs
     */
    function hasSensitiveInputs(form) {
        const inputs = form.querySelectorAll('input');
        let sensitiveCount = 0;
        
        inputs.forEach(input => {
            const name = input.getAttribute('name') || '';
            const id = input.getAttribute('id') || '';
            const type = input.getAttribute('type') || '';
            
            // Check if input is a password field
            if (type === 'password') {
                sensitiveCount++;
                return;
            }
            
            // Check other sensitive input patterns
            for (const category in SENSITIVE_FORM_PATTERNS.inputPatterns) {
                const patterns = SENSITIVE_FORM_PATTERNS.inputPatterns[category];
                
                if (patterns.some(pattern => 
                    name.toLowerCase().includes(pattern) || 
                    id.toLowerCase().includes(pattern)
                )) {
                    sensitiveCount++;
                    break;
                }
            }
        });
        
        return sensitiveCount >= SENSITIVE_FORM_PATTERNS.minSensitiveInputs;
    }

    /**
     * Check if a form is a search form
     * @param {HTMLFormElement} form - The form to check
     * @returns {boolean} True if the form is a search form
     */
    function isSearchForm(form) {
        // Check for search-related attributes
        if (form.classList.contains('search-form') || form.id.includes('search')) {
            return true;
        }
        
        // Check if the form has a search input
        const searchInput = form.querySelector('input[type="search"], input[name*="search"], input[name*="query"], input[id*="search"], input[id*="query"]');
        if (searchInput) {
            return true;
        }
        
        // Check if the form has a search button or icon
        const searchButton = form.querySelector('button[type="submit"] .material-icons');
        if (searchButton && searchButton.textContent.trim() === 'search') {
            return true;
        }
        
        return false;
    }
    
    /**
     * Check if a form is likely to be sensitive
     * @param {HTMLFormElement} form - The form to check
     * @returns {boolean} True if the form is likely sensitive
     */
    function isSensitiveForm(form) {
        // Skip forms that are already protected
        if (form.hasAttribute('data-protected')) {
            return false;
        }
        
        // Skip forms with novalidate-recaptcha attribute
        if (form.hasAttribute('data-novalidate-recaptcha')) {
            return false;
        }
        
        // Skip search forms
        if (isSearchForm(form)) {
            return false;
        }
        
        // Check if form has action that indicates sensitivity
        if (isActionSensitive(form)) {
            return true;
        }
        
        // Check if form has sensitive inputs
        if (hasSensitiveInputs(form)) {
            return true;
        }
        
        return false;
    }
    
    /**
     * Find and protect all sensitive forms on the page
     */
    function protectSensitiveForms() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            // Check if form has a reCAPTCHA placeholder
            const hasPlaceholder = !!form.querySelector('.recaptcha-placeholder-slot, [data-recaptcha-slot]');
            
            // If form has a placeholder or is sensitive, protect it
            if (hasPlaceholder || isSensitiveForm(form)) {
                form.setAttribute('data-protected', 'true');
                
                // Log to console if in development mode
                if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                    console.log('Auto-protected form:', form.id || form.action || 'unnamed form');
                }
            }
        });
        
        // If reCAPTCHA handler is available, reinitialize it
        if (window.ReCaptchaHandler && typeof window.ReCaptchaHandler.initialize === 'function') {
            window.ReCaptchaHandler.initialize();
        }
    }
    
    // Run on page load and after any content changes
    document.addEventListener('DOMContentLoaded', protectSensitiveForms);
    document.addEventListener('contentChanged', protectSensitiveForms);
    
    // Run after slight delay to catch dynamically loaded forms
    setTimeout(protectSensitiveForms, 1000);
})();

/**
 * Auto-protect forms by adding reCAPTCHA verification
 * This script automatically adds reCAPTCHA to forms with the 'protect-form' class
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if reCAPTCHA script is already loaded
    const isRecaptchaLoaded = typeof grecaptcha !== 'undefined';
    
    // Find all forms with the 'protect-form' class that don't already have reCAPTCHA
    // Exclude forms with the 'search-form' class
    const forms = document.querySelectorAll('form.protect-form:not(.recaptcha-processed):not(.search-form)');
    
    // Only proceed if we have forms that need protection
    if (forms.length === 0) {
        return;
    }
    
    // Mark forms as processed to prevent double-processing
    forms.forEach(form => {
        form.classList.add('recaptcha-processed');
        
        // Skip if this is a search form
        if (form.classList.contains('search-form') || form.id.includes('search')) {
            return;
        }
        
        // Check if the form already has a reCAPTCHA container
        if (!form.querySelector('.recaptcha-container')) {
            // Create reCAPTCHA container
            const recaptchaContainer = document.createElement('div');
            recaptchaContainer.className = 'recaptcha-container mt-3';
            
            // Create reCAPTCHA div
            const recaptchaDiv = document.createElement('div');
            recaptchaDiv.className = 'g-recaptcha';
            
            // Get site key from meta tag without fallback
            const siteKeyMeta = document.querySelector('meta[name="recaptcha-site-key"]');
            const siteKey = siteKeyMeta ? siteKeyMeta.getAttribute('content') : '';
            
            // Log site key (but don't show the full key for security)
            if (siteKey) {
                const maskedKey = siteKey.substring(0, 8) + '...' + siteKey.substring(siteKey.length - 4);
                console.log('Using reCAPTCHA site key:', maskedKey);
            } else {
                console.error('No reCAPTCHA site key found in meta tags. reCAPTCHA will not work.');
            }
            
            // Only add reCAPTCHA if we have a site key
            if (siteKey) {
                // Set reCAPTCHA attributes
                recaptchaDiv.setAttribute('data-sitekey', siteKey);
                recaptchaDiv.setAttribute('data-callback', 'onRecaptchaSuccess');
                recaptchaDiv.setAttribute('data-expired-callback', 'onRecaptchaExpired');
                recaptchaDiv.setAttribute('data-error-callback', 'onRecaptchaError');
                
                // Create message container for errors
                const messageDiv = document.createElement('div');
                messageDiv.className = 'recaptcha-message text-danger mt-1';
                
                // Append elements
                recaptchaContainer.appendChild(recaptchaDiv);
                recaptchaContainer.appendChild(messageDiv);
            } else {
                // Display a warning if no site key is available
                recaptchaContainer.innerHTML = `
                    <div class="alert alert-warning small py-2 text-center">
                        <span class="material-icons fs-6 me-2">warning</span>
                        <span>reCAPTCHA configuration issue. Please contact the administrator.</span>
                    </div>
                `;
            }
            
            // Find submission button for positioning
            const submitButton = form.querySelector('[type="submit"]');
            if (submitButton) {
                // Insert reCAPTCHA before the submit button or its container
                const buttonContainer = submitButton.closest('.form-group') || submitButton.parentNode;
                form.insertBefore(recaptchaContainer, buttonContainer);
            } else {
                // Just append to the end of the form if no submit button found
                form.appendChild(recaptchaContainer);
            }
        }
    });
    
    // If reCAPTCHA script is not loaded yet, load it
    if (!isRecaptchaLoaded && !document.getElementById('recaptcha-script')) {
        const script = document.createElement('script');
        script.id = 'recaptcha-script';
        script.src = 'https://www.google.com/recaptcha/api.js';
        script.async = true;
        script.defer = true;
        document.head.appendChild(script);
    }
}); 