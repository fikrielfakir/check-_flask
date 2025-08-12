// Frontend performance optimizations

// Lazy Loading with Intersection Observer
class LazyLoader {
    constructor() {
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadContent(entry.target);
                    this.observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });
    }

    observe(element) {
        this.observer.observe(element);
    }

    loadContent(element) {
        const chartType = element.dataset.chart;
        if (chartType) {
            this.loadChartData(chartType, element);
        }
    }

    async loadChartData(chartType, element) {
        try {
            const response = await fetch(`/api/charts/${chartType}`);
            const data = await response.json();
            
            // Render chart based on type
            switch(chartType) {
                case 'monthly-trends':
                    this.renderMonthlyTrends(data, element);
                    break;
                case 'risk-distribution':
                    this.renderRiskDistribution(data, element);
                    break;
                case 'bank-performance':
                    this.renderBankPerformance(data, element);
                    break;
            }
        } catch (error) {
            console.error('Error loading chart data:', error);
            element.innerHTML = '<div class="alert alert-warning">Erreur de chargement des données</div>';
        }
    }

    renderMonthlyTrends(data, element) {
        // Implementation for monthly trends chart
        element.innerHTML = `
            <canvas id="monthly-trends-chart"></canvas>
        `;
        // Chart.js implementation would go here
    }

    renderRiskDistribution(data, element) {
        // Implementation for risk distribution chart
        element.innerHTML = `
            <canvas id="risk-distribution-chart"></canvas>
        `;
    }

    renderBankPerformance(data, element) {
        // Implementation for bank performance chart
        element.innerHTML = `
            <canvas id="bank-performance-chart"></canvas>
        `;
    }
}

// Debounce utility for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Optimized search with debouncing
class SmartSearch {
    constructor(inputElement, suggestionsElement, apiEndpoint) {
        this.input = inputElement;
        this.suggestions = suggestionsElement;
        this.apiEndpoint = apiEndpoint;
        this.cache = new Map();
        
        this.debouncedSearch = debounce(this.performSearch.bind(this), 300);
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.input.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            if (query.length >= 2) {
                this.debouncedSearch(query);
            } else {
                this.hideSuggestions();
            }
        });
    }

    async performSearch(query) {
        // Check cache first
        if (this.cache.has(query)) {
            this.displaySuggestions(this.cache.get(query));
            return;
        }

        try {
            const response = await fetch(`${this.apiEndpoint}?q=${encodeURIComponent(query)}`);
            const results = await response.json();
            
            // Cache results
            this.cache.set(query, results);
            
            this.displaySuggestions(results);
        } catch (error) {
            console.error('Search error:', error);
        }
    }

    displaySuggestions(results) {
        this.suggestions.innerHTML = '';
        
        if (results.length === 0) {
            this.suggestions.innerHTML = '<div class="no-results">Aucun résultat trouvé</div>';
        } else {
            results.forEach(result => {
                const item = document.createElement('div');
                item.className = 'suggestion-item';
                item.innerHTML = this.formatSuggestion(result);
                item.addEventListener('click', () => this.selectSuggestion(result));
                this.suggestions.appendChild(item);
            });
        }
        
        this.suggestions.style.display = 'block';
    }

    formatSuggestion(result) {
        return `
            <div class="suggestion-content">
                <div class="suggestion-title">${result.name}</div>
                <div class="suggestion-details">${result.details || ''}</div>
            </div>
        `;
    }

    selectSuggestion(result) {
        this.input.value = result.name;
        this.hideSuggestions();
        
        // Trigger custom event
        this.input.dispatchEvent(new CustomEvent('suggestion-selected', { detail: result }));
    }

    hideSuggestions() {
        this.suggestions.style.display = 'none';
    }
}

// Performance monitoring
class PerformanceMonitor {
    constructor() {
        this.metrics = {
            pageLoadTime: 0,
            apiCallTimes: [],
            errorCount: 0
        };
        
        this.startMonitoring();
    }

    startMonitoring() {
        // Monitor page load time
        window.addEventListener('load', () => {
            this.metrics.pageLoadTime = performance.now();
            this.sendMetrics();
        });

        // Monitor API calls
        this.interceptFetch();
        
        // Monitor errors
        window.addEventListener('error', (e) => {
            this.metrics.errorCount++;
            console.error('JavaScript error:', e.error);
        });
    }

    interceptFetch() {
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            const startTime = performance.now();
            try {
                const response = await originalFetch(...args);
                const endTime = performance.now();
                
                this.metrics.apiCallTimes.push({
                    url: args[0],
                    duration: endTime - startTime,
                    status: response.status
                });
                
                return response;
            } catch (error) {
                this.metrics.errorCount++;
                throw error;
            }
        };
    }

    sendMetrics() {
        // Send performance metrics to server
        if (this.metrics.pageLoadTime > 3000) {
            console.warn('Slow page load detected:', this.metrics.pageLoadTime, 'ms');
        }
        
        // Could send to analytics endpoint
        // fetch('/api/analytics/performance', {
        //     method: 'POST',
        //     headers: { 'Content-Type': 'application/json' },
        //     body: JSON.stringify(this.metrics)
        // });
    }
}

// Image optimization and lazy loading
class ImageOptimizer {
    constructor() {
        this.setupLazyImages();
    }

    setupLazyImages() {
        const images = document.querySelectorAll('img[data-src]');
        
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));
    }
}

// Real-time notifications
class NotificationManager {
    constructor() {
        this.socket = null;
        this.permissions = false;
        this.setupNotifications();
    }

    async setupNotifications() {
        // Request notification permission
        if ('Notification' in window) {
            const permission = await Notification.requestPermission();
            this.permissions = permission === 'granted';
        }

        // Setup WebSocket for real-time updates
        if (typeof io !== 'undefined') {
            this.socket = io();
            this.setupSocketListeners();
        }
    }

    setupSocketListeners() {
        this.socket.on('cheque_alert', (data) => {
            this.showNotification('Alerte Chèque', data.message, 'warning');
        });

        this.socket.on('fraud_detected', (data) => {
            this.showNotification('Fraude Détectée', data.message, 'danger');
        });

        this.socket.on('system_update', (data) => {
            this.showNotification('Mise à jour', data.message, 'info');
        });
    }

    showNotification(title, message, type = 'info') {
        // Browser notification
        if (this.permissions) {
            new Notification(title, {
                body: message,
                icon: '/static/icons/notification.png'
            });
        }

        // In-app notification
        this.showInAppNotification(title, message, type);
    }

    showInAppNotification(title, message, type) {
        const container = document.getElementById('notifications-container') || this.createNotificationContainer();
        
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show notification-item`;
        notification.innerHTML = `
            <strong>${title}</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    createNotificationContainer() {
        const container = document.createElement('div');
        container.id = 'notifications-container';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
        return container;
    }
}

// Initialize performance optimizations when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize lazy loader
    const lazyLoader = new LazyLoader();
    document.querySelectorAll('[data-chart]').forEach(element => {
        lazyLoader.observe(element);
    });

    // Initialize smart search for client/depositor inputs
    const clientSearch = document.getElementById('clientSearch');
    const clientSuggestions = document.getElementById('clientSuggestions');
    if (clientSearch && clientSuggestions) {
        new SmartSearch(clientSearch, clientSuggestions, '/api/clients/search');
    }

    // Initialize performance monitoring
    new PerformanceMonitor();

    // Initialize image optimization
    new ImageOptimizer();

    // Initialize notification manager
    new NotificationManager();
});

// Export classes for use in other modules
window.LazyLoader = LazyLoader;
window.SmartSearch = SmartSearch;
window.PerformanceMonitor = PerformanceMonitor;