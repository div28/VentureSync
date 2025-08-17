from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import json
import re
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY')
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

if not CLAUDE_API_KEY:
    logger.warning("CLAUDE_API_KEY not found in environment variables - using fallback analysis")

# AI Agent Classes
class ComplianceStrategistAgent:
    """AI agent that creates personalized compliance strategies for AI startups"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.model = "claude-3-5-sonnet-20241022"
    
    def analyze_startup_profile(self, startup_data):
        """Analyze startup and create compliance strategy"""
        
        if not self.api_key:
            return self._fallback_analysis(startup_data)
        
        prompt = f"""
        You are a senior compliance strategist specializing in AI startups. Analyze this startup profile and create a comprehensive compliance assessment that will help them turn compliance into a competitive advantage for fundraising.

        STARTUP PROFILE:
        - Company: {startup_data.get('companyName', 'AI Startup')}
        - Funding Stage: {startup_data.get('fundingStage', 'Unknown')}
        - Team Size: {startup_data.get('teamSize', 'Unknown')}
        - AI System: {startup_data.get('aiDescription', 'AI system description not provided')}
        - Use Cases: {', '.join(startup_data.get('useCases', []))}
        - Data Types: {', '.join(startup_data.get('dataTypes', []))}
        - Target Industries: {', '.join(startup_data.get('industries', []))}
        - Operating Regions: {', '.join(startup_data.get('regions', []))}
        - Fundraising Timeline: {startup_data.get('fundraising', 'Unknown')}

        ANALYSIS REQUIREMENTS:
        1. Focus on stage-appropriate compliance (don't overwhelm pre-seed with enterprise requirements)
        2. Identify investor red flags that could kill fundraising
        3. Highlight competitive advantages compliance can create
        4. Provide realistic timelines and costs
        5. Consider industry-specific regulations

        Respond with a JSON object with these exact keys:
        {{
            "compliance_score": <number 1-100>,
            "investor_score": <number 1-100>,
            "risk_level": "<LOW/MEDIUM/HIGH>",
            "stage_assessment": "<analysis of what compliance makes sense for their stage>",
            "investor_readiness": "<assessment of VC due diligence readiness>",
            "competitive_advantages": ["<ways compliance can differentiate them>"],
            "key_risks": ["<top 3 compliance risks>"],
            "recommendations": [
                {{
                    "priority": "<high/medium/low>",
                    "title": "<specific recommendation>",
                    "description": "<what they need to do>",
                    "timeline": "<realistic timeframe>",
                    "cost": "<cost estimate>",
                    "impact": "<why this matters for fundraising/business>"
                }}
            ],
            "benchmarks": {{
                "industry_percentile": <number 1-100>,
                "time_to_compliance": "<weeks>",
                "estimated_investment": "<dollar range>",
                "success_probability": "<percentage>"
            }}
        }}

        Be specific about costs and timelines. Focus on recommendations that actually help with fundraising.
        """
        
        try:
            response = requests.post(
                CLAUDE_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": self.model,
                    "max_tokens": 2500,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['content'][0]['text']
                
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                    logger.info(f"Successfully analyzed startup: {startup_data.get('companyName')}")
                    return analysis
                else:
                    logger.error("No valid JSON found in Claude response")
                    return self._fallback_analysis(startup_data)
            else:
                logger.error(f"Claude API error: {response.status_code} - {response.text}")
                return self._fallback_analysis(startup_data)
                
        except requests.exceptions.Timeout:
            logger.error("Claude API timeout")
            return self._fallback_analysis(startup_data)
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return self._fallback_analysis(startup_data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return self._fallback_analysis(startup_data)
        except Exception as e:
            logger.error(f"Unexpected error in compliance analysis: {str(e)}")
            return self._fallback_analysis(startup_data)
    
    def _fallback_analysis(self, startup_data):
        """Fallback analysis using rule-based logic"""
        
        # Base scoring
        compliance_score = 50
        investor_score = 40
        
        # Adjust based on funding stage
        stage_adjustments = {
            'pre-seed': {'compliance': -10, 'investor': -15},
            'seed': {'compliance': 0, 'investor': 0},
            'series-a': {'compliance': 10, 'investor': 15},
            'series-b': {'compliance': 20, 'investor': 25},
            'growth': {'compliance': 30, 'investor': 35}
        }
        
        stage = startup_data.get('fundingStage', 'seed')
        if stage in stage_adjustments:
            compliance_score += stage_adjustments[stage]['compliance']
            investor_score += stage_adjustments[stage]['investor']
        
        # Industry risk adjustments
        high_risk_industries = ['healthcare', 'finance', 'hr']
        medium_risk_industries = ['education', 'retail']
        
        industries = startup_data.get('industries', [])
        if any(industry in high_risk_industries for industry in industries):
            compliance_score -= 20
            investor_score -= 15
        elif any(industry in medium_risk_industries for industry in industries):
            compliance_score -= 10
            investor_score -= 5
        
        # Data sensitivity adjustments
        sensitive_data = ['health', 'financial', 'biometric']
        personal_data = ['personal', 'behavioral', 'location']
        
        data_types = startup_data.get('dataTypes', [])
        if any(data_type in sensitive_data for data_type in data_types):
            compliance_score -= 15
            investor_score -= 10
        elif any(data_type in personal_data for data_type in data_types):
            compliance_score -= 5
            investor_score -= 5
        
        # Geographic complexity
        regions = startup_data.get('regions', [])
        if 'eu' in regions:
            compliance_score -= 10
        if len(regions) > 2:
            compliance_score -= 5
        
        # AI use case complexity
        high_risk_use_cases = ['decision', 'automation']
        use_cases = startup_data.get('useCases', [])
        if any(use_case in high_risk_use_cases for use_case in use_cases):
            compliance_score -= 10
            investor_score -= 5
        
        # Cap scores
        compliance_score = max(15, min(90, compliance_score))
        investor_score = max(10, min(85, investor_score))
        
        # Determine risk level
        if compliance_score < 40:
            risk_level = "HIGH"
        elif compliance_score < 65:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Generate recommendations
        recommendations = self._generate_recommendations(startup_data, compliance_score)
        
        return {
            "compliance_score": compliance_score,
            "investor_score": investor_score,
            "risk_level": risk_level,
            "stage_assessment": f"For {stage} stage, focus on foundational compliance elements",
            "investor_readiness": "Conditional - address key gaps for investor confidence",
            "competitive_advantages": [
                "Proactive compliance approach shows maturity",
                "Risk mitigation attracts conservative investors",
                "Compliance-first culture enables enterprise sales"
            ],
            "key_risks": [
                "Privacy policy gaps could block data collection",
                "Industry regulations may limit market access",
                "Investor due diligence could reveal compliance gaps"
            ],
            "recommendations": recommendations,
            "benchmarks": {
                "industry_percentile": max(25, compliance_score - 10),
                "time_to_compliance": "8-12 weeks" if compliance_score < 60 else "4-6 weeks",
                "estimated_investment": "$25,000 - $45,000" if compliance_score < 60 else "$15,000 - $25,000",
                "success_probability": f"{min(85, max(35, investor_score + 10))}%"
            }
        }
    
    def _generate_recommendations(self, startup_data, compliance_score):
        """Generate stage and industry-appropriate recommendations"""
        recommendations = []
        
        # Always needed foundational items
        recommendations.append({
            "priority": "high",
            "title": "Privacy Policy & Terms of Service",
            "description": "Implement comprehensive privacy policy and terms of service tailored to your AI system",
            "timeline": "2-3 weeks",
            "cost": "$2,500 - $4,000",
            "impact": "Required for legal data collection and investor confidence"
        })
        
        recommendations.append({
            "priority": "high",
            "title": "Data Processing Agreements",
            "description": "Create standardized customer data processing agreements",
            "timeline": "1-2 weeks",
            "cost": "$1,200 - $2,000",
            "impact": "Enables B2B customer trust and contract execution"
        })
        
        # Industry-specific recommendations
        industries = startup_data.get('industries', [])
        
        if 'healthcare' in industries or 'health' in startup_data.get('dataTypes', []):
            recommendations.append({
                "priority": "high",
                "title": "HIPAA Compliance Assessment",
                "description": "Healthcare data requires HIPAA compliance evaluation and implementation",
                "timeline": "6-8 weeks",
                "cost": "$12,000 - $18,000",
                "impact": "Critical for healthcare market access - required by all health customers"
            })
        
        if 'finance' in industries or 'financial' in startup_data.get('dataTypes', []):
            recommendations.append({
                "priority": "high",
                "title": "Financial Services Compliance",
                "description": "SOX, PCI DSS, and financial regulation compliance assessment",
                "timeline": "8-12 weeks",
                "cost": "$15,000 - $25,000",
                "impact": "Required for financial services customers and reduces liability"
            })
        
        if 'hr' in industries or any(use_case in ['decision', 'automation'] for use_case in startup_data.get('useCases', [])):
            recommendations.append({
                "priority": "high",
                "title": "Algorithmic Bias Audit",
                "description": "Third-party bias testing required for hiring/decision-making AI",
                "timeline": "3-4 weeks",
                "cost": "$6,000 - $10,000",
                "impact": "VC requirement - 89% of investors require bias audits for decision AI"
            })
        
        # Geographic compliance
        regions = startup_data.get('regions', [])
        if 'eu' in regions:
            recommendations.append({
                "priority": "medium",
                "title": "GDPR Compliance Framework",
                "description": "Implement GDPR-compliant data handling for European operations",
                "timeline": "6-8 weeks",
                "cost": "$10,000 - $15,000",
                "impact": "Required for EU market - up to 4% revenue fines for violations"
            })
        
        # Stage-based recommendations
        stage = startup_data.get('fundingStage', '')
        fundraising = startup_data.get('fundraising', '')
        
        if stage in ['series-a', 'series-b'] or fundraising in ['0-6', '6-12']:
            recommendations.append({
                "priority": "medium",
                "title": "SOC2 Type II Certification",
                "description": "Security certification increasingly required by enterprise customers and VCs",
                "timeline": "3-4 months",
                "cost": "$12,000 - $20,000",
                "impact": "25% valuation premium with certification, required for enterprise sales"
            })
        
        # Return top 5 recommendations
        return recommendations[:5]


# Initialize AI agent
compliance_agent = ComplianceStrategistAgent(CLAUDE_API_KEY)

# Helper functions
def calculate_benchmarks(compliance_score, investor_score, startup_data):
    """Calculate industry benchmarks for comparison"""
    
    # Industry percentile based on compliance score
    industry_percentile = max(15, min(95, compliance_score - 5))
    
    # Time to compliance based on current score
    if compliance_score >= 70:
        time_to_compliance = "4-6 weeks"
    elif compliance_score >= 50:
        time_to_compliance = "8-12 weeks"
    else:
        time_to_compliance = "12-20 weeks"
    
    # Investment estimate based on gaps
    if compliance_score >= 70:
        investment_range = "$8,000 - $15,000"
    elif compliance_score >= 50:
        investment_range = "$15,000 - $30,000"
    else:
        investment_range = "$30,000 - $50,000"
    
    # Success probability based on investor score
    success_probability = f"{min(90, max(25, investor_score + 15))}%"
    
    return {
        "industry_percentile": f"{industry_percentile}th",
        "time_to_compliance": time_to_compliance,
        "estimated_investment": investment_range,
        "success_probability": success_probability
    }

def generate_executive_summary(analysis_data, startup_data):
    """Generate executive summary from analysis"""
    
    return {
        "compliance_score": analysis_data.get("compliance_score", 50),
        "investor_score": analysis_data.get("investor_score", 40),
        "risk_level": analysis_data.get("risk_level", "MEDIUM"),
        "investment_readiness": analysis_data.get("investor_readiness", "Conditional"),
        "key_recommendations": analysis_data.get("recommendations", [])[:3],
        "estimated_investment": analysis_data.get("benchmarks", {}).get("estimated_investment", "$20,000 - $35,000"),
        "timeline_to_readiness": analysis_data.get("benchmarks", {}).get("time_to_compliance", "8-12 weeks"),
        "competitive_positioning": "Compliance-forward approach differentiates from 73% of AI startups"
    }

# Routes
@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "FounderShield API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "claude_api_available": bool(CLAUDE_API_KEY)
    })

@app.route('/api/analyze-compliance', methods=['POST'])
def analyze_compliance():
    """Main compliance analysis endpoint"""
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ['companyName', 'fundingStage', 'aiDescription']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        logger.info(f"Starting analysis for {data.get('companyName')} ({data.get('fundingStage')} stage)")
        
        # Run AI agent analysis
        analysis = compliance_agent.analyze_startup_profile(data)
        
        # Generate analysis ID
        analysis_id = f"FA-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create comprehensive result
        result = {
            "analysis_id": analysis_id,
            "timestamp": datetime.now().isoformat(),
            "company_profile": {
                "name": data.get('companyName'),
                "stage": data.get('fundingStage'),
                "team_size": data.get('teamSize'),
                "industries": data.get('industries', []),
                "regions": data.get('regions', []),
                "ai_description": data.get('aiDescription')
            },
            "compliance_analysis": analysis,
            "executive_summary": generate_executive_summary(analysis, data),
            "benchmarks": calculate_benchmarks(
                analysis.get('compliance_score', 50),
                analysis.get('investor_score', 40),
                data
            )
        }
        
        logger.info(f"Analysis completed for {data.get('companyName')} - Compliance: {analysis.get('compliance_score')}, Investor: {analysis.get('investor_score')}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in compliance analysis: {str(e)}")
        return jsonify({
            "error": "Analysis failed",
            "message": "Unable to complete analysis. Please try again."
        }), 500

@app.route('/api/generate-roadmap', methods=['POST'])
def generate_roadmap():
    """Generate implementation roadmap based on analysis"""
    try:
        data = request.get_json()
        
        if not data or not data.get('analysis_id'):
            return jsonify({"error": "Analysis ID required"}), 400
        
        # Get assessment data
        assessment_data = data.get('assessment_data', {})
        
        # Generate roadmap based on startup stage and industry
        roadmap = generate_compliance_roadmap(assessment_data)
        
        logger.info(f"Roadmap generated for analysis {data.get('analysis_id')}")
        return jsonify(roadmap)
        
    except Exception as e:
        logger.error(f"Error generating roadmap: {str(e)}")
        return jsonify({
            "error": "Roadmap generation failed",
            "message": "Unable to generate roadmap. Please try again."
        }), 500

def generate_compliance_roadmap(assessment_data):
    """Generate a detailed implementation roadmap"""
    
    stage = assessment_data.get('fundingStage', 'seed')
    industries = assessment_data.get('industries', [])
    regions = assessment_data.get('regions', [])
    
    phases = []
    total_cost = 0
    
    # Phase 1: Foundation (Always needed)
    foundation_tasks = [
        {
            "task": "Privacy Policy & Terms of Service",
            "description": "Implement comprehensive privacy policy tailored to AI system",
            "effort": "2-3 weeks",
            "cost": 3000,
            "dependencies": []
        },
        {
            "task": "Data Processing Agreements",
            "description": "Create customer data processing agreements",
            "effort": "1-2 weeks",
            "cost": 1500,
            "dependencies": ["Privacy Policy"]
        }
    ]
    
    phases.append({
        "phase": "Foundation (Weeks 1-4)",
        "priority": "high",
        "description": "Essential legal and policy framework",
        "tasks": foundation_tasks
    })
    
    phase1_cost = sum(task['cost'] for task in foundation_tasks)
    total_cost += phase1_cost
    
    # Phase 2: Industry-Specific Compliance
    industry_tasks = []
    
    if 'healthcare' in industries:
        industry_tasks.append({
            "task": "HIPAA Compliance Implementation",
            "description": "Healthcare data protection and privacy compliance",
            "effort": "6-8 weeks",
            "cost": 15000,
            "dependencies": ["Data Processing Agreements"]
        })
    
    if 'finance' in industries:
        industry_tasks.append({
            "task": "Financial Services Compliance",
            "description": "SOX, PCI DSS, and financial regulation compliance",
            "effort": "8-10 weeks",
            "cost": 18000,
            "dependencies": ["Foundation phase"]
        })
    
    if 'hr' in industries:
        industry_tasks.append({
            "task": "Algorithmic Bias Audit",
            "description": "Third-party bias testing and certification",
            "effort": "3-4 weeks",
            "cost": 8000,
            "dependencies": ["Privacy Policy"]
        })
    
    if 'eu' in regions:
        industry_tasks.append({
            "task": "GDPR Compliance Framework",
            "description": "European data protection regulation compliance",
            "effort": "6-8 weeks",
            "cost": 12000,
            "dependencies": ["Data Processing Agreements"]
        })
    
    if industry_tasks:
        phases.append({
            "phase": "Industry Compliance (Weeks 5-12)",
            "priority": "high",
            "description": "Industry and region-specific requirements",
            "tasks": industry_tasks
        })
        
        phase2_cost = sum(task['cost'] for task in industry_tasks)
        total_cost += phase2_cost
    
    # Phase 3: Investment Readiness (for Series A+ or active fundraising)
    if stage in ['series-a', 'series-b'] or assessment_data.get('fundraising') in ['0-6', '6-12']:
        investment_tasks = [
            {
                "task": "SOC2 Type II Certification",
                "description": "Security certification for enterprise customers",
                "effort": "12-16 weeks",
                "cost": 15000,
                "dependencies": ["Industry Compliance"]
            },
            {
                "task": "Investor Documentation Package",
                "description": "Complete compliance documentation for due diligence",
                "effort": "2-3 weeks",
                "cost": 4000,
                "dependencies": ["All previous phases"]
            },
            {
                "task": "Legal Review & Validation",
                "description": "External legal counsel review of all documentation",
                "effort": "2-3 weeks",
                "cost": 6000,
                "dependencies": ["Investor Documentation"]
            }
        ]
        
        phases.append({
            "phase": "Investment Readiness (Weeks 13-20)",
            "priority": "medium",
            "description": "Preparation for due diligence and enterprise sales",
            "tasks": investment_tasks
        })
        
        phase3_cost = sum(task['cost'] for task in investment_tasks)
        total_cost += phase3_cost
    
    # Calculate timeline
    max_timeline = 20 if len(phases) > 2 else 12 if len(phases) > 1 else 4
    
    return {
        "roadmap_id": f"RM-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "company": assessment_data.get('companyName', 'AI Startup'),
        "generated_date": datetime.now().isoformat(),
        "phases": phases,
        "summary": {
            "total_phases": len(phases),
            "total_timeline": f"{max_timeline} weeks",
            "total_investment": f"${total_cost:,}",
            "critical_path": "Privacy Policy → Industry Compliance → Investor Readiness"
        },
        "milestone_gates": [
            "Foundation compliance operational",
            "Industry-specific requirements met",
            "Investor due diligence ready"
        ],
        "success_metrics": [
            "Legal risk reduced by 80%",
            "Investor confidence increased",
            "Enterprise customer ready",
            "Regulatory audit prepared"
        ]
    }

@app.route('/api/benchmark-data', methods=['POST'])
def get_benchmark_data():
    """Get industry benchmark data for comparison"""
    try:
        data = request.get_json() or {}
        
        industry = data.get('industry', 'general')
        stage = data.get('stage', 'seed')
        
        # Industry-specific benchmarks
        industry_benchmarks = {
            "healthcare": {"avg_score": 52, "avg_investment": "$35,000", "violation_rate": "18%"},
            "finance": {"avg_score": 58, "avg_investment": "$42,000", "violation_rate": "22%"},
            "hr": {"avg_score": 48, "avg_investment": "$28,000", "violation_rate": "15%"},
            "retail": {"avg_score": 62, "avg_investment": "$22,000", "violation_rate": "10%"},
            "education": {"avg_score": 55, "avg_investment": "$25,000", "violation_rate": "12%"},
            "general": {"avg_score": 54, "avg_investment": "$30,000", "violation_rate": "14%"}
        }
        
        # Stage-specific benchmarks
        stage_benchmarks = {
            "pre-seed": {"compliance_score": 35, "investment": "$8,000", "timeline": "6-8 weeks"},
            "seed": {"compliance_score": 48, "investment": "$18,000", "timeline": "8-12 weeks"},
            "series-a": {"compliance_score": 67, "investment": "$35,000", "timeline": "12-16 weeks"},
            "series-b": {"compliance_score": 78, "investment": "$65,000", "timeline": "16-24 weeks"},
            "growth": {"compliance_score": 85, "investment": "$100,000", "timeline": "24-32 weeks"}
        }
        
        current_industry = industry_benchmarks.get(industry, industry_benchmarks["general"])
        current_stage = stage_benchmarks.get(stage, stage_benchmarks["seed"])
        
        benchmarks = {
            "industry_averages": {
                "compliance_score": current_industry["avg_score"],
                "average_investment": current_industry["avg_investment"],
                "violation_rate": current_industry["violation_rate"]
            },
            "stage_comparison": current_stage,
            "success_factors": [
                "Proactive compliance increases fundraising success by 45%",
                "Companies with bias audits raise 30% more capital on average",
                "GDPR compliance adds 15-20% valuation premium for EU market",
                "SOC2 certification reduces enterprise sales cycle by 40%",
                "Privacy-first startups see 25% higher customer trust scores"
            ],
            "market_insights": {
                "regulatory_trend": "Increasing enforcement with 35% more AI-related fines in 2024",
                "investor_focus": "89% of VCs now require compliance review in due diligence",
                "competitive_advantage": "Only 27% of AI startups have proactive compliance",
                "enterprise_requirement": "92% of Fortune 500 companies require vendor compliance certification"
            }
        }
        
        return jsonify(benchmarks)
        
    except Exception as e:
        logger.error(f"Error fetching benchmark data: {str(e)}")
        return jsonify({
            "error": "Benchmark data unavailable",
            "message": "Unable to fetch benchmark data. Please try again."
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "message": "The requested endpoint does not exist"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "error": "Bad request",
        "message": "Invalid request data"
    }), 400

# Run the application
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
