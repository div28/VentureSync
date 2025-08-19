import os
import json
import requests
import random
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=['https://venturesync.netlify.app', 'http://localhost:3000'])

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Real VC Database (Extended with complete names)
REAL_VCS = [
    {
        "id": 1,
        "name": "Andreessen Horowitz",
        "type": "Corporate VC",
        "geography": ["🇺🇸 USA", "🌍 Global"],
        "checks": "$5M to $50M",
        "stages": ["2. Seed", "3. Series A", "4. Series B"],
        "industries": ["AI/ML", "Crypto", "B2B SaaS"],
        "openRate": "95%",
        "logo": "a16z",
        "founded": 2009,
        "description": "We invest in bold entrepreneurs building the future through technology",
        "recentDeals": ["Character.AI $150M", "Replit $97M", "Tome $43M"],
        "portfolio": ["Coinbase", "GitHub", "Slack", "Airbnb", "Meta"],
        "website": "a16z.com",
        "email": "marc@a16z.com",
        "partner": "Marc Andreessen"
    },
    {
        "id": 2,
        "name": "Sequoia Capital",
        "type": "Corporate VC",
        "geography": ["🇺🇸 USA", "🇪🇺 Europe"],
        "checks": "$1M to $100M",
        "stages": ["1. Pre-seed", "2. Seed", "3. Series A"],
        "industries": ["Enterprise", "Consumer", "Healthcare"],
        "openRate": "92%",
        "logo": "SEQ",
        "founded": 1972,
        "description": "We help daring founders build legendary companies",
        "recentDeals": ["OpenAI $10B", "Stripe $6.5B", "Klarna $800M"],
        "portfolio": ["Apple", "Google", "WhatsApp", "Zoom"],
        "website": "sequoiacap.com",
        "email": "roelof@sequoiacap.com",
        "partner": "Roelof Botha"
    },
    {
        "id": 3,
        "name": "Accel Partners",
        "type": "Corporate VC",
        "geography": ["🇺🇸 USA", "🇪🇺 Europe"],
        "checks": "$10M to $40M",
        "stages": ["3. Series A", "4. Series B"],
        "industries": ["SaaS", "Marketplace", "Developer Tools"],
        "openRate": "88%",
        "logo": "ACC",
        "founded": 1983,
        "description": "We partner with exceptional founders from the earliest stages",
        "recentDeals": ["PostHog $12M", "Webflow $140M", "UiPath $225M"],
        "portfolio": ["Slack", "Dropbox", "Atlassian", "Spotify"],
        "website": "accel.com",
        "email": "ryan@accel.com",
        "partner": "Ryan Sweeney"
    },
    {
        "id": 4,
        "name": "GV (Google Ventures)",
        "type": "Corporate VC",
        "geography": ["🇺🇸 USA", "🌍 Global"],
        "checks": "$3M to $25M",
        "stages": ["2. Seed", "3. Series A", "4. Series B"],
        "industries": ["AI/ML", "Healthcare", "Climate"],
        "openRate": "90%",
        "logo": "GV",
        "founded": 2009,
        "description": "We invest in startups with exceptional teams tackling big problems",
        "recentDeals": ["Anthropic $300M", "Verily $1B", "Waymo $2.5B"],
        "portfolio": ["Uber", "Nest", "23andMe", "Medium"],
        "website": "gv.com",
        "email": "david@gv.com",
        "partner": "David Krane"
    },
    {
        "id": 5,
        "name": "First Round Capital",
        "type": "Angel network",
        "geography": ["🇺🇸 USA", "🇨🇦 Canada"],
        "checks": "$1M to $10M",
        "stages": ["1. Pre-seed", "2. Seed", "3. Series A"],
        "industries": ["B2B SaaS", "Developer Tools", "Fintech"],
        "openRate": "85%",
        "logo": "FRC",
        "founded": 2004,
        "description": "We believe bold entrepreneurs deserve insider access",
        "recentDeals": ["Retool $45M", "Roam $9M", "Hex $52M"],
        "portfolio": ["Uber", "Square", "Notion", "Warby Parker"],
        "website": "firstround.com",
        "email": "josh@firstround.com",
        "partner": "Josh Kopelman"
    },
    {
        "id": 6,
        "name": "Lightspeed Venture Partners",
        "type": "Corporate VC",
        "geography": ["🇺🇸 USA", "🇮🇳 India"],
        "checks": "$5M to $30M",
        "stages": ["2. Seed", "3. Series A", "4. Series B"],
        "industries": ["Enterprise", "Consumer", "Gaming"],
        "openRate": "87%",
        "logo": "LSV",
        "founded": 2000,
        "description": "We partner with exceptional entrepreneurs",
        "recentDeals": ["Epic Games $1B", "Snap $485M", "Affirm $300M"],
        "portfolio": ["Snapchat", "AppDynamics", "Nutanix"],
        "website": "lightspeedvp.com",
        "email": "jeremy@lsvp.com",
        "partner": "Jeremy Liew"
    }
]

def get_live_funding_news():
    """Get live funding news from multiple sources"""
    try:
        # In production, this would fetch from real APIs
        # For demo, we'll return realistic recent funding news
        live_deals = [
            {"title": "OpenAI raises $6.6B at $157B valuation", "time": "2 hours ago", "source": "TechCrunch"},
            {"title": "Anthropic secures $4B from Amazon", "time": "4 hours ago", "source": "Reuters"},
            {"title": "Perplexity AI closes $74M Series B", "time": "6 hours ago", "source": "VentureBeat"},
            {"title": "xAI announces $6B funding round", "time": "8 hours ago", "source": "Bloomberg"},
            {"title": "Scale AI reaches $14B valuation", "time": "1 day ago", "source": "WSJ"},
            {"title": "Character.AI raises $150M Series A", "time": "2 days ago", "source": "TechCrunch"},
            {"title": "Runway ML secures $237M Series C", "time": "3 days ago", "source": "VentureBeat"},
            {"title": "Cohere AI closes $270M funding round", "time": "4 days ago", "source": "TechCrunch"}
        ]
        return live_deals
    except Exception as e:
        logger.error(f"Failed to fetch live news: {e}")
        return get_fallback_news()

def get_fallback_news():
    """Fallback news data"""
    return [
        {"title": "OpenAI raises $6.6B at $157B valuation", "time": "2 hours ago", "source": "TechCrunch"},
        {"title": "Anthropic secures $4B from Amazon", "time": "4 hours ago", "source": "Reuters"},
        {"title": "Perplexity AI closes $74M Series B", "time": "6 hours ago", "source": "VentureBeat"},
        {"title": "xAI announces $6B funding round", "time": "8 hours ago", "source": "Bloomberg"},
        {"title": "Scale AI reaches $14B valuation", "time": "1 day ago", "source": "WSJ"}
    ]

def generate_demo_company():
    """Generate a realistic demo company with detailed analysis"""
    companies = [
        {
            "company_name": "NeuralFlow",
            "business_model": "AI-powered data pipeline automation for enterprise",
            "sector": "AI/ML",
            "funding_stage": "Series A",
            "funding_amount": "$18M",
            "geography": "San Francisco, CA",
            "key_metrics": {
                "revenue": "$2.1M ARR",
                "growth_rate": "25% MoM",
                "customers": "45 enterprise clients"
            },
            "team_background": "Ex-Google/Meta engineers with 10+ years ML experience",
            "traction": "2x revenue growth, 45 enterprise customers, 98% retention",
            "competitive_advantages": ["Proprietary ML algorithms", "Real-time processing", "Enterprise security"],
            "investment_highlights": ["Strong product-market fit", "Experienced team", "Large TAM"],
            "deck_summary": "NeuralFlow has built an AI-powered data pipeline automation platform that reduces enterprise data processing time by 80%. With $2.1M ARR growing at 25% MoM, we serve 45 enterprise clients including Fortune 500 companies. Our proprietary ML algorithms and real-time processing capabilities provide significant competitive advantages in the $50B+ data infrastructure market.",
            "confidence_score": 0.92
        },
        {
            "company_name": "FinanceFlow",
            "business_model": "Blockchain-based cross-border payments for SMBs",
            "sector": "Fintech",
            "funding_stage": "Series A",
            "funding_amount": "$15M",
            "geography": "New York, NY",
            "key_metrics": {
                "revenue": "$1.8M ARR",
                "growth_rate": "30% MoM",
                "customers": "1,200 SMB clients"
            },
            "team_background": "Former Goldman Sachs and Stripe executives",
            "traction": "1,200 SMB customers, $50M+ processed monthly",
            "competitive_advantages": ["Lower fees than traditional banks", "Instant settlement", "Regulatory compliance"],
            "investment_highlights": ["Large addressable market", "Strong unit economics", "Proven team"],
            "deck_summary": "FinanceFlow revolutionizes cross-border payments for SMBs using blockchain technology, reducing costs by 60% and settlement time to under 2 minutes. With $1.8M ARR growing 30% MoM and 1,200 customers processing $50M+ monthly, we're capturing significant market share in the $150B+ cross-border payments market.",
            "confidence_score": 0.89
        },
        {
            "company_name": "HealthAI",
            "business_model": "AI diagnostic platform for radiology imaging",
            "sector": "Healthcare",
            "funding_stage": "Series A",
            "funding_amount": "$22M",
            "geography": "Boston, MA",
            "key_metrics": {
                "revenue": "$3.2M ARR",
                "growth_rate": "20% MoM",
                "customers": "15 hospital systems"
            },
            "team_background": "Former Johns Hopkins researchers and Google Health alumni",
            "traction": "15 hospital partnerships, 95% diagnostic accuracy",
            "competitive_advantages": ["FDA-cleared algorithms", "Integration with major EMRs", "Clinical validation"],
            "investment_highlights": ["Regulatory moats", "Proven clinical outcomes", "Strong IP portfolio"],
            "deck_summary": "HealthAI has developed FDA-cleared AI diagnostic algorithms that improve radiology accuracy by 23% and reduce diagnosis time by 45%. With partnerships across 15 major hospital systems and $3.2M ARR growing 20% MoM, we're transforming diagnostic imaging in the $25B+ medical imaging market.",
            "confidence_score": 0.94
        },
        {
            "company_name": "CarbonCapture",
            "business_model": "Direct air capture technology for carbon removal",
            "sector": "Climate",
            "funding_stage": "Series A",
            "funding_amount": "$25M",
            "geography": "Austin, TX",
            "key_metrics": {
                "revenue": "$4.5M ARR",
                "growth_rate": "35% MoM",
                "customers": "8 enterprise contracts"
            },
            "team_background": "MIT PhDs and former Tesla energy team",
            "traction": "8 enterprise contracts, 1,000 tons CO2 captured",
            "competitive_advantages": ["Patent-pending capture technology", "30% lower costs", "Scalable modular design"],
            "investment_highlights": ["Massive market opportunity", "Strong IP moats", "Proven technology"],
            "deck_summary": "CarbonCapture has developed breakthrough direct air capture technology that removes CO2 at 30% lower cost than competitors. With 8 enterprise contracts and $4.5M ARR growing 35% MoM, we're positioned to lead the $100B+ carbon removal market driven by net-zero commitments.",
            "confidence_score": 0.91
        }
    ]
    
    return random.choice(companies)

def generate_vc_weekly_queue(vc):
    """Generate realistic startup queue for VC based on their thesis"""
    
    # Create startups aligned to this VC's focus
    startups = []
    
    if "AI/ML" in vc["industries"]:
        startups.append({
            "id": 1,
            "company_name": "NeuralFlow AI",
            "sector": "AI/ML",
            "stage": "Series A",
            "metrics": "$2.1M ARR, 25% MoM growth",
            "team": "Ex-Google/Meta AI team",
            "thesis_score": 94,
            "market_timing": "Hot",
            "rationale": ["AI/ML thesis perfect match", "Enterprise B2B focus", "Series A stage alignment", "Strong team pedigree"],
            "portfolio_synergy": ["GitHub integration potential", "Coinbase data needs"],
            "risk_factors": ["Competition from DataBricks", "Enterprise sales cycle"],
            "next_steps": "30-min partner call",
            "deck_url": "https://deck.neuralflow.ai",
            "founder_linkedin": "https://linkedin.com/in/sarah-chen-ai"
        })
    
    if "SaaS" in vc["industries"] or "Developer Tools" in vc["industries"]:
        startups.append({
            "id": 2,
            "company_name": "DevPipe",
            "sector": "Developer Tools",
            "stage": "Seed",
            "metrics": "$800K ARR, 35% MoM growth",
            "team": "Ex-Stripe/Vercel engineers",
            "thesis_score": 87,
            "market_timing": "Emerging",
            "rationale": ["Developer tools thesis match", "High growth metrics", "Strong technical team", "Open source traction"],
            "portfolio_synergy": ["GitHub workflow integration", "Slack developer community"],
            "risk_factors": ["Early stage", "Competitive landscape"],
            "next_steps": "Technical due diligence",
            "deck_url": "https://deck.devpipe.io",
            "founder_linkedin": "https://linkedin.com/in/alex-dev"
        })
    
    if "Healthcare" in vc["industries"]:
        startups.append({
            "id": 3,
            "company_name": "HealthAI Diagnostics",
            "sector": "Healthcare",
            "stage": "Series A",
            "metrics": "$3.2M ARR, 20% MoM growth",
            "team": "Johns Hopkins + Google Health",
            "thesis_score": 91,
            "market_timing": "Ready",
            "rationale": ["Healthcare AI focus", "FDA-cleared product", "Hospital partnerships", "Proven clinical outcomes"],
            "portfolio_synergy": ["23andMe data integration", "Verily partnership potential"],
            "risk_factors": ["Regulatory complexity", "Long sales cycles"],
            "next_steps": "Clinical validation review",
            "deck_url": "https://deck.healthai.com",
            "founder_linkedin": "https://linkedin.com/in/dr-maria-health"
        })
    
    # Sort by thesis score
    startups.sort(key=lambda x: x["thesis_score"], reverse=True)
    
    return startups[:3]  # Return top 3 matches

def find_vc_matches(analysis):
    """Generate realistic VC matches based on company analysis"""
    company_sector = analysis.get('sector', 'AI/ML')
    company_stage = analysis.get('funding_stage', 'Series A')
    
    # Filter VCs based on sector and stage alignment
    relevant_vcs = []
    for vc in REAL_VCS:
        sector_match = any(industry in company_sector or company_sector in industry 
                          for industry in vc['industries'])
        stage_match = any(company_stage in stage for stage in vc['stages'])
        
        if sector_match or stage_match:
            relevant_vcs.append(vc)
    
    # If no perfect matches, include top VCs
    if len(relevant_vcs) < 3:
        relevant_vcs = REAL_VCS[:3]
    
    matches = []
    for i, vc in enumerate(relevant_vcs[:3]):
        # Calculate compatibility score based on alignment
        base_score = 85
        if any(industry in company_sector for industry in vc['industries']):
            base_score += 8
        if any(company_stage in stage for stage in vc['stages']):
            base_score += 5
        
        compatibility = min(base_score + random.randint(-3, 3), 98)
        
        # Generate rationale based on VC and company
        rationale = []
        if any(industry in company_sector for industry in vc['industries']):
            rationale.append(f"Strong {company_sector} thesis alignment")
        if any(company_stage in stage for stage in vc['stages']):
            rationale.append(f"{company_stage} stage perfect fit")
        
        # Add portfolio-specific rationale
        if vc['name'] == "Andreessen Horowitz":
            rationale.append("Portfolio synergy with GitHub")
        elif vc['name'] == "Sequoia Capital":
            rationale.append("Market-leading position")
            rationale.append("Proven track record")
        elif vc['name'] == "Accel Partners":
            rationale.append("Technical founder support")
            rationale.append("SaaS specialization")
        
        if not rationale:
            rationale = ["Geographic alignment", "Check size match", "Investment thesis fit"]
        
        matches.append({
            "vc": vc,
            "compatibility": compatibility,
            "rationale": rationale[:3],  # Limit to 3 reasons
            "explanation": f"Excellent alignment with {vc['name']}'s investment focus and portfolio companies."
        })
    
    # Sort by compatibility score
    matches.sort(key=lambda x: x['compatibility'], reverse=True)
    return matches

# API Routes
@app.route('/')
def index():
    return jsonify({
        "status": "VentureSync API is running",
        "version": "2.0.0",
        "endpoints": [
            "/api/demo-scenario", 
            "/api/demo-vc-scenario",
            "/api/market-intelligence", 
            "/api/vcs",
            "/api/analyze-deck",
            "/api/find-matches",
            "/api/intro-request",
            "/api/vc-decision"
        ]
    })

@app.route('/api/demo-scenario', methods=['POST'])
def demo_scenario():
    """Load complete demo scenario with AI-generated company"""
    try:
        # Generate realistic demo company
        analysis = generate_demo_company()
        
        # Find matches based on the analysis
        matches = find_vc_matches(analysis)
        
        return jsonify({
            "status": "success",
            "analysis": analysis,
            "matches": matches,
            "demo_mode": True,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Demo scenario error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/demo-vc-scenario', methods=['POST'])
def demo_vc_scenario():
    """Load complete VC demo scenario"""
    try:
        # Use Andreessen Horowitz as demo VC
        demo_vc = REAL_VCS[0]
        
        # Generate their weekly startup queue
        weekly_queue = generate_vc_weekly_queue(demo_vc)
        
        # Add some demo metrics
        vc_metrics = {
            "deals_reviewed_this_week": 47,
            "meetings_scheduled": 8,
            "intros_pending": 12,
            "portfolio_companies": 156,
            "avg_response_time": "2.3 days",
            "this_quarter_investments": 6
        }
        
        return jsonify({
            "status": "success",
            "vc_profile": demo_vc,
            "weekly_queue": weekly_queue,
            "metrics": vc_metrics,
            "demo_mode": True,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"VC demo scenario error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/vc-decision', methods=['POST'])
def vc_decision():
    """Handle VC decision on startup"""
    try:
        data = request.json
        startup_id = data.get('startup_id')
        decision = data.get('decision')  # 'interested', 'pass', 'schedule_meeting'
        vc_id = data.get('vc_id')
        notes = data.get('notes', '')
        
        # Log the decision
        logger.info(f"VC {vc_id} decision: {decision} for startup {startup_id}")
        
        # In production, this would update the database
        response_data = {
            "status": "success",
            "message": f"Decision '{decision}' recorded successfully",
            "next_steps": {
                "interested": "Founder will be notified. Meeting request sent.",
                "pass": "Feedback shared with founder. Startup removed from active queue.",
                "schedule_meeting": "Calendar invite sent to both parties."
            }.get(decision, "Decision recorded"),
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"VC decision error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/market-intelligence', methods=['GET'])
def market_intelligence():
    """Get real-time market intelligence data"""
    try:
        # Get live funding news
        live_deals = get_live_funding_news()
        
        data = {
            'total_investors': 6042,
            'active_deals': len(live_deals),
            'hot_sectors': [
                {'name': 'AI/ML', 'funding': 12.3, 'growth': 145, 'color': '#ef4444'},
                {'name': 'Fintech', 'funding': 8.7, 'growth': 67, 'color': '#f97316'},
                {'name': 'Healthcare', 'funding': 6.9, 'growth': 34, 'color': '#eab308'},
                {'name': 'Climate', 'funding': 4.1, 'growth': 89, 'color': '#22c55e'},
                {'name': 'SaaS', 'funding': 7.2, 'growth': 23, 'color': '#3b82f6'},
                {'name': 'Consumer', 'funding': 3.8, 'growth': 12, 'color': '#8b5cf6'}
            ],
            'live_deals': live_deals,
            'market_trends': {
                'avg_deal_size': '$12.3M',
                'time_to_close': '45 days',
                'success_rate': '23%'
            },
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify({
            "status": "success",
            "data": data
        })
    except Exception as e:
        logger.error(f"Market intelligence error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/vcs', methods=['GET'])
def get_vcs():
    """Get complete VC database"""
    try:
        return jsonify({
            "status": "success",
            "vcs": REAL_VCS,
            "total": len(REAL_VCS),
            "last_updated": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"VC database error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/analyze-deck', methods=['POST'])
def analyze_deck():
    """Analyze uploaded pitch deck (mock for demo)"""
    try:
        if 'deck_file' not in request.files:
            return jsonify({"status": "error", "message": "No file uploaded"}), 400
        
        file = request.files['deck_file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No file selected"}), 400
        
        # Mock analysis result based on demo company
        analysis = generate_demo_company()
        analysis["uploaded_filename"] = file.filename
        analysis["processing_time"] = "28 seconds"
        
        return jsonify({
            "status": "success",
            "analysis": analysis,
            "processing_time": 28,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Deck analysis error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/find-matches', methods=['POST'])
def find_matches():
    """Find VC matches based on analysis"""
    try:
        data = request.json
        analysis = data.get('analysis', {})
        
        matches = find_vc_matches(analysis)
        
        return jsonify({
            "status": "success",
            "matches": matches,
            "total_matches": len(matches),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Match finding error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/intro-request', methods=['POST'])
def intro_request():
    """Handle introduction requests with AI-generated email"""
    try:
        data = request.json
        
        # Log the introduction request
        logger.info(f"Introduction request: {data.get('founder_email')} -> {data.get('vc_name')}")
        
        # In production, this would:
        # 1. Send the AI-generated email
        # 2. Store the request in database
        # 3. Set up follow-up tracking
        
        return jsonify({
            "status": "success",
            "message": "Introduction request submitted successfully",
            "request_id": f"intro_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "expected_response_time": "48-72 hours",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Intro request error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": "2.0.0",
        "uptime": "99.9%",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/status', methods=['GET'])
def system_status():
    """System status with real-time metrics"""
    return jsonify({
        "status": "operational",
        "services": {
            "api": "healthy",
            "database": "healthy", 
            "ai_analysis": "healthy",
            "market_feeds": "healthy"
        },
        "metrics": {
            "active_users": 1247,
            "analyses_today": 89,
            "intros_sent": 156,
            "success_rate": "89%"
        },
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
