// Wizard functionality with persona optimization
let currentStep = 1;
let totalSteps = 4;
let wizardData = {};
let selectedPersona = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeWizard();
    setupWizardNavigation();
    loadURLParameters();
});

function initializeWizard() {
    updateProgress();
    setupPersonaSelection();
    setupFormValidation();
    
    // Load saved data if available
    loadSavedWizardData();
}

function loadURLParameters() {
    const params = new URLSearchParams(window.location.search);
    const persona = params.get('persona');
    const isDemo = params.get('demo');
    const scenarioName = params.get('scenario');
    
    if (persona) {
        selectedPersona = persona;
        wizardData.persona = persona;
        
        // Auto-select persona and advance
        setTimeout(() => {
            selectPersona(persona);
            if (isDemo) {
                loadDemoScenario(scenarioName);
            }
        }, 500);
    }
}

function loadDemoScenario(scenarioName) {
    const savedScenario = sessionStorage.getItem('selectedScenario');
    if (savedScenario) {
        try {
            const scenario = JSON.parse(savedScenario);
            prefillWizardFromScenario(scenario);
        } catch (error) {
            console.error('Failed to load saved scenario:', error);
        }
    }
}

function prefillWizardFromScenario(scenario) {
    wizardData = {
        ...wizardData,
        company_name: scenario.name,
        industry: scenario.industry.toLowerCase(),
        ai_description: scenario.ai_system,
        demo_scenario: scenario
    };
    
    // Auto-advance after a short delay
    setTimeout(() => {
        if (currentStep === 1) {
            nextStep();
        }
    }, 1000);
}

function setupPersonaSelection() {
    const personaCards = document.querySelectorAll('.persona-card');
    personaCards.forEach(card => {
        card.addEventListener('click', () => {
            const persona = card.dataset.persona;
            selectPersona(persona);
        });
    });
}

function selectPersona(persona) {
    document.querySelectorAll('.persona-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    const selectedCard = document.querySelector(`[data-persona="${persona}"]`);
    if (selectedCard) {
        selectedCard.classList.add('selected');
    }
    
    selectedPersona = persona;
    wizardData.persona = persona;
    
    // Update guidance for next steps
    updatePersonaGuidance(persona);
    
    // Enable next button
    const nextBtn = document.getElementById('nextBtn');
    if (nextBtn) {
        nextBtn.disabled = false;
    }
}

function updatePersonaGuidance(persona) {
    const guidanceConfig = {
        entrepreneur: {
            step2: "As an AI entrepreneur, we'll focus on how compliance can accelerate your fundraising and demonstrate investor readiness.",
            step3: "We'll analyze your AI system for investor appeal and regulatory positioning that VCs care about."
        },
        consultant: {
            step2: "As an AI consultant, we'll focus on assessing client liability risks and protecting your business from legal exposure.",
            step3: "We'll evaluate the compliance risks this client brings and recommend contract protections."
        },
        seller: {
            step2: "As an SMB AI seller, we'll focus on how compliance can enable enterprise sales and differentiate your offering.",
            step3: "We'll analyze how to position your AI solution to compliance-conscious enterprise buyers."
        }
    };
    
    const config = guidanceConfig[persona];
    if (config) {
        const step2Guidance = document.querySelector('#step2 .persona-guidance');
        const step3Guidance = document.querySelector('#step3 .persona-guidance');
        
        if (step2Guidance) {
            step2Guidance.innerHTML = `<i class="fas fa-lightbulb"></i> ${config.step2}`;
            step2Guidance.style.display = 'block';
        }
        
        if (step3Guidance) {
            step3Guidance.innerHTML = `<i class="fas fa-lightbulb"></i> ${config.step3}`;
            step3Guidance.style.display = 'block';
        }
    }
}

function setupFormValidation() {
    const forms = document.querySelectorAll('.wizard-form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        inputs.forEach(input => {
            input.addEventListener('change', validateCurrentStep);
            input.addEventListener('blur', validateCurrentStep);
        });
    });
}

function setupWizardNavigation() {
    const nextBtn = document.getElementById('nextBtn');
    const prevBtn = document.getElementById('prevBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    if (nextBtn) {
        nextBtn.addEventListener('click', nextStep);
    }
    
    if (prevBtn) {
        prevBtn.addEventListener('click', previousStep);
    }
    
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', runAnalysis);
    }
}

function nextStep() {
    if (!validateCurrentStep()) {
        showNotification('Please complete all required fields', 'warning');
        return;
    }
    
    collectCurrentStepData();
    
    if (currentStep < totalSteps) {
        currentStep++;
        updateWizardDisplay();
        updateProgress();
        
        // Auto-fill demo data if available
        if (wizardData.demo_scenario) {
            autoFillDemoData();
        }
    }
}

function previousStep() {
    if (currentStep > 1) {
        currentStep--;
        updateWizardDisplay();
        updateProgress();
    }
}

function updateWizardDisplay() {
    // Hide all steps
    document.querySelectorAll('.wizard-step').forEach(step => {
        step.classList.remove('active');
    });
    
    // Show current step
    const currentStepElement = document.getElementById(`step${currentStep}`);
    if (currentStepElement) {
        currentStepElement.classList.add('active');
    }
    
    // Update navigation buttons
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    if (prevBtn) {
        prevBtn.style.display = currentStep > 1 ? 'block' : 'none';
    }
    
    if (nextBtn) {
        nextBtn.style.display = currentStep < totalSteps ? 'block' : 'none';
    }
    
    if (analyzeBtn) {
        analyzeBtn.style.display = currentStep === 3 ? 'block' : 'none';
    }
}

function autoFillDemoData() {
    const scenario = wizardData.demo_scenario;
    if (!scenario) return;
    
    if (currentStep === 2) {
        // Fill company details
        const form = document.querySelector('#step2 .wizard-form');
        if (form) {
            const companyName = form.querySelector('[name="company_name"]');
            const industry = form.querySelector('[name="industry"]');
            
            if (companyName && !companyName.value) {
                companyName.value = scenario.name;
                companyName.style.background = '#fef3c7';
            }
            
            if (industry && !industry.value) {
                industry.value = scenario.industry.toLowerCase();
                industry.style.background = '#fef3c7';
            }
        }
    } else if (currentStep === 3) {
        // Fill AI system details
        const form = document.querySelector('#step3 .wizard-form');
        if (form) {
            const aiDescription = form.querySelector('[name="ai_description"]');
            
            if (aiDescription && !aiDescription.value) {
                aiDescription.value = scenario.ai_system;
                aiDescription.style.background = '#fef3c7';
            }
        }
    }
}

function validateCurrentStep() {
    const currentStepElement = document.getElementById(`step${currentStep}`);
    if (!currentStepElement) return true;
    
    if (currentStep === 1) {
        return selectedPersona != null;
    }
    
    const requiredFields = currentStepElement.querySelectorAll('[required]');
    for (let field of requiredFields) {
        if (!field.value.trim()) {
            field.focus();
            field.style.borderColor = '#dc2626';
            return false;
        } else {
            field.style.borderColor = '';
        }
    }
    
    return true;
}

function collectCurrentStepData() {
    const currentStepElement = document.getElementById(`step${currentStep}`);
    if (!currentStepElement) return;
    
    const form = currentStepElement.querySelector('.wizard-form');
    if (!form) return;
    
    const formData = new FormData(form);
    
    // Handle checkboxes
    const checkboxes = form.querySelectorAll('input[type="checkbox"]:checked');
    const checkboxData = {};
    
    checkboxes.forEach(checkbox => {
        const name = checkbox.name;
        if (!checkboxData[name]) {
            checkboxData[name] = [];
        }
        checkboxData[name].push(checkbox.value);
    });
    
    // Merge form data
    for (let [key, value] of formData.entries()) {
        if (!key.includes('checkbox')) {
            wizardData[key] = value;
        }
    });
    
    // Add checkbox data
    Object.keys(checkboxData).forEach(key => {
        wizardData[key] = checkboxData[key];
    });
    
    // Save to localStorage
    saveWizardData();
}

function updateProgress() {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    const progressPercent = ((currentStep - 1) / (totalSteps - 1)) * 100;
    
    if (progressFill) {
        progressFill.style.width = `${progressPercent}%`;
    }
    
    if (progressText) {
        progressText.textContent = `Step ${currentStep} of ${totalSteps}`;
    }
}

async function runAnalysis() {
    collectCurrentStepData();
    
    // Move to results step
    currentStep = 4;
    updateWizardDisplay();
    updateProgress();
    
    showAnalysisLoading();
    
    try {
        const analysisData = {
            ...wizardData,
            use_demo: !!wizardData.demo_scenario,
            persona: selectedPersona
        };
        
        if (analysisData.use_demo) {
            analysisData.demo_type = selectedPersona;
        }
        
        await simulateAnalysisSteps();
        
        const result = await makeAPICall('/api/analyze', analysisData, 'POST');
        
        displayWizardResults(result);
        
        // Track completion
        trackWizardCompletion(selectedPersona);
        
    } catch (error) {
        console.error('Analysis failed:', error);
        showAnalysisError(error);
    }
}

async function simulateAnalysisSteps() {
    const steps = document.querySelectorAll('.analysis-step');
    
    for (let i = 0; i < steps.length; i++) {
        steps.forEach(step => step.classList.remove('active'));
        steps[i].classList.add('active');
        await new Promise(resolve => setTimeout(resolve, 1200));
    }
}

function showAnalysisLoading() {
    const loading = document.getElementById('analysisLoading');
    const results = document.getElementById('analysisResults');
    
    if (loading) loading.style.display = 'block';
    if (results) results.style.display = 'none';
}

function displayWizardResults(analysis) {
    const loading = document.getElementById('analysisLoading');
    const results = document.getElementById('analysisResults');
    
    if (loading) loading.style.display = 'none';
    if (!results) return;
    
    window.NexusAI.setAnalysis(analysis);
    
    const riskData = analysis.risk_assessment || {};
    const personaMessage = document.getElementById('personaSpecificMessage');
    
    if (personaMessage) {
        personaMessage.innerHTML = getPersonaSpecificMessage(selectedPersona, riskData);
    }
    
    const summaryDiv = document.getElementById('resultsSummary');
    if (summaryDiv) {
        summaryDiv.innerHTML = createResultsSummary(analysis, selectedPersona);
    }
    
    results.style.display = 'block';
    
    // Clear saved data on successful completion
    clearSavedWizardData();
}

function getPersonaSpecificMessage(persona, riskData) {
    const messages = {
        entrepreneur: `
            <div class="persona-message entrepreneur">
                <i class="fas fa-rocket"></i>
                <p>Your AI system has been analyzed for investor readiness and fundraising impact. 
                   Compliance score of <strong>${riskData.compliance_score || 'N/A'}%</strong> 
                   ${riskData.compliance_score >= 85 ? 'exceeds VC expectations' : 'needs improvement for optimal VC appeal'}.</p>
            </div>
        `,
        consultant: `
            <div class="persona-message consultant">
                <i class="fas fa-shield-alt"></i>
                <p>Client liability assessment complete. Risk level: <strong>${riskData.risk_level || 'Unknown'}</strong>. 
                   ${riskData.risk_level === 'CRITICAL' ? 'Recommend avoiding this engagement' : 
                     riskData.risk_level === 'HIGH' ? 'Require enhanced contract protections' : 
                     'Standard engagement terms acceptable'}.</p>
            </div>
        `,
        seller: `
            <div class="persona-message seller">
                <i class="fas fa-chart-line"></i>
                <p>Sales enablement analysis complete. Compliance readiness: <strong>${riskData.compliance_score || 'N/A'}%</strong>. 
                   ${riskData.compliance_score >= 70 ? 'Ready for enterprise sales' : 'Client education recommended before enterprise pitches'}.</p>
            </div>
        `
    };
    
    return messages[persona] || messages.entrepreneur;
}

function createResultsSummary(analysis, persona) {
    const riskData = analysis.risk_assessment || {};
    const insights = analysis.persona_insights || {};
    
    return `
        <div class="results-grid">
            <div class="result-scores">
                <div class="score-card">
                    <div class="score-value" style="color: ${riskData.status_color || '#dc2626'}">
                        ${riskData.risk_score || '--'}
                    </div>
                    <div class="score-label">Risk Score</div>
                    <div class="score-status">${riskData.risk_level || 'Unknown'} Risk</div>
                </div>
                <div class="score-card">
                    <div class="score-value" style="color: #10b981">
                        ${riskData.compliance_score || '--'}
                    </div>
                    <div class="score-label">Compliance Score</div>
                    <div class="score-status">Current Level</div>
                </div>
            </div>
            
            <div class="executive-summary">
                <h3>Executive Summary</h3>
                <p>${analysis.executive_summary || 'Analysis completed successfully.'}</p>
            </div>
            
            ${Object.keys(insights).length > 0 ? `
                <div class="persona-specific-insights">
                    <h3>${getPersonaTitle(persona)} Insights</h3>
                    <div class="insights-list">
                        ${Object.entries(insights).map(([key, value]) => `
                            <div class="insight-row">
                                <span class="insight-label">${formatLabel(key)}:</span>
                                <span class="insight-value">${value}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

function getPersonaTitle(persona) {
    const titles = {
        entrepreneur: 'Investor & Fundraising',
        consultant: 'Client Risk & Liability',
        seller: 'Sales & Market Positioning'
    };
    return titles[persona] || 'Business';
}

function formatLabel(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function showAnalysisError(error) {
    const loading = document.getElementById('analysisLoading');
    const results = document.getElementById('analysisResults');
    
    if (loading) loading.style.display = 'none';
    if (!results) return;
    
    results.innerHTML = `
        <div class="error-state">
            <div class="error-icon">⚠️</div>
            <h3>Analysis Error</h3>
            <p>We encountered an issue analyzing your AI system. Please try again or contact support.</p>
            <div class="error-actions">
                <button class="btn-primary" onclick="runAnalysis()">
                    <i class="fas fa-refresh"></i> Try Again
                </button>
                <button class="btn-secondary" onclick="goToDashboard()">
                    <i class="fas fa-tachometer-alt"></i> Go to Dashboard
                </button>
            </div>
        </div>
    `;
    
    results.style.display = 'block';
}

function saveWizardData() {
    localStorage.setItem('nexusai_wizard_data', JSON.stringify(wizardData));
    localStorage.setItem('nexusai_wizard_step', currentStep.toString());
}

function loadSavedWizardData() {
    const savedData = localStorage.getItem('nexusai_wizard_data');
    const savedStep = localStorage.getItem('nexusai_wizard_step');
    
    if (savedData && !wizardData.demo_scenario) {
        try {
            wizardData = JSON.parse(savedData);
            if (wizardData.persona) {
                selectedPersona = wizardData.persona;
            }
        } catch (error) {
            console.warn('Failed to load saved wizard data:', error);
        }
    }
    
    if (savedStep && !window.location.search.includes('demo')) {
        const step = parseInt(savedStep);
        if (step > 1 && step <= totalSteps) {
            showNotification('Continuing from where you left off...', 'info');
            setTimeout(() => {
                currentStep = step;
                updateWizardDisplay();
                updateProgress();
            }, 1000);
        }
    }
}

function clearSavedWizardData() {
    localStorage.removeItem('nexusai_wizard_data');
    localStorage.removeItem('nexusai_wizard_step');
    sessionStorage.removeItem('selectedScenario');
    sessionStorage.removeItem('selectedPersona');
}

function trackWizardCompletion(persona) {
    console.log('Wizard completed:', { persona, steps: currentStep });
}

// Global functions
async function downloadWizardReport() {
    const analysis = window.NexusAI.getAnalysis();
    if (!analysis) {
        showNotification('No analysis data available', 'error');
        return;
    }
    
    try {
        showNotification('Generating your report...', 'info');
        
        const response = await fetch('/api/generate-report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                analysis_data: analysis,
                company_name: wizardData.company_name || 'Your Company',
                persona: selectedPersona,
                wizard_data: wizardData
            })
        });
        
        if (!response.ok) throw new Error('Failed to generate report');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `NexusAI_${selectedPersona}_Analysis_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showNotification('Report downloaded successfully!', 'success');
        
    } catch (error) {
        showNotification('Failed to download report', 'error');
        console.error('Report download error:', error);
    }
}

function goToDashboard() {
    window.location.href = '/dashboard';
}

function startNewAssessment() {
    clearSavedWizardData();
    window.location.reload();
}

// Export functions
window.nextStep = nextStep;
window.previousStep = previousStep;
window.runAnalysis = runAnalysis;
window.downloadWizardReport = downloadWizardReport;
window.goToDashboard = goToDashboard;
window.startNewAssessment = startNewAssessment;

// Auto-save every 30 seconds
setInterval(() => {
    if (Object.keys(wizardData).length > 0) {
        saveWizardData();
    }
}, 30000);
