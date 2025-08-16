// Analytics functionality for product insights
document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname === '/' || window.location.pathname === '/dashboard') {
        initializeAnalytics();
    }
});

function initializeAnalytics() {
    loadAnalyticsData();
    setupAnalyticsInteractions();
}

async function loadAnalyticsData() {
    try {
        const response = await fetch('/api/analytics-dashboard');
        const analytics = await response.json();
        
        if (window.location.pathname === '/') {
            updateLandingPageAnalytics(analytics);
        } else {
            updateDashboardAnalytics(analytics);
        }
        
    } catch (error) {
        console.error('Failed to load analytics:', error);
        showFallbackAnalytics();
    }
}

function updateLandingPageAnalytics(analytics) {
    // Update conversion metrics in analytics section
    updateConversionBars(analytics.conversion_metrics);
    updateLTVDisplay(analytics.ltv_by_persona);
    updateMarketData(analytics.market_intelligence);
}

function updateConversionBars(conversionMetrics) {
    Object.entries(conversionMetrics).forEach(([persona, data]) => {
        const bar = document.querySelector(`.persona-metric[data-persona="${persona}"] .conversion-fill`);
        if (bar) {
            const rate = parseInt(data.conversion_rate);
            setTimeout(() => {
                bar.style.width = `${rate}%`;
            }, 500);
        }
        
        const rateDisplay = document.querySelector(`.persona-metric[data-persona="${persona}"] .conversion-rate`);
        if (rateDisplay) {
            rateDisplay.textContent = data.conversion_rate;
        }
    });
}

function updateLTVDisplay(ltvData) {
    Object.entries(ltvData).forEach(([persona, data]) => {
        const ltvItem = document.querySelector(`.ltv-item[data-persona="${persona}"]`);
        if (ltvItem) {
            const valueElement = ltvItem.querySelector('.ltv-value');
            const retentionElement = ltvItem.querySelector('.ltv-retention');
            
            if (valueElement) {
                animateValue(valueElement, 0, data.avg_ltv, 1500, '$', ',');
            }
            
            if (retentionElement) {
                retentionElement.textContent = data.retention_12m;
            }
        }
    });
}

function updateMarketData(marketData) {
    const tamElement = document.querySelector('.market-value');
    if (tamElement) {
        tamElement.textContent = marketData.tam;
    }
    
    const growthElement = document.querySelector('.market-growth');
    if (growthElement) {
        growthElement.textContent = `+${marketData.growth_rate} Growth`;
    }
    
    // Update competitive analysis
    const competitorElements = document.querySelectorAll('.competitor');
    competitorElements.forEach(el => {
        if (el.textContent.includes('NexusAI')) {
            el.classList.add('nexus');
        }
    });
}

function updateDashboardAnalytics(analytics) {
    // Update persona metrics cards
    updatePersonaMetricCards(analytics);
    updateBusinessMetrics(analytics);
}

function updatePersonaMetricCards(analytics) {
    const conversionData = analytics.conversion_metrics;
    const ltvData = analytics.ltv_by_persona;
    
    Object.entries(conversionData).forEach(([persona, data]) => {
        const card = document.querySelector(`.persona-metric-card.${persona}`);
        if (card) {
            const stats = card.querySelectorAll('.stat-value');
            if (stats[0]) stats[0].textContent = data.conversion_rate;
            if (stats[1] && ltvData[persona]) {
                const ltv = ltvData[persona].avg_ltv;
                stats[1].textContent = `$${(ltv / 1000).toFixed(1)}K`;
            }
            if (stats[2] && ltvData[persona]) {
                stats[2].textContent = ltvData[persona].retention_12m;
            }
        }
    });
}

function updateBusinessMetrics(analytics) {
    // Simulate business metrics updates
    const metricItems = document.querySelectorAll('.metric-item');
    metricItems.forEach(item => {
        const changeElement = item.querySelector('.metric-change');
        if (changeElement) {
            const isPositive = Math.random() > 0.3;
            const change = Math.floor(Math.random() * 20) + 5;
            
            changeElement.textContent = `${isPositive ? '+' : '-'}${change}% MoM`;
            changeElement.className = `metric-change ${isPositive ? 'positive' : 'negative'}`;
        }
    });
}

function setupAnalyticsInteractions() {
    // Add hover effects to analytics cards
    const analyticsCards = document.querySelectorAll('.analytics-card, .persona-metric-card');
    analyticsCards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-2px)';
            card.style.boxShadow = '0 10px 25px -5px rgb(0 0 0 / 0.1)';
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
            card.style.boxShadow = '';
        });
    });
    
    // Add click tracking to persona options
    const personaOptions = document.querySelectorAll('.persona-option');
    personaOptions.forEach(option => {
        option.addEventListener('click', () => {
            trackPersonaSelection(option.dataset.persona);
        });
    });
}

function animateValue(element, start, end, duration, prefix = '', suffix = '', useComma = false) {
    const range = end - start;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const current = Math.floor(start + (range * progress));
        
        let value = current;
        if (useComma) {
            value = current.toLocaleString();
        }
        
        element.textContent = prefix + value + suffix;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

function showFallbackAnalytics() {
    // Show static analytics if API fails
    const fallbackData = {
        conversion_metrics: {
            entrepreneur: { conversion_rate: '31%' },
            consultant: { conversion_rate: '35%' },
            seller: { conversion_rate: '25%' }
        },
        ltv_by_persona: {
            entrepreneur: { avg_ltv: 12000, retention_12m: '78%' },
            consultant: { avg_ltv: 8500, retention_12m: '82%' },
            seller: { avg_ltv: 4200, retention_12m: '65%' }
        },
        market_intelligence: {
            tam: '$12.3B',
            growth_rate: '34% YoY'
        }
    };
    
    if (window.location.pathname === '/') {
        updateLandingPageAnalytics(fallbackData);
    } else {
        updateDashboardAnalytics(fallbackData);
    }
}

function trackPersonaSelection(persona) {
    // Analytics tracking
    console.log('Persona selected:', persona);
    
    // Update persona-specific messaging
    updatePersonaMessaging(persona);
    
    // Track in localStorage for session
    localStorage.setItem('selected_persona', persona);
}

function updatePersonaMessaging(persona) {
    const messages = {
        entrepreneur: {
            cta: 'Get Investor-Ready',
            focus: 'fundraising advantage'
        },
        consultant: {
            cta: 'Assess Client Risk',
            focus: 'liability protection'
        },
        seller: {
            cta: 'Enable Enterprise Sales',
            focus: 'sales acceleration'
        }
    };
    
    const message = messages[persona];
    if (message) {
        const ctaButton = document.getElementById('startAssessment');
        if (ctaButton) {
            ctaButton.textContent = message.cta;
        }
    }
}

// A/B Testing Functions
function initializeABTests() {
    // Simulate A/B test for CTA buttons
    const isVariantB = Math.random() > 0.5;
    
    if (isVariantB) {
        const ctaButtons = document.querySelectorAll('.btn-primary');
        ctaButtons.forEach(btn => {
            if (btn.textContent.includes('Assessment')) {
                btn.textContent = btn.textContent.replace('Assessment', 'Analysis');
                btn.setAttribute('data-variant', 'b');
            }
        });
        
        trackABTest('cta_text', 'variant_b');
    } else {
        trackABTest('cta_text', 'control');
    }
}

function trackABTest(testName, variant) {
    // Track A/B test participation
    localStorage.setItem(`ab_test_${testName}`, variant);
    console.log('A/B Test:', testName, variant);
}

// Product Analytics Events
function trackEvent(eventName, properties = {}) {
    const eventData = {
        event: eventName,
        properties: {
            ...properties,
            timestamp: new Date().toISOString(),
            url: window.location.href,
            user_agent: navigator.userAgent
        }
    };
    
    // In production, send to analytics service
    console.log('Analytics Event:', eventData);
    
    // Store locally for demo purposes
    const events = JSON.parse(localStorage.getItem('analytics_events') || '[]');
    events.push(eventData);
    localStorage.setItem('analytics_events', JSON.stringify(events.slice(-100))); // Keep last 100 events
}

// User Journey Tracking
function trackUserJourney() {
    const journey = JSON.parse(localStorage.getItem('user_journey') || '[]');
    
    const step = {
        page: window.location.pathname,
        timestamp: new Date().toISOString(),
        persona: localStorage.getItem('selected_persona')
    };
    
    journey.push(step);
    localStorage.setItem('user_journey', JSON.stringify(journey.slice(-20))); // Keep last 20 steps
}

// Conversion Funnel Tracking
function trackFunnelStep(step) {
    const funnel = JSON.parse(localStorage.getItem('conversion_funnel') || '{}');
    funnel[step] = new Date().toISOString();
    localStorage.setItem('conversion_funnel', JSON.stringify(funnel));
    
    trackEvent('funnel_step', { step });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    trackUserJourney();
    
    if (window.location.pathname === '/') {
        initializeABTests();
        trackFunnelStep('landing_page_view');
    } else if (window.location.pathname === '/wizard') {
        trackFunnelStep('wizard_start');
    } else if (window.location.pathname === '/dashboard') {
        trackFunnelStep('dashboard_view');
    }
});

// Export analytics functions
window.Analytics = {
    trackEvent,
    trackPersonaSelection,
    trackFunnelStep,
    trackUserJourney,
    updatePersonaMessaging
};
