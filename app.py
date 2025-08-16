from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import requests
import json
import os
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
import io
import random
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Claude API configuration
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY', 'your-claude-api-key')
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

# Enhanced demo scenarios with persona focus
DEMO_SCENARIOS = {
    "entrepreneur": [
        {
            "name": "TechStart Pro",
            "type": "AI Startup - Series A",
            "industry": "B2B SaaS",
            "ai_system": "Sales lead scoring with anonymized data",
            "risk_level": "LOW",
            "risk_score": 25,
            "compliance_score": 92,
            "potential_fines": "$15,000",
            "status": "✅ Investor Ready",
            "key_strengths": ["GDPR compliant", "SOC2 certified", "Clear data policies"],
            "estimated_cost": "$45,000",
            "funding_advantage": "78% higher Series A success",
            "investor_confidence": "92% VC approval rate"
        },
        {
            "name": "HealthTech AI",
            "type": "Healthcare Startup - Seed",
            "industry": "Healthcare",
            "ai_system": "HIPAA-compliant patient scheduling AI",
            "risk_level": "LOW",
            "risk_score": 30,
            "compliance_score": 89,
            "potential_fines": "$25,000",
            "status": "✅ Series B Ready",
            "key_strengths": ["HIPAA certified", "BAA agreements", "Encrypted data"],
            "estimated_cost": "$78,000",
            "funding_advantage": "Enterprise deals 60% faster",
            "investor_confidence": "Zero compliance violations"
        }
    ],
    "consultant": [
        {
            "name": "QuickHire AI Client",
            "type": "HR Tech Prospect",
            "industry": "Human Resources",
            "ai_system": "AI hiring tool with bias issues",
            "risk_level": "CRITICAL",
            "risk_score": 95,
            "compliance_score": 15,
            "potential_fines": "$4,200,000",
            "status": "🚨 Avoid Client",
            "key_risks": ["EEOC violations", "Discriminatory AI", "No bias testing"],
            "estimated_cost": "$180,000",
            "lawsuit_probability": "73% violation rate",
            "protection_needed": "Contract liability caps essential"
        },
        {
            "name": "RetailBot Corp",
            "type": "E-commerce Client",
            "industry": "Retail",
            "ai_system": "Customer data mining without consent",
            "risk_level": "CRITICAL",
            "risk_score": 88,
            "compliance_score": 22,
            "potential_fines": "$2,800,000",
            "status": "🚨 High Risk Client",
            "key_risks": ["GDPR violations", "No consent", "Data misuse"],
            "estimated_cost": "$220,000",
            "lawsuit_probability": "High GDPR enforcement",
            "protection_needed": "Full compliance before engagement"
        }
    ],
    "seller": [
        {
            "name": "FinanceBot Inc",
            "type": "FinTech SMB",
            "industry": "Financial Services",
            "ai_system": "Investment advice chatbot",
            "risk_level": "MEDIUM",
            "risk_score": 55,
            "compliance_score": 68,
            "potential_fines": "$350,000",
            "status": "⚠️ Education Needed",
            "key_gaps": ["SEC registration", "Fiduciary duties", "Risk disclosures"],
            "estimated_cost": "$125,000",
            "client_education": "Compliance training required",
            "liability_protection": "Moderate risk mitigation"
        }
    ]
}

# Analytics data for demo
ANALYTICS_DATA = {
    "conversion_metrics": {
        "entrepreneur": {"visitors": 1000, "assessments": 450, "paid": 140, "conversion_rate": "31%"},
        "consultant": {"visitors": 800, "assessments": 520, "paid": 180, "conversion_rate": "35%"},
        "seller": {"visitors": 600, "assessments": 240, "paid": 60, "conversion_rate": "25%"}
    },
    "ltv_by_persona": {
        "entrepreneur": {"avg_ltv": 12000, "retention_12m": "78%", "expansion_revenue": "45%"},
        "consultant": {"avg_ltv": 8500, "retention_12m": "82%", "expansion_revenue": "25%"},
        "seller": {"avg_ltv": 4200, "retention_12m": "65%", "expansion_revenue": "15%"}
    },
    "market_intelligence": {
        "tam": "$12.3B",
        "sam": "$2.1B", 
        "som": "$210M",
        "growth_rate": "34% YoY",
        "competitor_analysis": {
            "vanta": "Enterprise only, $2K+ monthly",
            "legal_firms": "$500/hr, slow delivery",
            "nexusai": "Entrepreneur-focused, $299/month"
        }
    }
}

class RiskScoringEngine:
    def __init__(self):
        self.industry_weights = {
            'healthcare': {'base_risk': 0.8, 'multiplier': 1.5},
            'finance': {'base_risk': 0.75, 'multiplier': 1.4},
            'hr': {'base_risk': 0.7, 'multiplier': 1.3},
            'education': {'base_risk': 0.6, 'multiplier': 1.2},
            'retail': {'base_risk': 0.5, 'multiplier': 1.1},
            'saas': {'base_risk': 0.4, 'multiplier': 1.0}
        }
        
        self.persona_adjustments = {
            'entrepreneur': {'risk_tolerance': 0.9, 'growth_factor': 1.2},
            'consultant': {'risk_tolerance': 0.7, 'liability_factor': 1.4},
            'seller': {'risk_tolerance': 0.8, 'education_factor': 1.1}
        }

    def calculate_persona_risk(self, ai_system_data, persona):
        industry = ai_system_data.get('industry', 'saas').lower()
        base_score = self.industry_weights.get(industry, self.industry_weights['saas'])['base_risk'] * 100
        
        persona_config = self.persona_adjustments.get(persona, self.persona_adjustments['entrepreneur'])
        adjusted_score = base_score * persona_config.get('risk_tolerance', 1.0)
        
        return min(100, max(0, int(adjusted_score)))

class ComprehensiveAnalysisAgent:
    def __init__(self):
        self.risk_engine = RiskScoringEngine()
        
    def analyze_with_persona(self, ai_system_data, persona):
        risk_score = self.risk_engine.calculate_persona_risk(ai_system_data, persona)
        compliance_score = max(10, 100 - risk_score)
        
        risk_level = self._get_risk_level(risk_score)
        
        # Persona-specific analysis
        if persona == 'entrepreneur':
            return self._entrepreneur_analysis(ai_system_data, risk_score, compliance_score, risk_level)
        elif persona == 'consultant':
            return self._consultant_analysis(ai_system_data, risk_score, compliance_score, risk_level)
        else:
            return self._seller_analysis(ai_system_data, risk_score, compliance_score, risk_level)
    
    def _entrepreneur_analysis(self, data, risk_score, compliance_score, risk_level):
        return {
            "risk_assessment": {
                "risk_level": risk_level,
                "risk_score": risk_score,
                "compliance_score": compliance_score,
                "status_color": self._get_status_color(risk_level),
                "investor_readiness": "Series B Ready" if compliance_score > 85 else "Needs improvement"
            },
            "financial_impact": {
                "potential_fines": f"${random.randint(50000, 500000):,}",
                "implementation_costs": f"${random.randint(80000, 200000):,}",
                "fundraising_impact": f"{random.randint(40, 80)}% faster with compliance",
                "roi_timeline": "6-12 months"
            },
            "investor_advantage": {
                "vc_approval_rate": f"{90 - (risk_score // 10)}%",
                "due_diligence_speed": f"{random.randint(40, 70)}% faster",
                "valuation_premium": f"{random.randint(15, 35)}% higher"
            },
            "recommendations": {
                "immediate_actions": ["Prepare investor compliance package", "Document data governance"],
                "funding_milestones": ["Complete SOC2 before Series A", "EU compliance before international expansion"]
            },
            "executive_summary": f"Compliance score of {compliance_score}% positions you in top {100-compliance_score}% of AI startups. Strong foundation for investor confidence."
        }
    
    def _consultant_analysis(self, data, risk_score, compliance_score, risk_level):
        lawsuit_risk = "High" if risk_score > 70 else "Medium" if risk_score > 40 else "Low"
        
        return {
            "risk_assessment": {
                "risk_level": risk_level,
                "risk_score": risk_score,
                "compliance_score": compliance_score,
                "status_color": self._get_status_color(risk_level),
                "client_recommendation": "Avoid" if risk_score > 70 else "Proceed with caution" if risk_score > 40 else "Safe to engage"
            },
            "financial_impact": {
                "potential_fines": f"${random.randint(500000, 5000000):,}",
                "legal_costs": f"${random.randint(100000, 500000):,}",
                "lawsuit_probability": f"{risk_score}%",
                "insurance_impact": lawsuit_risk
            },
            "client_protection": {
                "contract_clauses": ["Liability caps", "Compliance warranties", "Indemnification"],
                "pricing_adjustment": f"{max(0, (risk_score - 30) * 2)}% risk premium",
                "engagement_terms": "Require compliance audit" if risk_score > 60 else "Standard terms"
            },
            "recommendations": {
                "immediate_actions": ["Client risk assessment", "Contract protection review"],
                "ongoing_protection": ["Monthly compliance checks", "Insurance review"]
            },
            "executive_summary": f"Client presents {risk_level.lower()} liability risk. {lawsuit_risk} probability of compliance violations requiring enhanced contract protection."
        }
    
    def _seller_analysis(self, data, risk_score, compliance_score, risk_level):
        return {
            "risk_assessment": {
                "risk_level": risk_level,
                "risk_score": risk_score,
                "compliance_score": compliance_score,
                "status_color": self._get_status_color(risk_level),
                "sales_impact": "Compliance gap may slow enterprise sales"
            },
            "financial_impact": {
                "potential_fines": f"${random.randint(100000, 1000000):,}",
                "sales_impact": f"{random.randint(20, 50)}% longer sales cycles",
                "deal_loss_risk": f"{risk_score // 2}%",
                "compliance_investment": f"${random.randint(50000, 150000):,}"
            },
            "sales_enablement": {
                "client_education": ["Compliance training materials", "Risk mitigation guides"],
                "competitive_advantage": "Compliance-first positioning",
                "deal_protection": ["Liability limitations", "Shared responsibility model"]
            },
            "recommendations": {
                "immediate_actions": ["Create compliance materials", "Train sales team"],
                "market_positioning": ["Compliance leader", "Risk-aware provider"]
            },
            "executive_summary": f"Compliance gaps present {risk_level.lower()} sales risk. Client education and positioning can turn compliance into competitive advantage."
        }
    
    def _get_risk_level(self, risk_score):
        if risk_score >= 80: return "CRITICAL"
        elif risk_score >= 60: return "HIGH"
        elif risk_score >= 40: return "MEDIUM"
        else: return "LOW"
    
    def _get_status_color(self, risk_level):
        colors = {"CRITICAL": "#dc2626", "HIGH": "#ea580c", "MEDIUM": "#f59e0b", "LOW": "#10b981"}
        return colors.get(risk_level, "#6b7280")

# Initialize AI agent
analysis_agent = ComprehensiveAnalysisAgent()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/wizard')
def wizard():
    return render_template('wizard.html')

@app.route('/api/demo-scenarios')
def get_demo_scenarios():
    return jsonify(DEMO_SCENARIOS)

@app.route('/api/analytics-dashboard')
def get_analytics_dashboard():
    return jsonify(ANALYTICS_DATA)

@app.route('/api/analyze', methods=['POST'])
def analyze_compliance():
    data = request.json
    use_demo = data.get('use_demo', False)
    persona = data.get('persona', 'entrepreneur')
    
    if use_demo:
        demo_type = data.get('demo_type', persona)
        scenarios = DEMO_SCENARIOS.get(demo_type, DEMO_SCENARIOS['entrepreneur'])
        demo_data = random.choice(scenarios)
        
        # Return demo analysis with persona focus
        return jsonify({
            "risk_assessment": {
                "risk_level": demo_data['risk_level'],
                "risk_score": demo_data['risk_score'],
                "compliance_score": demo_data['compliance_score'],
                "status_color": "#dc2626" if demo_data['risk_level'] == "CRITICAL" else "#10b981"
            },
            "demo_data": demo_data,
            "persona_insights": get_persona_insights(persona, demo_data),
            "executive_summary": f"{demo_data['name']} analysis complete for {persona} workflow."
        })
    
    # Real analysis with persona consideration
    try:
        result = analysis_agent.analyze_with_persona(data, persona)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_persona_insights(persona, demo_data):
    if persona == 'entrepreneur':
        return {
            "funding_impact": demo_data.get('funding_advantage', 'Positive impact on fundraising'),
            "investor_confidence": demo_data.get('investor_confidence', 'High investor appeal'),
            "competitive_advantage": "Compliance as differentiator"
        }
    elif persona == 'consultant':
        return {
            "liability_assessment": demo_data.get('lawsuit_probability', 'Risk assessment complete'),
            "contract_protection": demo_data.get('protection_needed', 'Standard protections sufficient'),
            "engagement_recommendation": demo_data['status']
        }
    else:
        return {
            "sales_impact": demo_data.get('client_education', 'Client education recommended'),
            "liability_protection": demo_data.get('liability_protection', 'Moderate protection needed'),
            "market_positioning": "Compliance-aware provider"
        }

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    data = request.json
    analysis_data = data.get('analysis_data', {})
    company_name = data.get('company_name', 'Demo Company')
    
    # Generate PDF (simplified)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    story.append(Paragraph(f"NexusAI Compliance Report - {company_name}", styles['Title']))
    story.append(Spacer(1, 20))
    
    # Analysis summary
    story.append(Paragraph("Executive Summary", styles['Heading2']))
    summary = analysis_data.get('executive_summary', 'Compliance analysis completed.')
    story.append(Paragraph(summary, styles['Normal']))
    story.append(Spacer(1, 15))
    
    # Risk assessment
    risk_data = analysis_data.get('risk_assessment', {})
    story.append(Paragraph("Risk Assessment", styles['Heading2']))
    story.append(Paragraph(f"Risk Level: {risk_data.get('risk_level', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"Risk Score: {risk_data.get('risk_score', 'N/A')}/100", styles['Normal']))
    story.append(Paragraph(f"Compliance Score: {risk_data.get('compliance_score', 'N/A')}/100", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(buffer.getvalue())
        tmp_file_path = tmp_file.name
    
    return send_file(
        tmp_file_path,
        as_attachment=True,
        download_name=f"NexusAI_Report_{company_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
        mimetype='application/pdf'
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
