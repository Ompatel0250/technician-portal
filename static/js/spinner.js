/**
 * Utility functions for handling loading spinners across the application
 */

// Show spinner element with optional message
function showSpinner(elementId, message = 'Loading...') {
    const element = document.getElementById(elementId);
    if (element) {
        // Create spinner container if it doesn't exist
        let spinnerContainer = document.getElementById(`${elementId}-spinner-container`);
        if (!spinnerContainer) {
            spinnerContainer = document.createElement('div');
            spinnerContainer.id = `${elementId}-spinner-container`;
            spinnerContainer.className = 'spinner-container d-flex flex-column align-items-center justify-content-center p-5';
            
            // Create the spinner
            const spinner = document.createElement('div');
            spinner.className = 'spinner-border text-primary mb-3';
            spinner.setAttribute('role', 'status');
            
            // Create spinner sr-only text
            const srText = document.createElement('span');
            srText.className = 'visually-hidden';
            srText.textContent = 'Loading...';
            spinner.appendChild(srText);
            
            // Create message element
            const messageEl = document.createElement('div');
            messageEl.className = 'spinner-message text-muted';
            messageEl.id = `${elementId}-spinner-message`;
            messageEl.textContent = message;
            
            // Append all elements
            spinnerContainer.appendChild(spinner);
            spinnerContainer.appendChild(messageEl);
            
            // Store original content
            spinnerContainer.setAttribute('data-original-content', element.innerHTML);
            
            // Replace content with spinner
            element.innerHTML = '';
            element.appendChild(spinnerContainer);
        } else {
            // Update existing spinner message
            const messageEl = document.getElementById(`${elementId}-spinner-message`);
            if (messageEl) {
                messageEl.textContent = message;
            }
            
            // Make sure the spinner is visible
            spinnerContainer.style.display = 'flex';
        }
    }
}

// Hide spinner and restore original content
function hideSpinner(elementId) {
    const element = document.getElementById(elementId);
    const spinnerContainer = document.getElementById(`${elementId}-spinner-container`);
    
    if (element && spinnerContainer) {
        // Get original content
        const originalContent = spinnerContainer.getAttribute('data-original-content');
        
        // Restore original content if it exists
        if (originalContent) {
            element.innerHTML = originalContent;
        } else {
            // Just hide the spinner if there's no original content
            spinnerContainer.style.display = 'none';
        }
    }
}

// Show overlay spinner for the entire page or a specific element
function showOverlaySpinner(targetElementId = null, message = 'Loading...') {
    // Create overlay container
    let overlay = document.getElementById('global-spinner-overlay');
    
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'global-spinner-overlay';
        overlay.className = 'spinner-overlay';
        
        // Create spinner container
        const spinnerContainer = document.createElement('div');
        spinnerContainer.className = 'd-flex flex-column align-items-center justify-content-center';
        
        // Create spinner
        const spinner = document.createElement('div');
        spinner.className = 'spinner-border text-light';
        spinner.style.width = '3rem';
        spinner.style.height = '3rem';
        spinner.setAttribute('role', 'status');
        
        // Create spinner sr-only text
        const srText = document.createElement('span');
        srText.className = 'visually-hidden';
        srText.textContent = 'Loading...';
        spinner.appendChild(srText);
        
        // Create message
        const messageEl = document.createElement('div');
        messageEl.className = 'text-light mt-3';
        messageEl.id = 'global-spinner-message';
        messageEl.textContent = message;
        
        // Append to container
        spinnerContainer.appendChild(spinner);
        spinnerContainer.appendChild(messageEl);
        overlay.appendChild(spinnerContainer);
        
        // If target element specified, make the overlay relative to that element
        if (targetElementId) {
            const targetElement = document.getElementById(targetElementId);
            if (targetElement) {
                targetElement.style.position = 'relative';
                overlay.style.position = 'absolute';
                targetElement.appendChild(overlay);
            } else {
                // Fallback to body if target element not found
                document.body.appendChild(overlay);
            }
        } else {
            // Otherwise append to body (full screen overlay)
            document.body.appendChild(overlay);
        }
    } else {
        // Update existing spinner message
        const messageEl = document.getElementById('global-spinner-message');
        if (messageEl) {
            messageEl.textContent = message;
        }
        
        // Make sure overlay is visible
        overlay.style.display = 'flex';
    }
}

// Hide overlay spinner
function hideOverlaySpinner() {
    const overlay = document.getElementById('global-spinner-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// Automatically add spinner for all action buttons with data-spinner attribute
document.addEventListener('DOMContentLoaded', function() {
    // Attach to buttons with data-spinner attribute
    const spinnerButtons = document.querySelectorAll('[data-spinner]');
    
    spinnerButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Get target container ID from data-spinner-target, default to global if not set
            const targetId = this.getAttribute('data-spinner-target') || null;
            const message = this.getAttribute('data-spinner-message') || 'Processing...';
            
            if (targetId) {
                showSpinner(targetId, message);
            } else {
                showOverlaySpinner(null, message);
            }
        });
    });
});