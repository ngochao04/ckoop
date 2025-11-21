// Get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Format price to VND
function formatPrice(price) {
    return new Intl.NumberFormat('vi-VN', { 
        style: 'currency', 
        currency: 'VND' 
    }).format(price);
}

// Format date
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('vi-VN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Check if user is logged in
function isLoggedIn() {
    return localStorage.getItem('token') !== null;
}

// Get current user
function getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}

// Logout user
function logout() {
    const token = localStorage.getItem('token');
    
    if (confirm('Bạn có chắc muốn đăng xuất?')) {
        if (token) {
            fetch('/api/accounts/logout/', {
                method: 'POST',
                headers: {
                    'Authorization': 'Token ' + token,
                    'X-CSRFToken': getCookie('csrftoken')
                }
            }).then(() => {
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                window.location.href = '/';
            }).catch(() => {
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                window.location.href = '/';
            });
        } else {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/';
        }
    }
}

// Update cart count in navbar
function updateCartCount() {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    fetch('/api/cart/me/', {
        headers: {
            'Authorization': 'Token ' + token
        }
    })
    .then(res => res.json())
    .then(data => {
        const cartCountElement = document.getElementById('cart-count');
        if (cartCountElement) {
            cartCountElement.textContent = data.total_items || 0;
        }
    })
    .catch(err => console.error('Error loading cart:', err));
}

// Show loading spinner
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Đang tải...</span>
                </div>
            </div>
        `;
    }
}

// Show error message
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="text-center py-5">
                <p class="text-danger">${message}</p>
            </div>
        `;
    }
}

// Show success message
function showSuccess(message, duration = 3000) {
    const messageDiv = document.getElementById('message');
    if (messageDiv) {
        messageDiv.innerHTML = `<div class="alert alert-success">${message}</div>`;
        
        setTimeout(() => {
            messageDiv.innerHTML = '';
        }, duration);
    }
}

// Show error alert
function showErrorAlert(message, duration = 3000) {
    const messageDiv = document.getElementById('message');
    if (messageDiv) {
        messageDiv.innerHTML = `<div class="alert alert-danger">${message}</div>`;
        
        setTimeout(() => {
            messageDiv.innerHTML = '';
        }, duration);
    }
}

// Redirect to login if not authenticated
function requireAuth() {
    if (!isLoggedIn()) {
        alert('Vui lòng đăng nhập để tiếp tục');
        window.location.href = '/login/';
        return false;
    }
    return true;
}

// Make authenticated API call
async function apiCall(url, options = {}) {
    const token = localStorage.getItem('token');
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            ...(token ? { 'Authorization': 'Token ' + token } : {})
        }
    };
    
    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };
    
    try {
        const response = await fetch(url, mergedOptions);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Có lỗi xảy ra');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Initialize page - check authentication
function initializePage() {
    updateCartCount();
}

// Run on every page load
document.addEventListener('DOMContentLoaded', initializePage);