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

# Real VC Database (20 VCs)
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
        "website": "a16z.com"
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
        "website": "sequoiacap.com"
    },
    {
        "id": 3,
        "name": "Accel",
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
        "website": "accel.com"
    }
]

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
    """Generate a realistic demo company"""
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
            "deck_summary": "AI-powered data automation platform serving enterprise clients with strong growth metrics and experienced team.",
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
            "deck_summary": "Cross-border payment solution for SMBs with blockchain technology and strong customer traction.",
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
            "deck_summary": "AI-powered radiology platform with FDA clearance and proven clinical outcomes across hospital systems.",
            "confidence_score": 0.94
        }
    ]
    
    return random.choice(companies)

def find_vc_matches(analysis):
    """Generate VC matches for demo company"""
    matches = [
        {
            "vc": REAL_VCS[0],  # a16z
            "compatibility": 94,
            "rationale": ["Strong AI/ML thesis alignment", "Portfolio synergy with GitHub", "Series A stage perfect fit"],
            "explanation": "Excellent alignment with Andreessen Horowitz's AI/ML investment thesis and portfolio companies like GitHub and Meta."
        },
        {
            "vc": REAL_VCS[1],  # Sequoia
            "compatibility": 89,
            "rationale": ["Market-leading position", "Proven track record", "Geographic alignment"],
            "explanation": "Strong strategic fit with Sequoia's enterprise software expertise and track record with companies like Google and Zoom."
        },
        {
            "vc": REAL_VCS[2],  # Accel
            "compatibility": 87,
            "rationale": ["SaaS specialization", "Technical founder support", "Stage alignment"],
            "explanation": "Perfect match for technical B2B SaaS companies with Accel's portfolio including Slack and Dropbox."
        }
    ]
    return matches

# API Routes
@app.route('/')
def index():
    return jsonify({
        "status": "VentureSync API is running",
        "version": "1.0.0",
        "endpoints": ["/api/demo-scenario", "/api/market-intelligence", "/api/vcs"]
    })

@app.route('/api/demo-scenario', methods=['POST'])
def demo_scenario():
    """Load complete demo scenario"""
    try:
        # Generate demo company
        analysis = generate_demo_company()
        
        # Find matches
        matches = find_vc_matches(analysis)
        
        return jsonify({
            "status": "success",
            "analysis": analysis,
            "matches": matches,
            "demo_mode": True
        })
        
    except Exception as e:
        logger.error(f"Demo scenario error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/market-intelligence', methods=['GET'])
def market_intelligence():
    """Get market intelligence data"""
    try:
        data = {
            'total_investors': 6042,
            'hot_sectors': [
                {'name': 'AI/ML', 'funding': 12.3, 'growth': 145, 'color': '#ef4444'},
                {'name': 'Fintech', 'funding': 8.7, 'growth': 67, 'color': '#f97316'},
                {'name': 'Healthcare', 'funding': 6.9, 'growth': 34, 'color': '#eab308'},
                {'name': 'Climate', 'funding': 4.1, 'growth': 89, 'color': '#22c55e'},
                {'name': 'SaaS', 'funding': 7.2, 'growth': 23, 'color': '#3b82f6'},
                {'name': 'Consumer', 'funding': 3.8, 'growth': 12, 'color': '#8b5cf6'}
            ],
            'live_deals': get_fallback_news(),
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
    """Get VC database"""
    try:
        return jsonify({
            "status": "success",
            "vcs": REAL_VCS,
            "total": len(REAL_VCS)
        })
    except Exception as e:
        logger.error(f"VC database error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/intro-request', methods=['POST'])
def intro_request():
    """Handle introduction requests"""
    try:
        data = request.json
        return jsonify({
            "status": "success",
            "message": "Introduction request submitted successfully"
        })
    except Exception as e:
        logger.error(f"Intro request error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
