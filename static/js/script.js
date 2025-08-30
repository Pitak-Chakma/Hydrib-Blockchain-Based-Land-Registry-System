// JavaScript for Blockchain Land Management System

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize animations for page elements
    initAnimations();
    
    // Auto-dismiss alerts after 5 seconds with fade effect
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 500);
        });
    }, 5000);
    
    // Add animation to blockchain records
    const blockchainBadges = document.querySelectorAll('.badge.bg-success');
    blockchainBadges.forEach(function(badge) {
        if (badge.textContent.includes('BLK')) {
            badge.classList.add('blockchain-record');
            badge.setAttribute('title', 'Blockchain Record - Immutable Proof of Transaction');
            
            // Add hover effect to show full record
            badge.addEventListener('mouseenter', function() {
                const tooltip = document.createElement('div');
                tooltip.className = 'blockchain-tooltip';
                tooltip.textContent = badge.textContent;
                tooltip.style.position = 'absolute';
                tooltip.style.backgroundColor = 'rgba(0,0,0,0.8)';
                tooltip.style.color = 'white';
                tooltip.style.padding = '8px 12px';
                tooltip.style.borderRadius = '6px';
                tooltip.style.fontSize = '12px';
                tooltip.style.fontFamily = '"Roboto Mono", monospace';
                tooltip.style.zIndex = '1000';
                tooltip.style.maxWidth = '300px';
                tooltip.style.wordBreak = 'break-all';
                
                const rect = badge.getBoundingClientRect();
                tooltip.style.top = (rect.bottom + window.scrollY + 10) + 'px';
                tooltip.style.left = (rect.left + window.scrollX) + 'px';
                
                document.body.appendChild(tooltip);
                badge.tooltip = tooltip;
            });
            
            badge.addEventListener('mouseleave', function() {
                if (badge.tooltip) {
                    document.body.removeChild(badge.tooltip);
                    badge.tooltip = null;
                }
            });
        }
    });
    
    // Enhanced form validation for land listing with better UI feedback
    const addLandForm = document.querySelector('form[action*="add_land"]');
    if (addLandForm) {
        const priceInput = document.getElementById('price');
        
        if (priceInput) {
            // Add real-time validation
            priceInput.addEventListener('input', function() {
                validatePrice(priceInput);
            });
            
            // Validate on blur
            priceInput.addEventListener('blur', function() {
                validatePrice(priceInput);
            });
        }
        
        addLandForm.addEventListener('submit', function(event) {
            if (priceInput && parseFloat(priceInput.value) <= 0) {
                event.preventDefault();
                
                // Create a better error message
                const errorMsg = document.createElement('div');
                errorMsg.className = 'alert alert-danger mt-2';
                errorMsg.innerHTML = '<i class="bi bi-exclamation-triangle-fill me-2"></i> Price must be greater than zero!';
                
                // Remove any existing error messages
                const existingError = priceInput.parentNode.querySelector('.alert');
                if (existingError) {
                    priceInput.parentNode.removeChild(existingError);
                }
                
                // Add the new error message
                priceInput.parentNode.appendChild(errorMsg);
                
                // Highlight the input
                priceInput.classList.add('is-invalid');
                priceInput.focus();
            }
        });
    }
    
    // Role selection info display in signup form with enhanced UI
    const roleSelect = document.getElementById('role');
    if (roleSelect) {
        const roleInfo = document.getElementById('role-info');
        
        roleSelect.addEventListener('change', function() {
            if (this.value === 'seller' || this.value === 'buyer') {
                if (roleInfo.style.display === 'none' || roleInfo.style.display === '') {
                    roleInfo.style.display = 'block';
                    roleInfo.style.opacity = '0';
                    roleInfo.style.transform = 'translateY(-10px)';
                    
                    setTimeout(() => {
                        roleInfo.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                        roleInfo.style.opacity = '1';
                        roleInfo.style.transform = 'translateY(0)';
                    }, 10);
                }
            } else {
                if (roleInfo.style.display === 'block') {
                    roleInfo.style.opacity = '0';
                    roleInfo.style.transform = 'translateY(-10px)';
                    
                    setTimeout(() => {
                        roleInfo.style.display = 'none';
                    }, 300);
                }
            }
        });
        
        // Trigger change event to set initial state
        const event = new Event('change');
        roleSelect.dispatchEvent(event);
    }
    
    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80, // Offset for fixed header
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Add hover effects to feature cards
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px)';
            this.style.boxShadow = '0 10px 30px rgba(74, 108, 247, 0.15)';
            this.style.borderColor = 'rgba(74, 108, 247, 0.3)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = 'none';
            this.style.borderColor = 'rgba(74, 108, 247, 0.1)';
        });
    });
});

// Function to validate price input
function validatePrice(input) {
    const value = parseFloat(input.value);
    const feedbackElement = input.parentNode.querySelector('.invalid-feedback') || document.createElement('div');
    
    if (isNaN(value) || value <= 0) {
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
        
        feedbackElement.className = 'invalid-feedback';
        feedbackElement.textContent = 'Please enter a valid price greater than zero.';
        
        if (!input.parentNode.querySelector('.invalid-feedback')) {
            input.parentNode.appendChild(feedbackElement);
        }
    } else {
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
        
        if (input.parentNode.querySelector('.invalid-feedback')) {
            input.parentNode.removeChild(feedbackElement);
        }
    }
}

// Function to initialize animations
function initAnimations() {
    // Animate elements when they come into view
    const animateOnScroll = function() {
        const elements = document.querySelectorAll('.feature-card, .advantage-card, .section-heading, .blockchain-transactions-container');
        
        elements.forEach(element => {
            const elementPosition = element.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;
            
            if (elementPosition < windowHeight - 100) {
                element.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }
        });
    };
    
    // Set initial state for animations
    const elementsToAnimate = document.querySelectorAll('.feature-card, .advantage-card, .section-heading, .blockchain-transactions-container');
    elementsToAnimate.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
    });
    
    // Run animation on load and scroll
    window.addEventListener('scroll', animateOnScroll);
    window.addEventListener('load', animateOnScroll);
    
    // Trigger initial animation
    setTimeout(animateOnScroll, 100);
}