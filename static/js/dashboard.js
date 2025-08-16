// Dashboard functionality with product analytics
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupFormHandlers();
    loadAnalytics();
});

function initializeDashboard() {
    updatePersonaMetrics();
    animateMetrics();
    
    // Check if we should show pricing panel from wizard
    if (localStorage.getItem('showPricing') === 'true') {
        localStorage.removeItem('showPricing');
        setTimeout(() => viewPricingStrategy(), 500);
    }
}

function setupFormHandlers() {
    const assessmentForm = document.getElementById('quickAssessmentForm');
    if (assessmentForm) {
        assessmentForm.addEventListener('submit', handleQuickAssessment);
    }
    
    const demoToggle = document.getElementById('useDemoData');
    if (demoToggle) {
        demoToggle.addEventListener('change', toggleDemoFields);
    }
}

async function loadAnalytics() {
    try {
        const response = await fetch('/api/analytics-dashboard');
        const analytics = await response.json();
        
        updateConversionMetrics(analytics.conversion_metrics);
        updateLTVMetrics(analytics.ltv_by_persona);
        updateMarketIntelligence(analytics.market_intelligence);
        
    } catch (error) {
        console.error('Failed to load analytics:', error);
    }
}

function updatePersonaMetrics() {
    // Animate persona metric cards
    const metricCards = document.querySelectorAll('.persona-metric-card');
    metricCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 200);
    });
}

function animateMetrics() {
    // Animate conversion bars
    const conversionBars = document.querySelectorAll('.conversion-fill');
    conversionBars.forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(() => {
            bar.style.width = width;
        }, 500);
    });
    
    // Animate numbers
    const statValues = document.querySelectorAll('.stat-value');
    statValues.forEach(stat => {
        const text = stat.textContent;
        const number = parseInt(text.replace(/\D/g, ''));
        if (number) {
            animateNumber(stat, 0, number, 1000, text.includes('K') ? 'K' : text.includes('%') ? '%' : '');
        }
    });
}

function animateNumber(element, start, end, duration, suffix = '') {
    const range = end - start;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const current = Math.floor(start + (range * progress));
        
        element.textContent = current.toLocaleString() + suffix;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

function updateConversionMetrics(metrics) {
    Object.entries(metrics).forEach(([persona, data]) => {
        const card = document.querySelector(`.persona-metric-card.${persona}`);
        if (card) {
            const conversionRate = card.querySelector('.stat-value');
            if (conversionRate) {
                conversionRate.textContent = data.conversion_rate;
            }
        }
    });
}

function updateLTVMetrics(ltvData) {
    Object.entries(ltvData).forEach(([persona, data]) => {
        const card = document.querySelector(`.persona-metric-card.${persona}`);
        if (card) {
            const ltvValue = card.querySelectorAll('.stat-value')[1];
            const retentionValue = card.querySelectorAll('.stat-value')[2];
            
            if (ltvValue) ltvValue.textContent = `$${(data.avg_ltv / 1000).toFixed(1)}K`;
            if (retentionValue) retentionValue.textContent = data.retention_12m;
        }
    });
}

function updateMarketIntelligence(marketData) {
    // Update market position metrics if elements exist
    const tamElement = document.querySelector('.market-value');
    if (tamElement) {
        tamElement.textContent = marketData.tam;
    }
}

async function handleQuickAssessment(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    showLoading('loadingOverlay');
    
    try {
        data.use_demo = document.getElementById('useDemoData').checked;
        data.persona = data.persona || 'entrepreneur';
        
        if (data.use_demo) {
            data.demo_type = data.persona;
        }
        
        const result = await makeAPICall('/api/analyze', data, 'POST');
        
        hideLoading('loadingOverlay');
        displayPersonaResults(result, data.persona);
        
        // Track analytics event
        trackAnalyticsEvent('quick_assessment', {
            persona: data.persona,
            industry: data.industry,
            demo_mode: data.use_demo
        });
        
    } catch (error) {
        hideLoading('loadingOverlay');
        showNotification('Analysis failed. Please try again.', 'error');
        console.error('Analysis error:', error);
    }
}

function displayPersonaResults(analysis, persona) {
    const resultsPanel = document.getElementById('resultsPanel');
    const personaResult = document.getElementById('personaResult');
    
    if (!resultsPanel || !personaResult) return;
    
    window.NexusAI.setAnalysis(analysis);
    window.NexusAI.setPersona(persona);
    
    const riskData = analysis.risk_assessment || {};
    const personaInsights = analysis.persona_insights || {};
    const demoData = analysis.demo_data || {};
    
    personaResult.innerHTML = createPersonaResultHTML(riskData, personaInsights, demoData, persona);
    
    resultsPanel.style.display = 'block';
    resultsPanel.scrollIntoView({ behavior: 'smooth' });
}

function createPersonaResultHTML(riskData, insights, demoData, persona) {
    const personaConfig = {
        entrepreneur: {
            icon: '🚀',
            title: 'Entrepreneur Analysis',
            focus: 'Investor Readiness',
            color: '#059669'
        },
        consultant: {
            icon: '🎯',
            title: 'Consultant Analysis', 
            focus: 'Client Risk Assessment',
            color: '#ea580c'
        },
        seller: {
            icon: '💼',
            title: 'Seller Analysis',
            focus: 'Sales Enablement',
            color: '#8b5cf6'
        }
    };
    
    const config = personaConfig[persona] || personaConfig.entrepreneur;
    
    return `
        <div class="persona-result-header">
            <div class="persona-icon" style="background: ${config.color}20; color: ${config.color}">
                ${config.icon}
            </div>
            <div class="persona-info">
                <h3>${config.title}</h3>
                <p>${config.focus}</p>
            </div>
        </div>
        
        <div class="risk-display">
            <div class="risk-meter">
                <div class="risk-score" style="border-color: ${riskData.status_color}; color: ${riskData.status_color}">
                    ${riskData.risk_score || '--'}
                </div>
                <div class="risk-label">Risk Score</div>
            </div>
            <div class="compliance-meter">
                <div class="compliance-score" style="border-color: #10b981; color: #10b981">
                    ${riskData.compliance_score || '--'}
                </div>
                <div class="compliance-label">Compliance Score</div>
            </div>
        </div>
        
        <div class="persona-insights">
            <h4>Key Insights for ${config.title.split(' ')[0]}s</h4>
            <div class="insights-grid">
                ${Object.entries(insights).map(([key, value]) => `
                    <div class="insight-item">
                        <span class="insight-label">${formatInsightLabel(key)}:</span>
                        <span class="insight-value">${value}</span>
                    </div>
                `).join('')}
            </div>
        </div>
        
        ${demoData.name ? `
            <div class="demo-context">
                <h4>Demo Scenario: ${demoData.name}</h4>
                <p>${demoData.industry} - ${demoData.type}</p>
            </div>
        ` : ''}
    `;
}

function formatInsightLabel(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function toggleDemoFields(e) {
    const isDemo = e.target.checked;
    const form = e.target.closest('form');
    const inputs = form.querySelectorAll('input:not([type="checkbox"]), select');
    
    inputs.forEach(input => {
        if (isDemo) {
            input.style.backgroundColor = '#fef3c7';
            input.style.border = '2px solid #f59e0b';
        } else {
            input.style.backgroundColor = '';
            input.style.border = '';
        }
    });
}

async function downloadReport() {
    const analysis = window.NexusAI.getAnalysis();
    const persona = window.NexusAI.getPersona();
    
    if (!analysis) {
        showNotification('Please run an analysis first', 'warning');
        return;
    }
    
    try {
        showNotification('Generating comprehensive report...', 'info');
        
        const response = await fetch('/api/generate-report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                analysis_data: analysis,
                company_name: 'Demo Company',
                persona: persona
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to generate report');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `NexusAI_${persona}_Report_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showNotification('Report downloaded successfully!', 'success');
        
        // Track download event
        trackAnalyticsEvent('report_download', { persona });
        
    } catch (error) {
        showNotification('Failed to download report', 'error');
        console.error('Report download error:', error);
    }
}

function viewFullDashboard() {
    // Scroll to show full dashboard insights
    document.querySelector('.persona-analytics').scrollIntoView({ 
        behavior: 'smooth' 
    });
}

function viewPricingStrategy() {
    showNotification('Pricing strategy feature coming soon', 'info');
}

function startNewAssessment() {
    window.location.href = '/wizard';
}

function trackAnalyticsEvent(eventName, properties = {}) {
    // In a real app, this would send to analytics service
    console.log('Analytics Event:', eventName, properties);
    
    // Simulate incrementing dashboard metrics
    if (eventName === 'quick_assessment') {
        updateAssessmentCount();
    }
}

function updateAssessmentCount() {
    // Simulate real-time metric updates
    const statCards = document.querySelectorAll('.persona-metric-card');
    statCards.forEach(card => {
        const conversionElement = card.querySelector('.stat-value');
        if (conversionElement && conversionElement.textContent.includes('%')) {
            const currentValue = parseInt(conversionElement.textContent);
            const newValue = Math.min(40, currentValue + Math.floor(Math.random() * 2));
            conversionElement.textContent = newValue + '%';
        }
    });
}

// Global functions for buttons
window.downloadReport = downloadReport;
window.viewFullDashboard = viewFullDashboard;
window.viewPricingStrategy = viewPricingStrategy;
window.startNewAssessment = startNewAssessment;

// Initialize CSS animations
const dashboardStyle = document.createElement('style');
dashboardStyle.textContent = `
    .persona-metric-card {
        opacity: 0;
        transform: translateY(20px);
        transition: all 0.6s ease;
    }
    
    .persona-result-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: var(--gray-50);
        border-radius: 0.75rem;
    }
    
    .persona-icon {
        width: 48px;
        height: 48px;
        border-radius: 0.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
    }
    
    .persona-info h3 {
        margin: 0 0 0.25rem 0;
        color: var(--gray-800);
    }
    
    .persona-info p {
        margin: 0;
        color: var(--gray-600);
        font-size: 0.875rem;
    }
    
    .persona-insights {
        margin-top: 1.5rem;
        padding: 1rem;
        background: var(--gray-50);
        border-radius: 0.75rem;
    }
    
    .insights-grid {
        display: grid;
        gap: 0.75rem;
        margin-top: 1rem;
    }
    
    .insight-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem;
        background: white;
        border-radius: 0.5rem;
        border: 1px solid var(--gray-200);
    }
    
    .insight-label {
        font-weight: 500;
        color: var(--gray-700);
    }
    
    .insight-value {
        color: var(--primary);
        font-weight: 600;
    }
    
    .demo-context {
        margin-top: 1rem;
        padding: 1rem;
        background: #fffbeb;
        border: 1px solid #f59e0b;
        border-radius: 0.75rem;
    }
    
    .demo-context h4 {
        margin: 0 0 0.5rem 0;
        color: var(--amber);
    }
    
    .demo-context p {
        margin: 0;
        color: var(--gray-700);
        font-size: 0.875rem;
    }
`;
document.head.appendChild(dashboardStyle);
