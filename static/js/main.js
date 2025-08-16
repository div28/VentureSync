// Main site functionality
let selectedPersona = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    initializePersonaSelection();
    initializeAnimations();
});

function initializeNavigation() {
    // Smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

function initializePersonaSelection() {
    const personaOptions = document.querySelectorAll('.persona-option');
    const startButton = document.getElementById('startAssessment');
    
    personaOptions.forEach(option => {
        option.addEventListener('click', () => {
            // Remove previous selections
            personaOptions.forEach(p => p.classList.remove('selected'));
            
            // Select current
            option.classList.add('selected');
            selectedPersona = option.dataset.persona;
            
            // Update start button
            if (startButton) {
                updateStartButton(selectedPersona);
            }
        });
    });
}

function updateStartButton(persona) {
    const startButton = document.getElementById('startAssessment');
    const personaMessages = {
        'entrepreneur': 'Get Investor-Ready',
        'consultant': 'Assess Client Risk', 
        'seller': 'Enable Enterprise Sales'
    };
    
    startButton.textContent = personaMessages[persona] || 'Start Assessment';
    startButton.href = `/wizard?persona=${persona}`;
}

function initializeAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Animate cards on scroll
    document.querySelectorAll('.market-card, .analytics-card, .research-card, .pricing-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

// API helper functions
async function makeAPICall(endpoint, data = null, method = 'GET') {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(endpoint, options);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Utility functions
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'flex';
    }
}

function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#dc2626' : type === 'success' ? '#10b981' : '#3b82f6'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    
    notification.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" style="margin-left: 1rem; background: none; border: none; color: white; cursor: pointer;">×</button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Global state management
window.NexusAI = {
    currentAnalysis: null,
    selectedPersona: null,
    
    setAnalysis: function(analysis) {
        this.currentAnalysis = analysis;
    },
    
    getAnalysis: function() {
        return this.currentAnalysis;
    },
    
    setPersona: function(persona) {
        this.selectedPersona = persona;
    },
    
    getPersona: function() {
        return this.selectedPersona;
    }
};

// CSS animation keyframes
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
`;
document.head.appendChild(style);
