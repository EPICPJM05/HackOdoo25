// Main JavaScript for Skill Swap Platform

// Initialize Socket.IO connection
let socket = io();

// Global variables
let currentUser = null;
let pendingCount = 0;

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Initialize application
function initializeApp() {
    setupSocketIO();
    setupFormValidation();
    setupRealTimeUpdates();
    setupSearchFunctionality();
    setupRatingSystem();
    setupModalHandlers();
    setupPagination();
}

// Socket.IO setup
function setupSocketIO() {
    // Connect to Socket.IO
    socket.on('connect', function() {
        console.log('Connected to server');
    });

    // Handle new swap request notifications
    socket.on('new_swap_request', function(data) {
        showNotification('New swap request received!', 'info');
        updatePendingCount();
    });

    // Handle swap accepted notifications
    socket.on('swap_accepted', function(data) {
        showNotification('Your swap request has been accepted!', 'success');
        updatePendingCount();
    });

    // Handle swap rejected notifications
    socket.on('swap_rejected', function(data) {
        showNotification('Your swap request has been rejected.', 'warning');
        updatePendingCount();
    });

    // Handle swap completed notifications
    socket.on('swap_completed', function(data) {
        showNotification('Swap marked as completed!', 'success');
    });

    // Handle disconnect
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
    });
}

// Form validation setup
function setupFormValidation() {
    // Email validation
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateEmail(this.value, this);
        });
    });

    // Password validation
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        input.addEventListener('input', function() {
            validatePassword(this.value, this);
        });
    });

    // Skill name validation
    const skillInputs = document.querySelectorAll('input[name="skill_name"]');
    skillInputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateSkillName(this.value, this);
        });
    });

    // Real-time email availability check
    const registerEmail = document.querySelector('input[name="email"]');
    if (registerEmail) {
        let emailTimeout;
        registerEmail.addEventListener('input', function() {
            clearTimeout(emailTimeout);
            emailTimeout = setTimeout(() => {
                checkEmailAvailability(this.value);
            }, 500);
        });
    }
}

// Email validation
function validateEmail(email, inputElement) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValid = emailRegex.test(email);
    
    if (inputElement) {
        if (isValid) {
            inputElement.classList.remove('is-invalid');
            inputElement.classList.add('is-valid');
        } else {
            inputElement.classList.remove('is-valid');
            inputElement.classList.add('is-invalid');
        }
    }
    
    return isValid;
}

// Password validation
function validatePassword(password, inputElement) {
    const isValid = password.length >= 6;
    
    if (inputElement) {
        if (isValid) {
            inputElement.classList.remove('is-invalid');
            inputElement.classList.add('is-valid');
        } else {
            inputElement.classList.remove('is-valid');
            inputElement.classList.add('is-invalid');
        }
    }
    
    return isValid;
}

// Skill name validation
function validateSkillName(skillName, inputElement) {
    const isValid = skillName.length >= 2 && /^[a-zA-Z0-9\s\-]+$/.test(skillName);
    
    if (inputElement) {
        if (isValid) {
            inputElement.classList.remove('is-invalid');
            inputElement.classList.add('is-valid');
        } else {
            inputElement.classList.remove('is-valid');
            inputElement.classList.add('is-invalid');
        }
    }
    
    return isValid;
}

// Check email availability
function checkEmailAvailability(email) {
    if (!email || !validateEmail(email)) return;
    
    fetch('/api/check-email', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: email })
    })
    .then(response => response.json())
    .then(data => {
        const emailInput = document.querySelector('input[name="email"]');
        if (emailInput) {
            if (data.available) {
                emailInput.classList.remove('is-invalid');
                emailInput.classList.add('is-valid');
                showFieldMessage(emailInput, 'Email is available', 'valid');
            } else {
                emailInput.classList.remove('is-valid');
                emailInput.classList.add('is-invalid');
                showFieldMessage(emailInput, data.message, 'invalid');
            }
        }
    })
    .catch(error => {
        console.error('Error checking email availability:', error);
    });
}

// Show field message
function showFieldMessage(element, message, type) {
    // Remove existing message
    const existingMessage = element.parentNode.querySelector('.field-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // Create new message
    const messageDiv = document.createElement('div');
    messageDiv.className = `field-message text-${type === 'valid' ? 'success' : 'danger'} small mt-1`;
    messageDiv.textContent = message;
    
    element.parentNode.appendChild(messageDiv);
}

// Real-time updates setup
function setupRealTimeUpdates() {
    // Update pending count every 30 seconds
    if (document.getElementById('pending-count')) {
        updatePendingCount();
        setInterval(updatePendingCount, 30000);
    }
    
    // Update active swaps count
    if (document.getElementById('active-count')) {
        updateActiveCount();
        setInterval(updateActiveCount, 60000);
    }
}

// Update pending count
function updatePendingCount() {
    fetch('/api/swaps/pending-count')
        .then(response => response.json())
        .then(data => {
            const countElement = document.getElementById('pending-count');
            if (countElement) {
                pendingCount = data.count;
                if (pendingCount > 0) {
                    countElement.textContent = pendingCount;
                    countElement.style.display = 'inline';
                } else {
                    countElement.style.display = 'none';
                }
            }
        })
        .catch(error => {
            console.error('Error updating pending count:', error);
        });
}

// Update active count
function updateActiveCount() {
    fetch('/api/swaps/active-count')
        .then(response => response.json())
        .then(data => {
            const countElement = document.getElementById('active-count');
            if (countElement) {
                countElement.textContent = data.count;
            }
        })
        .catch(error => {
            console.error('Error updating active count:', error);
        });
}

// Search functionality setup
function setupSearchFunctionality() {
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            performSearch();
        });
    }
    
    // Skill search autocomplete
    const skillSearchInput = document.querySelector('input[name="skill"]');
    if (skillSearchInput) {
        let searchTimeout;
        skillSearchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                searchSkills(this.value);
            }, 300);
        });
    }
    
    // Add clear filters functionality
    const clearFiltersBtn = document.getElementById('clear-filters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', function() {
            window.location.href = window.location.pathname;
        });
    }
}

// Perform search
function performSearch() {
    const searchInput = document.querySelector('input[name="skill"]');
    const skillType = document.querySelector('select[name="type"]');
    const nameInput = document.querySelector('input[name="name"]');
    const locationInput = document.querySelector('input[name="location"]');
    
    const searchUrl = new URL(window.location);
    
    // Add all search parameters
    if (searchInput && searchInput.value.trim()) {
        searchUrl.searchParams.set('skill', searchInput.value.trim());
    } else {
        searchUrl.searchParams.delete('skill');
    }
    
    if (skillType) {
        searchUrl.searchParams.set('type', skillType.value);
    }
    
    if (nameInput && nameInput.value.trim()) {
        searchUrl.searchParams.set('name', nameInput.value.trim());
    } else {
        searchUrl.searchParams.delete('name');
    }
    
    if (locationInput && locationInput.value.trim()) {
        searchUrl.searchParams.set('location', locationInput.value.trim());
    } else {
        searchUrl.searchParams.delete('location');
    }
    
    window.location.href = searchUrl.toString();
}

// Search skills for autocomplete
function searchSkills(query) {
    if (query.length < 2) return;
    
    fetch('/api/skills/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ search: query })
    })
    .then(response => response.json())
    .then(data => {
        showSkillSuggestions(data.skills);
    })
    .catch(error => {
        console.error('Error searching skills:', error);
    });
}

// Show skill suggestions
function showSkillSuggestions(skills) {
    const searchInput = document.querySelector('input[name="skill"]');
    if (!searchInput) return;
    
    // Remove existing suggestions
    const existingSuggestions = document.querySelector('.skill-suggestions');
    if (existingSuggestions) {
        existingSuggestions.remove();
    }
    
    if (skills.length === 0) return;
    
    // Create suggestions dropdown
    const suggestionsDiv = document.createElement('div');
    suggestionsDiv.className = 'skill-suggestions position-absolute bg-white border rounded shadow-sm';
    suggestionsDiv.style.top = '100%';
    suggestionsDiv.style.left = '0';
    suggestionsDiv.style.right = '0';
    suggestionsDiv.style.zIndex = '1000';
    
    skills.forEach(skill => {
        const suggestionItem = document.createElement('div');
        suggestionItem.className = 'suggestion-item p-2 cursor-pointer';
        suggestionItem.textContent = skill;
        suggestionItem.addEventListener('click', function() {
            searchInput.value = skill;
            suggestionsDiv.remove();
        });
        suggestionsDiv.appendChild(suggestionItem);
    });
    
    searchInput.parentNode.style.position = 'relative';
    searchInput.parentNode.appendChild(suggestionsDiv);
}

// Rating system setup
function setupRatingSystem() {
    const ratingContainers = document.querySelectorAll('.rating-input');
    ratingContainers.forEach(container => {
        const stars = container.querySelectorAll('.star');
        const hiddenInput = container.querySelector('input[type="hidden"]');
        
        stars.forEach((star, index) => {
            star.addEventListener('click', function() {
                const rating = index + 1;
                hiddenInput.value = rating;
                
                // Update star display
                stars.forEach((s, i) => {
                    if (i < rating) {
                        s.classList.add('text-warning');
                    } else {
                        s.classList.remove('text-warning');
                    }
                });
            });
            
            star.addEventListener('mouseenter', function() {
                const hoverRating = index + 1;
                stars.forEach((s, i) => {
                    if (i < hoverRating) {
                        s.classList.add('text-warning');
                    } else {
                        s.classList.remove('text-warning');
                    }
                });
            });
            
            star.addEventListener('mouseleave', function() {
                const currentRating = parseInt(hiddenInput.value) || 0;
                stars.forEach((s, i) => {
                    if (i < currentRating) {
                        s.classList.add('text-warning');
                    } else {
                        s.classList.remove('text-warning');
                    }
                });
            });
        });
    });
}

// Modal handlers setup
function setupModalHandlers() {
    // Swap request modal
    const swapRequestModal = document.getElementById('swapRequestModal');
    if (swapRequestModal) {
        swapRequestModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const userId = button.getAttribute('data-user-id');
            const userName = button.getAttribute('data-user-name');
            
            const modal = this;
            modal.querySelector('#receiver-id').value = userId;
            modal.querySelector('.modal-title').textContent = `Send Swap Request to ${userName}`;
        });
    }
    
    // Confirm action modals
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
}

// Pagination setup
function setupPagination() {
    const paginationLinks = document.querySelectorAll('.pagination .page-link');
    paginationLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const url = new URL(this.href);
            const currentUrl = new URL(window.location);
            
            // Preserve existing search parameters
            url.searchParams.forEach((value, key) => {
                currentUrl.searchParams.set(key, value);
            });
            
            window.location.href = currentUrl.toString();
        });
    });
}

// Show notification
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Loading spinner
function showLoading(element) {
    const spinner = document.createElement('div');
    spinner.className = 'spinner';
    element.appendChild(spinner);
    element.disabled = true;
}

function hideLoading(element) {
    const spinner = element.querySelector('.spinner');
    if (spinner) {
        spinner.remove();
    }
    element.disabled = false;
}

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Export functions for use in other scripts
window.SkillSwapApp = {
    showNotification,
    showLoading,
    hideLoading,
    formatDate,
    truncateText,
    updatePendingCount,
    updateActiveCount
};

// Handle platform-wide messages
function handlePlatformMessages() {
    const socket = io();
    
    socket.on('platform_message', function(data) {
        showPlatformMessage(data);
    });
}

// Show platform message
function showPlatformMessage(data) {
    const alertHtml = `
        <div class="alert alert-${data.type} alert-dismissible fade show" role="alert">
            <div class="d-flex align-items-center">
                <div class="flex-grow-1">
                    <h6 class="alert-heading mb-1">${data.title}</h6>
                    <p class="mb-0">${data.message}</p>
                    <small class="text-muted">Platform Message • ${new Date(data.timestamp).toLocaleString()}</small>
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        </div>
    `;
    
    // Insert at the top of the flash messages container
    const flashContainer = document.querySelector('.container.mt-3');
    if (flashContainer) {
        flashContainer.insertAdjacentHTML('afterbegin', alertHtml);
    }
}

// Initialize platform message handling
document.addEventListener('DOMContentLoaded', function() {
    handlePlatformMessages();
}); 