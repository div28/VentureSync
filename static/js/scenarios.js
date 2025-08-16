// Scenarios carousel functionality
let currentScenarioIndex = 0;
let scenarios = [];
let currentPersona = 'entrepreneur';
let scenarioInterval;

document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('scenarioCarousel')) {
        loadDemoScenarios();
        initializeCarouselControls();
        initializePersonaTabs();
    }
});

async function loadDemoScenarios() {
    try {
        const response = await fetch('/api/demo-scenarios');
        const data = await response.json();
        
        // Store all scenarios by persona
        window.allScenarios = data;
        
        // Load entrepreneur scenarios by default
        loadPersonaScenarios('entrepreneur');
        
    } catch (error) {
        console.error('Failed to load demo scenarios:', error);
        loadFallbackScenarios();
    }
}

function loadPersonaScenarios(persona) {
    currentPersona = persona;
    scenarios = window.allScenarios[persona] || [];
    currentScenarioIndex = 0;
    
    renderScenarios();
    updatePersonaTabs();
    
    if (scenarios.length > 0) {
        startCarouselAutoplay();
    }
}

function initializePersonaTabs() {
    const tabs = document.querySelectorAll('.persona-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const persona = tab.dataset.persona;
            loadPersonaScenarios(persona);
        });
    });
}

function updatePersonaTabs() {
    const tabs = document.querySelectorAll('.persona-tab');
    tabs.forEach(tab => {
        tab.classList.toggle('active', tab.dataset.persona === currentPersona);
    });
}

function loadFallbackScenarios() {
    window.allScenarios = {
        entrepreneur: [
            {
                name: "TechStart Pro",
                type: "AI Startup - Series A",
                industry: "B2B SaaS",
                ai_system: "Sales lead scoring with anonymized data",
                risk_level: "LOW",
                risk_score: 25,
                compliance_score: 92,
                potential_fines: "$15,000",
                status: "✅ Investor Ready",
                key_strengths: ["GDPR compliant", "SOC2 certified", "Clear data policies"],
                funding_advantage: "78% higher Series A success"
            }
        ],
        consultant: [
            {
                name: "QuickHire AI Client",
                type: "HR Tech Prospect",
                industry: "Human Resources",
                ai_system: "AI hiring tool with bias issues",
                risk_level: "CRITICAL",
                risk_score: 95,
                compliance_score: 15,
                potential_fines: "$4,200,000",
                status: "🚨 Avoid Client",
                key_risks: ["EEOC violations", "Discriminatory AI", "No bias testing"],
                lawsuit_probability: "73% violation rate"
            }
        ],
        seller: [
            {
                name: "FinanceBot Inc",
                type: "FinTech SMB",
                industry: "Financial Services",
                ai_system: "Investment advice chatbot",
                risk_level: "MEDIUM",
                risk_score: 55,
                compliance_score: 68,
                potential_fines: "$350,000",
                status: "⚠️ Education Needed",
                key_gaps: ["SEC registration", "Fiduciary duties", "Risk disclosures"],
                client_education: "Compliance training required"
            }
        ]
    };
    
    loadPersonaScenarios('entrepreneur');
}

function renderScenarios() {
    const carousel = document.getElementById('scenarioCarousel');
    const indicators = document.getElementById('carouselIndicators');
    
    if (!carousel || !indicators) return;
    
    // Clear existing content
    carousel.innerHTML = '';
    indicators.innerHTML = '';
    
    // Render scenario cards
    scenarios.forEach((scenario, index) => {
        const card = createScenarioCard(scenario, index);
        carousel.appendChild(card);
        
        // Create indicator
        const indicator = document.createElement('div');
        indicator.className = `indicator ${index === 0 ? 'active' : ''}`;
        indicator.addEventListener('click', () => goToScenario(index));
        indicators.appendChild(indicator);
    });
    
    updateCarouselPosition();
}

function createScenarioCard(scenario, index) {
    const card = document.createElement('div');
    card.className = 'scenario-card';
    
    const statusClass = getStatusClass(scenario.status);
    const highlights = getPersonaHighlights(scenario, currentPersona);
    
    card.innerHTML = `
        <div class="scenario-header">
            <h3 class="scenario-title">${scenario.name}</h3>
            <span class="scenario-status ${statusClass}">${scenario.status}</span>
        </div>
        
        <div class="scenario-content">
            <div class="scenario-info">
                <h4>Company Type</h4>
                <p>${scenario.type}</p>
                
                <h4>Industry</h4>
                <p>${scenario.industry}</p>
                
                <h4>AI System</h4>
                <p>${scenario.ai_system}</p>
                
                ${highlights.html}
            </div>
            
            <div class="scenario-metrics">
                <div class="metric">
                    <div class="metric-value risk" style="color: ${getScoreColor(scenario.risk_score)}">${scenario.risk_score}</div>
                    <div class="metric-label">Risk Score</div>
                </div>
                <div class="metric">
                    <div class="metric-value compliance" style="color: ${getScoreColor(100 - scenario.risk_score)}">${scenario.compliance_score}</div>
                    <div class="metric-label">Compliance</div>
                </div>
            </div>
        </div>
        
        <div class="scenario-footer">
            <div class="scenario-impact">
                <strong>${highlights.impactLabel}:</strong> ${highlights.impactValue}
            </div>
            <button class="btn-primary" onclick="analyzeScenario(${index})">
                <i class="fas fa-search"></i> ${highlights.ctaText}
            </button>
        </div>
    `;
    
    return card;
}

function getPersonaHighlights(scenario, persona) {
    switch(persona) {
        case 'entrepreneur':
            return {
                html: `
                    <h4>Investor Impact</h4>
                    <p>${scenario.funding_advantage || scenario.investor_confidence || 'Impacts fundraising potential'}</p>
                `,
                impactLabel: 'Fundraising Impact',
                impactValue: scenario.funding_advantage || scenario.investor_confidence || 'Variable',
                ctaText: 'Analyze for Investors'
            };
        case 'consultant':
            return {
                html: `
                    <h4>Liability Risk</h4>
                    <p>${scenario.lawsuit_probability || scenario.protection_needed || 'Client liability assessment'}</p>
                `,
                impactLabel: 'Lawsuit Risk',
                impactValue: scenario.lawsuit_probability || scenario.potential_fines,
                ctaText: 'Assess Client Risk'
            };
        case 'seller':
            return {
                html: `
                    <h4>Sales Impact</h4>
                    <p>${scenario.client_education || scenario.liability_protection || 'Client education needs'}</p>
                `,
                impactLabel: 'Sales Impact',
                impactValue: scenario.client_education || 'Client education required',
                ctaText: 'Analyze for Sales'
            };
        default:
            return {
                html: '<h4>Key Concerns</h4><p>Analysis available</p>',
                impactLabel: 'Impact',
                impactValue: 'Various',
                ctaText: 'Analyze Scenario'
            };
    }
}

function getStatusClass(status) {
    if (status.includes('✅') || status.includes('Ready') || status.includes('Compliant')) {
        return 'compliant';
    } else if (status.includes('🚨') || status.includes('Critical') || status.includes('Avoid')) {
        return 'non-compliant';
    } else {
        return 'partial';
    }
}

function getScoreColor(score) {
    if (score >= 80) return '#10b981';
    if (score >= 60) return '#f59e0b';
    if (score >= 40) return '#ea580c';
    return '#dc2626';
}

function initializeCarouselControls() {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            stopCarouselAutoplay();
            previousScenario();
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            stopCarouselAutoplay();
            nextScenario();
        });
    }
    
    // Touch/swipe support
    let startX = 0;
    const carousel = document.getElementById('scenarioCarousel');
    
    if (carousel) {
        carousel.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
        });
        
        carousel.addEventListener('touchend', (e) => {
            const endX = e.changedTouches[0].clientX;
            const deltaX = startX - endX;
            
            if (Math.abs(deltaX) > 50) {
                stopCarouselAutoplay();
                if (deltaX > 0) {
                    nextScenario();
                } else {
                    previousScenario();
                }
            }
        });
    }
}

function goToScenario(index) {
    currentScenarioIndex = index;
    updateCarouselPosition();
    updateIndicators();
}

function nextScenario() {
    currentScenarioIndex = (currentScenarioIndex + 1) % scenarios.length;
    updateCarouselPosition();
    updateIndicators();
}

function previousScenario() {
    currentScenarioIndex = (currentScenarioIndex - 1 + scenarios.length) % scenarios.length;
    updateCarouselPosition();
    updateIndicators();
}

function updateCarouselPosition() {
    const carousel = document.getElementById('scenarioCarousel');
    if (carousel && scenarios.length > 0) {
        const translateX = -currentScenarioIndex * 100;
        carousel.style.transform = `translateX(${translateX}%)`;
    }
}

function updateIndicators() {
    const indicators = document.querySelectorAll('.indicator');
    indicators.forEach((indicator, index) => {
        indicator.classList.toggle('active', index === currentScenarioIndex);
    });
}

function startCarouselAutoplay() {
    stopCarouselAutoplay(); // Clear any existing interval
    
    if (scenarios.length > 1) {
        scenarioInterval = setInterval(() => {
            nextScenario();
        }, 6000); // Change scenario every 6 seconds
    }
}

function stopCarouselAutoplay() {
    if (scenarioInterval) {
        clearInterval(scenarioInterval);
        scenarioInterval = null;
    }
}

async function analyzeScenario(index) {
    const scenario = scenarios[index];
    
    showNotification('Loading scenario analysis...', 'info');
    
    try {
        // Store selected scenario and persona
        sessionStorage.setItem('selectedScenario', JSON.stringify(scenario));
        sessionStorage.setItem('selectedPersona', currentPersona);
        
        // Navigate to wizard with pre-filled data
        const params = new URLSearchParams({
            demo: 'true',
            persona: currentPersona,
            scenario: scenario.name
        });
        
        window.location.href = `/wizard?${params.toString()}`;
        
    } catch (error) {
        console.error('Failed to analyze scenario:', error);
        showNotification('Failed to load scenario analysis', 'error');
    }
}

// Pause autoplay when tab is not visible
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        stopCarouselAutoplay();
    } else {
        startCarouselAutoplay();
    }
});

// Export functions for use in other modules
window.ScenarioCarousel = {
    loadDemoScenarios,
    loadPersonaScenarios,
    goToScenario,
    nextScenario,
    previousScenario,
    analyzeScenario
};
