from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import uuid
from datetime import datetime, timedelta
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import requests
import os

app = Flask(__name__)
CORS(app)

# Anthropic API configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

# Compliance frameworks database
COMPLIANCE_FRAMEWORKS = {
    "fintech": {
        "name": "Financial Technology",
        "regulations": [
            {
                "name": "GDPR - Financial Data Processing",
                "description": "Data protection for financial AI systems",
                "penalty": "Up to €20M or 4% of global revenue",
                "requirements": ["Data minimization", "Consent management", "Right to explanation"]
            },
            {
                "name": "PCI DSS - AI Payment Processing",
                "description": "Security standards for AI handling payment data",
                "penalty": "Up to $500K monthly fines",
                "requirements": ["Secure AI training", "Data encryption", "Access controls"]
            },
            {
                "name": "Fair Credit Reporting Act (FCRA)",
                "description": "AI-driven credit decisions and reporting",
                "penalty": "Up to $1M per violation",
                "requirements": ["Model explainability", "Bias testing", "Consumer notices"]
            }
        ]
    },
    "healthcare": {
        "name": "Healthcare Technology",
        "regulations": [
            {
                "name": "HIPAA - AI Healthcare Data",
                "description": "Privacy rules for AI processing health information",
                "penalty": "Up to $1.5M per incident",
                "requirements": ["De-identification", "Audit logs", "Business associate agreements"]
            },
            {
                "name": "FDA AI/ML Guidance",
                "description": "Regulatory framework for medical AI devices",
                "penalty": "Product recalls and $10M+ fines",
                "requirements": ["Clinical validation", "Continuous monitoring", "Change control"]
            },
            {
                "name": "EU AI Act - High-Risk Medical AI",
                "description": "Strict requirements for medical AI systems",
                "penalty": "Up to €30M or 6% of global revenue",
                "requirements": ["CE marking", "Quality management", "Human oversight"]
            }
        ]
    },
    "hr": {
        "name": "Human Resources Technology",
        "regulations": [
            {
                "name": "EU AI Act - HR AI Systems",
                "description": "Requirements for AI in hiring and workplace",
                "penalty": "Up to €15M or 3% of global revenue",
                "requirements": ["Bias monitoring", "Transparency", "Human review"]
            },
            {
                "name": "EEOC - AI in Hiring",
                "description": "Equal employment opportunity in AI recruitment",
                "penalty": "Unlimited damages in lawsuits",
                "requirements": ["Adverse impact testing", "Reasonable accommodations", "Documentation"]
            },
            {
                "name": "NYC Local Law 144",
                "description": "Bias audits for automated hiring tools",
                "penalty": "$500-$1,500 per violation",
                "requirements": ["Annual bias audits", "Public posting", "Alternative selection processes"]
            }
        ]
    },
    "social": {
        "name": "Social Media & Content",
        "regulations": [
            {
                "name": "Digital Services Act (DSA)",
                "description": "Content moderation and algorithmic transparency",
                "penalty": "Up to €50M or 6% of global revenue",
                "requirements": ["Risk assessments", "Algorithmic audits", "Transparency reports"]
            },
            {
                "name": "California SB 1001",
                "description": "Bot disclosure requirements",
                "penalty": "$2,500 per violation",
                "requirements": ["Bot identification", "Clear disclosure", "User consent"]
            },
            {
                "name": "UK Online Safety Act",
                "description": "Duty of care for AI-driven platforms",
                "penalty": "Up to £18M or 10% of global revenue",
                "requirements": ["Content governance", "Age verification", "Risk assessments"]
            }
        ]
    },
    "general": {
        "name": "General SaaS/Technology",
        "regulations": [
            {
                "name": "GDPR - AI Data Processing",
                "description": "General data protection for AI systems",
                "penalty": "Up to €20M or 4% of global revenue",
                "requirements": ["Lawful basis", "Data minimization", "Privacy by design"]
            },
            {
                "name": "CCPA - AI Consumer Rights",
                "description": "California consumer privacy for AI applications",
                "penalty": "Up to $7,500 per violation",
                "requirements": ["Data disclosure", "Opt-out rights", "Non-discrimination"]
            },
            {
                "name": "EU AI Act - General Purpose AI",
                "description": "Foundation model and general AI requirements",
                "penalty": "Up to €35M or 7% of global revenue",
                "requirements": ["Documentation", "Risk assessment", "Incident reporting"]
            }
        ]
    }
}

# Risk assessment matrices
STAGE_MULTIPLIERS = {
    "mvp": 0.8,
    "seed": 1.0,
    "series-a": 1.2,
    "series-b": 1.4
}

INDUSTRY_RISK_SCORES = {
    "fintech": 85,
    "healthcare": 90,
    "hr": 75,
    "social": 70,
    "general": 60
}

AI_TYPE_RISKS = {
    "generative": 65,
    "decision": 85,
    "recommendation": 60,
    "biometric": 95,
    "nlp": 55
}

def call_claude_api(prompt, max_tokens=1000):
    """Call Claude API for AI-powered analysis"""
    try:
        headers = {
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY
        }
        
        payload = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json()["content"][0]["text"]
        else:
            return "AI analysis unavailable at this time."
    except Exception as e:
        print(f"Claude API error: {e}")
        return "AI analysis unavailable at this time."

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/frameworks/<industry>', methods=['GET'])
def get_compliance_frameworks(industry):
    """Get compliance frameworks for specific industry"""
    if industry not in COMPLIANCE_FRAMEWORKS:
        return jsonify({"error": "Industry not found"}), 404
    
    return jsonify(COMPLIANCE_FRAMEWORKS[industry])

@app.route('/api/assess', methods=['POST'])
def assess_compliance():
    """Assess compliance based on startup data"""
    try:
        data = request.get_json()
        
        # Extract assessment data
        stage = data.get('stage', 'mvp')
        ai_types = data.get('aiTypes', [])
        industry = data.get('industry', 'general')
        company_data = data.get('companyData', {})
        
        # Calculate risk score
        base_score = INDUSTRY_RISK_SCORES.get(industry, 60)
        stage_multiplier = STAGE_MULTIPLIERS.get(stage, 1.0)
        
        # AI type risk calculation
        ai_risk = 0
        if ai_types:
            ai_risk = sum(AI_TYPE_RISKS.get(ai_type, 50) for ai_type in ai_types) / len(ai_types)
        
        # Final score calculation
        final_risk = min(95, max(15, base_score * stage_multiplier + (ai_risk - 50) * 0.5))
        compliance_score = 100 - final_risk
        
        # Generate AI-powered recommendations
        prompt = f"""
        As an AI compliance expert, analyze this startup's compliance posture:
        
        Company Stage: {stage}
        Industry: {industry}
        AI Types: {', '.join(ai_types)}
        Compliance Score: {compliance_score:.0f}/100
        
        Provide 3-5 specific, actionable recommendations to improve compliance.
        Focus on the most critical gaps first. Be concise and practical.
        """
        
        ai_recommendations = call_claude_api(prompt, 500)
        
        # Get applicable regulations
        regulations = COMPLIANCE_FRAMEWORKS.get(industry, COMPLIANCE_FRAMEWORKS['general'])
        
        assessment_result = {
            "assessmentId": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "complianceScore": round(compliance_score),
            "riskLevel": "High" if compliance_score < 50 else "Medium" if compliance_score < 75 else "Low",
            "stage": stage,
            "industry": industry,
            "aiTypes": ai_types,
            "applicableRegulations": regulations['regulations'][:3],  # Top 3 most relevant
            "recommendations": ai_recommendations,
            "nextSteps": generate_next_steps(stage, compliance_score),
            "fundraisingReadiness": calculate_fundraising_readiness(stage, compliance_score)
        }
        
        return jsonify(assessment_result)
        
    except Exception as e:
        print(f"Assessment error: {e}")
        return jsonify({"error": "Assessment failed"}), 500

def generate_next_steps(stage, score):
    """Generate stage-appropriate next steps"""
    steps = []
    
    if stage == "mvp":
        steps = [
            "Establish basic privacy policy",
            "Implement data collection consent",
            "Document AI decision processes"
        ]
    elif stage == "seed":
        steps = [
            "Complete compliance gap analysis",
            "Implement bias testing framework",
            "Prepare investor due diligence package"
        ]
    elif stage == "series-a":
        steps = [
            "Conduct third-party compliance audit",
            "Implement enterprise-grade security",
            "Establish compliance monitoring"
        ]
    else:  # series-b+
        steps = [
            "Achieve SOC 2 Type II certification",
            "Implement full regulatory compliance",
            "Prepare for IPO readiness"
        ]
    
    if score < 50:
        steps.insert(0, "Address critical compliance gaps immediately")
    
    return steps

def calculate_fundraising_readiness(stage, score):
    """Calculate fundraising readiness metrics"""
    readiness_score = min(100, score + 10)  # Slight boost for fundraising context
    
    # Stage-specific benchmarks
    benchmarks = {
        "mvp": {"target": 60, "investor_expectation": "Basic compliance framework"},
        "seed": {"target": 70, "investor_expectation": "Due diligence ready"},
        "series-a": {"target": 80, "investor_expectation": "Enterprise compliance"},
        "series-b": {"target": 90, "investor_expectation": "Audit-ready processes"}
    }
    
    stage_benchmark = benchmarks.get(stage, benchmarks["seed"])
    
    return {
        "score": round(readiness_score),
        "target": stage_benchmark["target"],
        "gap": max(0, stage_benchmark["target"] - readiness_score),
        "investorExpectation": stage_benchmark["investor_expectation"],
        "recommendation": "Ready for fundraising" if readiness_score >= stage_benchmark["target"] else "Address gaps before fundraising"
    }

@app.route('/api/monitoring/updates', methods=['GET'])
def get_regulatory_updates():
    """Get latest regulatory updates relevant to AI startups"""
    
    # In a real implementation, this would fetch from a regulatory monitoring service
    updates = [
        {
            "id": str(uuid.uuid4()),
            "date": (datetime.now() - timedelta(days=2)).isoformat(),
            "title": "EU AI Act High-Risk System Guidelines Published",
            "summary": "New implementation guidelines for high-risk AI systems under the EU AI Act",
            "impact": "High",
            "relevantIndustries": ["fintech", "healthcare", "hr"],
            "actionRequired": True,
            "deadline": (datetime.now() + timedelta(days=180)).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "date": (datetime.now() - timedelta(days=5)).isoformat(),
            "title": "California SB 1001 Enforcement Update",
            "summary": "Attorney General issues new guidance on AI bot disclosure requirements",
            "impact": "Medium",
            "relevantIndustries": ["social", "general"],
            "actionRequired": False,
            "deadline": None
        },
        {
            "id": str(uuid.uuid4()),
            "date": (datetime.now() - timedelta(days=7)).isoformat(),
            "title": "NIST AI Risk Management Framework 2.0",
            "summary": "Updated framework includes specific guidance for startup AI systems",
            "impact": "Medium",
            "relevantIndustries": ["general"],
            "actionRequired": False,
            "deadline": None
        }
    ]
    
    return jsonify({"updates": updates})

@app.route('/api/vc-simulation', methods=['POST'])
def vc_simulation():
    """Simulate VC due diligence questions and scoring"""
    try:
        data = request.get_json()
        stage = data.get('stage', 'seed')
        industry = data.get('industry', 'general')
        compliance_score = data.get('complianceScore', 50)
        
        # Generate VC-specific questions based on stage and industry
        questions = generate_vc_questions(stage, industry)
        
        # Simulate VC scoring
        vc_score = calculate_vc_score(compliance_score, stage)
        
        return jsonify({
            "simulationId": str(uuid.uuid4()),
            "vcScore": vc_score,
            "questions": questions,
            "benchmark": get_stage_benchmark(stage),
            "recommendations": generate_vc_recommendations(vc_score, stage)
        })
        
    except Exception as e:
        print(f"VC simulation error: {e}")
        return jsonify({"error": "VC simulation failed"}), 500

def generate_vc_questions(stage, industry):
    """Generate stage and industry appropriate VC questions"""
    base_questions = [
        "How do you ensure your AI models are free from bias?",
        "What data governance policies do you have in place?",
        "How do you handle user privacy and consent?",
        "What is your approach to AI model explainability?"
    ]
    
    industry_questions = {
        "fintech": [
            "How do you comply with financial regulations like GDPR and PCI DSS?",
            "What measures prevent discriminatory lending or credit decisions?"
        ],
        "healthcare": [
            "How do you ensure HIPAA compliance in your AI processing?",
            "What clinical validation have you completed for your AI models?"
        ],
        "hr": [
            "How do you prevent hiring discrimination in your AI?",
            "What bias auditing processes do you have in place?"
        ]
    }
    
    questions = base_questions[:]
    if industry in industry_questions:
        questions.extend(industry_questions[industry])
    
    return questions[:6]  # Limit to 6 questions

def calculate_vc_score(compliance_score, stage):
    """Calculate VC attractiveness score"""
    base_vc_score = compliance_score * 0.8  # VCs weight compliance at 80%
    
    stage_bonus = {
        "mvp": 5,
        "seed": 10,
        "series-a": 15,
        "series-b": 20
    }
    
    return min(100, round(base_vc_score + stage_bonus.get(stage, 10)))

def get_stage_benchmark(stage):
    """Get benchmark data for stage"""
    benchmarks = {
        "mvp": {"median_score": 45, "top_quartile": 65},
        "seed": {"median_score": 60, "top_quartile": 75},
        "series-a": {"median_score": 75, "top_quartile": 85},
        "series-b": {"median_score": 85, "top_quartile": 95}
    }
    return benchmarks.get(stage, benchmarks["seed"])

def generate_vc_recommendations(vc_score, stage):
    """Generate VC-specific recommendations"""
    if vc_score >= 80:
        return [
            "Excellent compliance posture for fundraising",
            "Use compliance as a competitive differentiator",
            "Prepare detailed due diligence materials"
        ]
    elif vc_score >= 60:
        return [
            "Address key compliance gaps before fundraising",
            "Implement recommended security measures",
            "Document compliance processes"
        ]
    else:
        return [
            "Significant compliance work needed before fundraising",
            "Consider compliance consultation",
            "Delay fundraising until critical gaps addressed"
        ]

@app.route('/generate-report', methods=['POST'])
def generate_detailed_report():
    """Generate comprehensive PDF compliance report"""
    try:
        data = request.get_json()
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#667eea')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#1a202c')
        )
        
        # Title
        title = Paragraph("FounderShield AI Compliance Report", title_style)
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Executive Summary Table
        exec_data = [
            ['Report ID', str(uuid.uuid4())[:8]],
            ['Generated', datetime.now().strftime('%Y-%m-%d %H:%M UTC')],
            ['Company Stage', data.get('stage', 'Unknown').title()],
            ['Industry', data.get('industry', 'Unknown').title()],
            ['Compliance Score', f"{data.get('score', 'N/A')}/100"],
            ['AI Systems', ', '.join(data.get('aiTypes', []))]
        ]
        
        exec_table = Table(exec_data, colWidths=[2*inch, 3*inch])
        exec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0'))
        ]))
        
        elements.append(Paragraph("Executive Summary", heading_style))
        elements.append(exec_table)
        elements.append(Spacer(1, 20))
        
        # Compliance Analysis
        elements.append(Paragraph("Compliance Analysis", heading_style))
        
        score = int(data.get('score', 50))
        if score >= 80:
            analysis = "Excellent compliance foundation. Your startup demonstrates strong regulatory awareness and implementation."
        elif score >= 60:
            analysis = "Good compliance progress with some areas for improvement. Focus on closing identified gaps."
        else:
            analysis = "Significant compliance gaps detected. Immediate action recommended to address regulatory risks."
        
        elements.append(Paragraph(analysis, styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Key Findings
        elements.append(Paragraph("Key Findings", heading_style))
        
        findings = [
            f"• Current compliance maturity: {score}% for {data.get('stage', 'unknown')} stage company",
            f"• Industry risk profile: {data.get('industry', 'unknown').title()} sector requirements",
            f"• AI system complexity: {len(data.get('aiTypes', []))} different AI capabilities",
            "• Regulatory landscape: EU AI Act, GDPR, and sector-specific requirements applicable"
        ]
        
        for finding in findings:
            elements.append(Paragraph(finding, styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        # Implementation Roadmap
        elements.append(Paragraph("Implementation Roadmap", heading_style))
        
        roadmap_items = [
            "Phase 1 (0-30 days): Address critical compliance gaps",
            "Phase 2 (30-90 days): Implement core governance frameworks",
            "Phase 3 (90-180 days): Complete sector-specific requirements",
            "Phase 4 (180+ days): Ongoing monitoring and optimization"
        ]
        
        for item in roadmap_items:
            elements.append(Paragraph(item, styles['Normal']))
        
        elements.append(Spacer(1, 30))
        
        # Contact Information
        elements.append(Paragraph("Next Steps", heading_style))
        contact_text = """
        This assessment provides a high-level overview of your compliance posture. 
        For detailed implementation guidance, consider scheduling a consultation with our compliance experts.
        
        Contact: compliance@foundershield.com
        Platform: https://foundershield.com
        
        Disclaimer: This report is for informational purposes only and does not constitute legal advice.
        """
        elements.append(Paragraph(contact_text, styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'FounderShield_Report_{datetime.now().strftime("%Y%m%d")}.pdf'
        )
        
    except Exception as e:
        print(f"Report generation error: {e}")
        return jsonify({"error": "Report generation failed"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
