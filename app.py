from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import time
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import anthropic
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize Claude client
client = anthropic.Anthropic(
    api_key=os.getenv('ANTHROPIC_API_KEY')
)

# Assessment configuration
COMPLIANCE_FRAMEWORKS = {
    'gdpr': {
        'name': 'General Data Protection Regulation',
        'weight': 0.3,
        'categories': ['data_protection', 'consent', 'rights', 'security']
    },
    'eu_ai_act': {
        'name': 'EU AI Act',
        'weight': 0.4,
        'categories': ['risk_assessment', 'transparency', 'human_oversight', 'accuracy']
    },
    'ccpa': {
        'name': 'California Consumer Privacy Act',
        'weight': 0.2,
        'categories': ['data_rights', 'disclosure', 'deletion', 'opt_out']
    },
    'industry_specific': {
        'name': 'Industry Specific Requirements',
        'weight': 0.1,
        'categories': ['sector_rules', 'best_practices']
    }
}

RISK_FACTORS = {
    'high_risk_ai': {
        'multiplier': 1.5,
        'description': 'High-risk AI system under EU AI Act'
    },
    'personal_data': {
        'multiplier': 1.3,
        'description': 'Processing personal data'
    },
    'biometric_data': {
        'multiplier': 1.8,
        'description': 'Processing biometric data'
    },
    'health_data': {
        'multiplier': 1.6,
        'description': 'Processing health data'
    },
    'financial_data': {
        'multiplier': 1.4,
        'description': 'Processing financial data'
    }
}

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'NexusAI Compliance Platform',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/assess', methods=['POST'])
def run_assessment():
    """Run AI compliance assessment using Claude API"""
    try:
        # Get assessment data
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No assessment data provided'}), 400
        
        logger.info(f"Running assessment for company: {data.get('companyName', 'Unknown')}")
        
        # Validate required fields
        required_fields = ['companyName', 'fundingStage', 'industry']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Calculate compliance score
        compliance_result = calculate_compliance_score(data)
        
        # Generate AI-powered insights using Claude
        ai_insights = generate_ai_insights(data, compliance_result)
        
        # Combine results
        result = {
            'overallScore': compliance_result['overall_score'],
            'scoreStatus': get_score_status(compliance_result['overall_score']),
            'compliance': compliance_result['framework_scores'],
            'risks': compliance_result['risks'],
            'recommendations': ai_insights.get('recommendations', []),
            'insights': ai_insights.get('insights', ''),
            'benchmarks': get_industry_benchmarks(data),
            'assessmentId': generate_assessment_id(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Store assessment results (in production, store in database)
        store_assessment_result(data, result)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Assessment failed: {str(e)}")
        return jsonify({'error': 'Assessment failed', 'details': str(e)}), 500

def calculate_compliance_score(data):
    """Calculate compliance score based on assessment data"""
    
    base_scores = {
        'gdpr': 70,
        'eu_ai_act': 60,
        'ccpa': 75,
        'industry_specific': 65
    }
    
    # Adjust scores based on company profile
    funding_stage = data.get('fundingStage', '')
    industry = data.get('industry', '')
    ai_use_cases = data.get('aiUseCases', [])
    data_types = data.get('dataTypes', [])
    target_markets = data.get('targetMarkets', [])
    high_risk = data.get('highRisk', 'unsure')
    
    # Stage-based adjustments
    stage_adjustments = {
        'pre-seed': {'multiplier': 0.8, 'bonus': 0},
        'seed': {'multiplier': 0.9, 'bonus': 5},
        'series-a': {'multiplier': 1.0, 'bonus': 10},
        'series-b': {'multiplier': 1.1, 'bonus': 15}
    }
    
    stage_config = stage_adjustments.get(funding_stage, {'multiplier': 1.0, 'bonus': 0})
    
    # Industry-specific adjustments
    industry_risk = {
        'fintech': 0.9,
        'healthtech': 0.8,
        'b2b-saas': 1.1,
        'e-commerce': 1.0
    }
    
    industry_multiplier = industry_risk.get(industry, 1.0)
    
    # Calculate framework scores
    framework_scores = {}
    risks = []
    
    for framework, config in COMPLIANCE_FRAMEWORKS.items():
        base_score = base_scores[framework]
        
        # Apply adjustments
        adjusted_score = base_score * stage_config['multiplier'] * industry_multiplier
        
        # Data type penalties
        for data_type in data_types:
            if data_type in RISK_FACTORS:
                risk_factor = RISK_FACTORS[data_type]
                penalty = (risk_factor['multiplier'] - 1) * 10
                adjusted_score -= penalty
                
                # Add to risks if score drops significantly
                if penalty > 5:
                    risks.append({
                        'level': 'high' if penalty > 15 else 'medium',
                        'description': risk_factor['description'],
                        'severity': min(penalty / 20, 1.0)
                    })
        
        # High-risk AI system penalty
        if high_risk == 'yes' and framework == 'eu_ai_act':
            adjusted_score -= 15
            risks.append({
                'level': 'high',
                'description': 'High-risk AI system requirements',
                'severity': 0.8
            })
        
        # Market-specific requirements
        if 'eu' in target_markets:
            if framework in ['gdpr', 'eu_ai_act']:
                adjusted_score += 5  # Bonus for EU focus
        
        # Ensure score is within bounds
        adjusted_score = max(0, min(100, adjusted_score + stage_config['bonus']))
        framework_scores[framework.replace('_', '')] = round(adjusted_score)
    
    # Calculate overall score
    overall_score = sum(
        framework_scores[framework.replace('_', '')] * config['weight']
        for framework, config in COMPLIANCE_FRAMEWORKS.items()
    )
    
    # Add some risks based on low scores
    for framework, score in framework_scores.items():
        if score < 50:
            risks.append({
                'level': 'high',
                'description': f'Low {COMPLIANCE_FRAMEWORKS[framework.replace("", "_")]["name"]} compliance',
                'severity': (50 - score) / 50
            })
        elif score < 70:
            risks.append({
                'level': 'medium',
                'description': f'Moderate {COMPLIANCE_FRAMEWORKS[framework.replace("", "_")]["name"]} gaps',
                'severity': (70 - score) / 70
            })
    
    return {
        'overall_score': round(overall_score),
        'framework_scores': framework_scores,
        'risks': risks[:5]  # Limit to top 5 risks
    }

def generate_ai_insights(assessment_data, compliance_result):
    """Generate AI-powered insights using Claude"""
    
    try:
        # Prepare context for Claude
        context = f"""
        Company Profile:
        - Name: {assessment_data.get('companyName', 'Unknown')}
        - Funding Stage: {assessment_data.get('fundingStage', 'Unknown')}
        - Industry: {assessment_data.get('industry', 'Unknown')}
        - AI Use Cases: {', '.join(assessment_data.get('aiUseCases', []))}
        - Data Types: {', '.join(assessment_data.get('dataTypes', []))}
        - Target Markets: {', '.join(assessment_data.get('targetMarkets', []))}
        - High Risk System: {assessment_data.get('highRisk', 'Unknown')}

        Compliance Scores:
        - Overall Score: {compliance_result['overall_score']}%
        - GDPR: {compliance_result['framework_scores'].get('gdpr', 0)}%
        - EU AI Act: {compliance_result['framework_scores'].get('euaiact', 0)}%
        - CCPA: {compliance_result['framework_scores'].get('ccpa', 0)}%

        Top Risks:
        {chr(10).join([f"- {risk['description']} ({risk['level']} risk)" for risk in compliance_result['risks'][:3]])}
        """

        prompt = f"""
        As an AI compliance expert, analyze this startup's compliance assessment and provide:

        1. Key insights about their compliance posture
        2. 5 specific, actionable recommendations prioritized by impact
        3. Fundraising implications and investor perspective

        Assessment Data:
        {context}

        Provide a structured response in JSON format:
        {{
            "insights": "2-3 sentence summary of key findings",
            "recommendations": [
                "Specific actionable recommendation 1",
                "Specific actionable recommendation 2",
                "Specific actionable recommendation 3",
                "Specific actionable recommendation 4",
                "Specific actionable recommendation 5"
            ],
            "fundraising_impact": "How compliance affects fundraising prospects",
            "priority_actions": [
                "Most critical action to take immediately",
                "Second most critical action"
            ]
        }}

        Focus on practical, startup-friendly advice that considers their funding stage and industry.
        """

        # Call Claude API
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Parse Claude's response
        try:
            ai_response = json.loads(response.content[0].text)
            return ai_response
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "insights": "AI analysis completed. Compliance gaps identified in data privacy and transparency requirements.",
                "recommendations": [
                    "Implement data minimization principles",
                    "Enhance algorithm explainability documentation",
                    "Complete privacy impact assessments",
                    "Establish data subject rights procedures",
                    "Set up compliance monitoring processes"
                ],
                "fundraising_impact": "Current compliance gaps may slow due diligence process",
                "priority_actions": [
                    "Address high-risk data processing issues",
                    "Document AI system capabilities and limitations"
                ]
            }

    except Exception as e:
        logger.error(f"Claude API call failed: {str(e)}")
        # Return fallback insights
        return generate_fallback_insights(assessment_data, compliance_result)

def generate_fallback_insights(assessment_data, compliance_result):
    """Generate fallback insights when Claude API is unavailable"""
    
    overall_score = compliance_result['overall_score']
    funding_stage = assessment_data.get('fundingStage', '')
    
    if overall_score >= 80:
        insights = "Strong compliance foundation with minimal gaps. Well-positioned for fundraising and enterprise sales."
    elif overall_score >= 65:
        insights = "Good compliance posture with some areas for improvement. Should not significantly impact fundraising timeline."
    else:
        insights = "Significant compliance gaps identified that require immediate attention before fundraising or enterprise sales."
    
    # Stage-specific recommendations
    stage_recommendations = {
        'pre-seed': [
            "Establish basic data privacy policies",
            "Document AI system architecture and data flow",
            "Implement user consent mechanisms",
            "Set up basic security controls",
            "Create privacy-by-design development practices"
        ],
        'seed': [
            "Complete comprehensive privacy impact assessment",
            "Implement data subject rights request procedures",
            "Enhance AI system documentation and testing",
            "Establish vendor compliance requirements",
            "Prepare investor-ready compliance documentation"
        ],
        'series-a': [
            "Conduct third-party compliance audit",
            "Implement advanced AI governance framework",
            "Establish compliance monitoring and reporting",
            "Complete industry-specific certifications",
            "Build compliance team and processes"
        ]
    }
    
    recommendations = stage_recommendations.get(funding_stage, stage_recommendations['seed'])
    
    return {
        "insights": insights,
        "recommendations": recommendations,
        "fundraising_impact": f"Compliance score of {overall_score}% is {'strong' if overall_score >= 75 else 'acceptable' if overall_score >= 60 else 'concerning'} for {funding_stage} stage fundraising.",
        "priority_actions": recommendations[:2]
    }

def get_score_status(score):
    """Get qualitative status based on numeric score"""
    if score >= 85:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 60:
        return "Fair"
    else:
        return "Needs Improvement"

def get_industry_benchmarks(data):
    """Get industry benchmark data"""
    industry = data.get('industry', 'b2b-saas')
    funding_stage = data.get('fundingStage', 'seed')
    
    # Mock benchmark data (in production, this would come from database)
    benchmarks = {
        'fintech': {
            'pre-seed': {'average': 65, 'top_quartile': 80},
            'seed': {'average': 72, 'top_quartile': 85},
            'series-a': {'average': 78, 'top_quartile': 90}
        },
        'healthtech': {
            'pre-seed': {'average': 70, 'top_quartile': 85},
            'seed': {'average': 75, 'top_quartile': 88},
            'series-a': {'average': 82, 'top_quartile': 92}
        },
        'b2b-saas': {
            'pre-seed': {'average': 68, 'top_quartile': 82},
            'seed': {'average': 74, 'top_quartile': 86},
            'series-a': {'average': 80, 'top_quartile': 91}
        }
    }
    
    industry_benchmarks = benchmarks.get(industry, benchmarks['b2b-saas'])
    stage_benchmarks = industry_benchmarks.get(funding_stage, industry_benchmarks['seed'])
    
    return {
        'industry_average': stage_benchmarks['average'],
        'top_quartile': stage_benchmarks['top_quartile'],
        'industry': industry,
        'stage': funding_stage
    }

def generate_assessment_id():
    """Generate unique assessment ID"""
    return f"assess_{int(time.time())}_{hash(str(time.time())) % 10000:04d}"

def store_assessment_result(assessment_data, result):
    """Store assessment result (placeholder for database storage)"""
    # In production, this would store to a database
    logger.info(f"Assessment completed for {assessment_data.get('companyName')} with score {result['overallScore']}%")

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    """Generate PDF compliance report"""
    try:
        data = request.get_json()
        assessment_data = data.get('assessmentData', {})
        results = data.get('results', {})
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#0a0f1c')
        )
        
        # Build PDF content
        story = []
        
        # Title
        company_name = assessment_data.get('companyName', 'Your Company')
        title = Paragraph(f"AI Compliance Assessment Report<br/>{company_name}", title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        summary_text = f"""
        This report provides a comprehensive analysis of {company_name}'s AI compliance posture 
        across key regulatory frameworks including GDPR, EU AI Act, and CCPA. 
        
        Overall Compliance Score: {results.get('overallScore', 0)}% ({results.get('scoreStatus', 'Unknown')})
        """
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Company Profile
        story.append(Paragraph("Company Profile", styles['Heading2']))
        profile_data = [
            ['Company Name', company_name],
            ['Funding Stage', assessment_data.get('fundingStage', 'Unknown').title()],
            ['Industry', assessment_data.get('industry', 'Unknown').title()],
            ['AI Use Cases', ', '.join(assessment_data.get('aiUseCases', []))],
            ['Data Types', ', '.join(assessment_data.get('dataTypes', []))],
            ['Target Markets', ', '.join(assessment_data.get('targetMarkets', []))]
        ]
        
        profile_table = Table(profile_data, colWidths=[2*inch, 4*inch])
        profile_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(profile_table)
        story.append(Spacer(1, 20))
        
        # Compliance Scores
        story.append(Paragraph("Compliance Framework Scores", styles['Heading2']))
        compliance = results.get('compliance', {})
        scores_data = [
            ['Framework', 'Score', 'Status'],
            ['GDPR', f"{compliance.get('gdpr', 0)}%", get_score_status(compliance.get('gdpr', 0))],
            ['EU AI Act', f"{compliance.get('euaiact', 0)}%", get_score_status(compliance.get('euaiact', 0))],
            ['CCPA', f"{compliance.get('ccpa', 0)}%", get_score_status(compliance.get('ccpa', 0))]
        ]
        
        scores_table = Table(scores_data, colWidths=[2.5*inch, 1*inch, 2.5*inch])
        scores_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(scores_table)
        story.append(Spacer(1, 20))
        
        # Recommendations
        story.append(Paragraph("Recommendations", styles['Heading2']))
        recommendations = results.get('recommendations', [])
        for i, rec in enumerate(recommendations[:5], 1):
            story.append(Paragraph(f"{i}. {rec}", styles['Normal']))
            story.append(Spacer(1, 6))
        
        story.append(Spacer(1, 20))
        
        # Footer
        footer_text = f"""
        Generated by NexusAI Compliance Platform on {datetime.now().strftime('%B %d, %Y')}
        
        This report is for informational purposes only and does not constitute legal advice.
        Please consult with qualified legal counsel for compliance matters.
        """
        story.append(Paragraph(footer_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{company_name.replace(' ', '_')}_Compliance_Report.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        return jsonify({'error': 'Report generation failed', 'details': str(e)}), 500

@app.route('/api/regulatory/latest', methods=['GET'])
def get_regulatory_updates():
    """Get latest regulatory updates"""
    try:
        # Mock regulatory updates (in production, this would come from regulatory APIs)
        updates = [
            {
                'id': 'eu-ai-act-2024-1',
                'title': 'EU AI Act Implementation Guidelines Published',
                'description': 'European Commission releases detailed implementation guidelines for high-risk AI systems.',
                'date': '2024-08-15',
                'impact': 'high',
                'frameworks': ['eu_ai_act'],
                'url': 'https://example.com/eu-ai-act-guidelines'
            },
            {
                'id': 'gdpr-update-2024-2',
                'title': 'GDPR Guidance on AI Decision Making',
                'description': 'Updated guidance on automated decision-making and profiling under GDPR.',
                'date': '2024-08-10',
                'impact': 'medium',
                'frameworks': ['gdpr'],
                'url': 'https://example.com/gdpr-ai-guidance'
            },
            {
                'id': 'ccpa-amendment-2024-1',
                'title': 'CCPA Amendments Affecting AI Systems',
                'description': 'New amendments to CCPA specifically addressing AI and machine learning systems.',
                'date': '2024-08-05',
                'impact': 'medium',
                'frameworks': ['ccpa'],
                'url': 'https://example.com/ccpa-ai-amendments'
            }
        ]
        
        return jsonify({
            'updates': updates,
            'last_updated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to fetch regulatory updates: {str(e)}")
        return jsonify({'error': 'Failed to fetch updates', 'details': str(e)}), 500

@app.route('/api/frameworks', methods=['GET'])
def get_compliance_frameworks():
    """Get available compliance frameworks"""
    return jsonify({
        'frameworks': COMPLIANCE_FRAMEWORKS,
        'risk_factors': RISK_FACTORS
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
