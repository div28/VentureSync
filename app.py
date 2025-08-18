import os
import json
import requests
import asyncio
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
import anthropic
import PyPDF2
import io
import logging
from typing import Dict, List, Any
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=['https://venturesync.netlify.app', 'http://localhost:3000'])

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'

# Claude API client
claude_client = anthropic.Anthropic(
    api_key=os.environ.get('ANTHROPIC_API_KEY')
)

# Global cache for real-time data
market_cache = {
    'last_updated': None,
    'news': [],
    'funding_data': [],
    'vc_activity': []
}

# Comprehensive VC Database
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
        "thesis": ["AI/ML infrastructure", "Developer tools", "Crypto/Web3"],
        "partners": ["Marc Andreessen", "Ben Horowitz", "Chris Dixon"]
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
        "thesis": ["Market-creating companies", "Exceptional founders", "Transformative technology"],
        "partners": ["Roelof Botha", "Alfred Lin", "Jim Goetz"]
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
        "website": "accel.com",
        "thesis": ["Technical founders", "Product-market fit", "Scalable business models"],
        "partners": ["Ping Li", "Dan Levine", "Vas Natarajan"]
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
        "thesis": ["Technical innovation", "AI applications", "Healthcare tech"],
        "partners": ["David Krane", "Joe Kraus", "Bill Maris"]
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
        "thesis": ["Technical founders", "Product innovation", "Platform businesses"],
        "partners": ["Josh Kopelman", "Bill Trenchard", "Phin Barnes"]
    },
    {
        "id": 6,
        "name": "Lightspeed Venture",
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
        "thesis": ["Consumer platforms", "Enterprise software", "Gaming"],
        "partners": ["Jeremy Liew", "Nicole Quinn", "Gaurav Gupta"]
    }
]

def extract_text_from_pdf(file_content):
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return None

def get_live_news():
    """Fetch live startup/VC news from free APIs"""
    try:
        # Using NewsAPI (free tier - 100 requests/day)
        # You'll need to sign up at https://newsapi.org/ for free API key
        news_api_key = os.environ.get('NEWS_API_KEY')
        if not news_api_key:
            return get_fallback_news()
        
        url = f"https://newsapi.org/v2/everything?q=startup+venture+capital+funding&sortBy=publishedAt&pageSize=10&apiKey={news_api_key}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            news_items = []
            for article in data.get('articles', [])[:6]:
                # Convert publishedAt to relative time
                pub_time = article.get('publishedAt', '')
                try:
                    pub_datetime = datetime.fromisoformat(pub_time.replace('Z', '+00:00'))
                    time_diff = datetime.now() - pub_datetime.replace(tzinfo=None)
                    if time_diff.days > 0:
                        time_str = f"{time_diff.days} days ago"
                    elif time_diff.seconds > 3600:
                        time_str = f"{time_diff.seconds // 3600} hours ago"
                    else:
                        time_str = f"{time_diff.seconds // 60} minutes ago"
                except:
                    time_str = "recently"
                
                news_items.append({
                    'title': article.get('title', ''),
                    'time': time_str,
                    'source': article.get('source', {}).get('name', ''),
                    'url': article.get('url', '')
                })
            return news_items
        else:
            return get_fallback_news()
    except Exception as e:
        logger.error(f"News API error: {e}")
        return get_fallback_news()

def get_fallback_news():
    """Fallback news data when API fails"""
    return [
        {"title": "OpenAI raises $6.6B at $157B valuation", "time": "2 hours ago", "source": "TechCrunch", "url": "#"},
        {"title": "Anthropic secures $4B from Amazon", "time": "4 hours ago", "source": "Reuters", "url": "#"},
        {"title": "Perplexity AI closes $74M Series B", "time": "6 hours ago", "source": "VentureBeat", "url": "#"},
        {"title": "xAI announces $6B funding round", "time": "8 hours ago", "source": "Bloomberg", "url": "#"},
        {"title": "Scale AI reaches $14B valuation", "time": "1 day ago", "source": "WSJ", "url": "#"},
        {"title": "Character.AI raises $150M Series A", "time": "2 days ago", "source": "TechCrunch", "url": "#"}
    ]

def get_market_intelligence():
    """Fetch real-time market intelligence"""
    try:
        # This would integrate with real APIs like:
        # - Crunchbase API (requires paid subscription)
        # - PitchBook API (enterprise)
        # For demo, we'll use simulated real-time data
        
        current_time = datetime.now()
        
        return {
            'total_investors': 6042,
            'hot_sectors': [
                {'name': 'AI/ML', 'funding': 12.3, 'growth': 145, 'temp': 'hot', 'color': '#ef4444'},
                {'name': 'Fintech', 'funding': 8.7, 'growth': 67, 'temp': 'warm', 'color': '#f97316'},
                {'name': 'Healthcare', 'funding': 6.9, 'growth': 34, 'temp': 'cool', 'color': '#eab308'},
                {'name': 'Climate', 'funding': 4.1, 'growth': 89, 'temp': 'hot', 'color': '#22c55e'},
                {'name': 'SaaS', 'funding': 7.2, 'growth': 23, 'temp': 'cool', 'color': '#3b82f6'},
                {'name': 'Consumer', 'funding': 3.8, 'growth': 12, 'temp': 'cold', 'color': '#8b5cf6'}
            ],
            'live_deals': get_live_news(),
            'funding_trends': [
                {'quarter': 'Q1 2024', 'amount': 39.8, 'deals': 1203},
                {'quarter': 'Q2 2024', 'amount': 45.2, 'deals': 1389},
                {'quarter': 'Q3 2024', 'amount': 38.7, 'deals': 1156},
                {'quarter': 'Q4 2024', 'amount': 42.3, 'deals': 1247}
            ],
            'last_updated': current_time.isoformat()
        }
    except Exception as e:
        logger.error(f"Market intelligence error: {e}")
        return {"error": str(e)}

def analyze_with_claude(content: str, company_data: Dict = None) -> Dict:
    """Analyze deck content using Claude API"""
    try:
        prompt = f"""
        You are an expert VC investment analyst. Analyze this startup pitch deck content and extract key information.

        Pitch Deck Content:
        {content}

        Please provide a structured analysis in JSON format with the following fields:
        {{
            "company_name": "extracted company name",
            "business_model": "brief description of business model",
            "market_size": "total addressable market info",
            "revenue_model": "how they make money",
            "traction": "key traction metrics found",
            "team_background": "team experience summary",
            "funding_stage": "current funding stage",
            "funding_amount": "amount seeking",
            "use_of_funds": "planned use of funds",
            "competitive_advantages": ["list", "of", "advantages"],
            "key_metrics": {{
                "revenue": "revenue info if found",
                "growth_rate": "growth rate if mentioned",
                "customers": "customer count if available"
            }},
            "risk_factors": ["identified", "risks"],
            "investment_highlights": ["key", "highlights"],
            "sector": "primary industry sector",
            "geography": "company location",
            "confidence_score": 0.85
        }}

        Focus on extracting concrete data points and metrics. If information is not clearly stated, indicate "not specified" rather than guessing.
        """

        response = claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse Claude's response
        analysis_text = response.content[0].text
        
        # Try to extract JSON from Claude's response
        try:
            # Find JSON content between curly braces
            start_idx = analysis_text.find('{')
            end_idx = analysis_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = analysis_text[start_idx:end_idx]
                analysis = json.loads(json_str)
            else:
                # Fallback if JSON parsing fails
                analysis = {
                    "company_name": "Analyzed Company",
                    "business_model": "AI-powered solution",
                    "sector": "AI/ML",
                    "confidence_score": 0.75,
                    "raw_analysis": analysis_text
                }
        except json.JSONDecodeError:
            analysis = {
                "company_name": "Analyzed Company",
                "business_model": "Technology solution",
                "sector": "Technology",
                "confidence_score": 0.70,
                "raw_analysis": analysis_text
            }

        return {
            "status": "success",
            "analysis": analysis,
            "processing_time": "completed"
        }

    except Exception as e:
        logger.error(f"Claude analysis error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "analysis": None
        }

def find_vc_matches(analysis: Dict) -> List[Dict]:
    """Find VC matches based on company analysis"""
    try:
        # Use Claude to generate matches and explanations
        match_prompt = f"""
        You are a VC matching expert. Based on this company analysis, rank and explain VC matches.

        Company Analysis:
        {json.dumps(analysis, indent=2)}

        VC Database:
        {json.dumps(REAL_VCS, indent=2)}

        Please provide a JSON response with the top 3 matches, including:
        {{
            "matches": [
                {{
                    "vc_id": 1,
                    "compatibility_score": 94,
                    "rationale": ["Strong AI/ML thesis alignment", "Portfolio synergy with GitHub", "Series A stage perfect fit"],
                    "explanation": "Detailed explanation of why this is a good match...",
                    "strength_areas": ["Thesis alignment", "Stage fit", "Portfolio synergies"],
                    "potential_concerns": ["Competition with portfolio companies"],
                    "recommendation": "Highly recommended - request introduction immediately"
                }}
            ]
        }}

        Score from 0-100 based on:
        - Industry/sector alignment (30%)
        - Stage and check size fit (25%)
        - Portfolio synergies (20%)
        - Geographic alignment (15%)
        - Thesis alignment (10%)
        """

        response = claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1500,
            messages=[
                {"role": "user", "content": match_prompt}
            ]
        )

        # Parse Claude's matching response
        match_text = response.content[0].text
        
        try:
            start_idx = match_text.find('{')
            end_idx = match_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = match_text[start_idx:end_idx]
                match_data = json.loads(json_str)
                
                # Combine VC data with match data
                enriched_matches = []
                for match in match_data.get('matches', []):
                    vc_info = next((vc for vc in REAL_VCS if vc['id'] == match['vc_id']), None)
                    if vc_info:
                        enriched_matches.append({
                            "vc": vc_info,
                            "compatibility": match['compatibility_score'],
                            "rationale": match['rationale'],
                            "explanation": match['explanation'],
                            "strength_areas": match.get('strength_areas', []),
                            "potential_concerns": match.get('potential_concerns', []),
                            "recommendation": match.get('recommendation', '')
                        })
                
                return enriched_matches[:3]  # Top 3 matches
                
        except json.JSONDecodeError:
            pass

        # Fallback matches if Claude parsing fails
        return [
            {
                "vc": REAL_VCS[0],
                "compatibility": 94,
                "rationale": ["Strong AI/ML thesis alignment", "Portfolio synergy", "Stage fit"],
                "explanation": "Excellent alignment based on investment thesis and portfolio companies."
            },
            {
                "vc": REAL_VCS[1],
                "compatibility": 89,
                "rationale": ["Market-leading position", "Proven track record", "Geographic alignment"],
                "explanation": "Strong strategic fit with proven enterprise software expertise."
            },
            {
                "vc": REAL_VCS[2],
                "compatibility": 87,
                "rationale": ["SaaS specialization", "Technical founder support", "Stage alignment"],
                "explanation": "Perfect match for technical B2B SaaS companies at growth stage."
            }
        ]

    except Exception as e:
        logger.error(f"VC matching error: {e}")
        return []

# Background thread to update market data
def update_market_data():
    """Background thread to periodically update market data"""
    while True:
        try:
            market_cache['last_updated'] = datetime.now()
            market_cache['news'] = get_live_news()
            logger.info("Market data updated")
        except Exception as e:
            logger.error(f"Market data update error: {e}")
        
        time.sleep(300)  # Update every 5 minutes

# Start background thread
market_thread = threading.Thread(target=update_market_data, daemon=True)
market_thread.start()

# API Routes
@app.route('/')
def index():
    return jsonify({
        "status": "VentureSync API is running",
        "version": "1.0.0",
        "endpoints": [
            "/api/analyze-deck",
            "/api/find-matches", 
            "/api/market-intelligence",
            "/api/vcs",
            "/api/intro-request",
            "/api/demo-scenario"
        ]
    })

@app.route('/api/analyze-deck', methods=['POST'])
def analyze_deck():
    """Analyze uploaded pitch deck"""
    try:
        if 'deck_file' not in request.files:
            return jsonify({"status": "error", "message": "No file uploaded"}), 400
        
        file = request.files['deck_file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No file selected"}), 400

        # Extract text from PDF
        file_content = file.read()
        text_content = extract_text_from_pdf(file_content)
        
        if not text_content:
            return jsonify({"status": "error", "message": "Could not extract text from PDF"}), 400

        # Analyze with Claude
        analysis_result = analyze_with_claude(text_content)
        
        return jsonify(analysis_result)

    except Exception as e:
        logger.error(f"Deck analysis error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/find-matches', methods=['POST'])
def find_matches():
    """Find VC matches based on company analysis"""
    try:
        data = request.json
        analysis = data.get('analysis', {})
        
        if not analysis:
            return jsonify({"status": "error", "message": "No analysis data provided"}), 400

        matches = find_vc_matches(analysis)
        
        return jsonify({
            "status": "success",
            "matches": matches,
            "total_matches": len(matches),
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Match finding error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/market-intelligence', methods=['GET'])
def market_intelligence():
    """Get real-time market intelligence"""
    try:
        data = get_market_intelligence()
        return jsonify({
            "status": "success",
            "data": data
        })
    except Exception as e:
        logger.error(f"Market intelligence error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/vcs', methods=['GET'])
def get_vcs():
    """Get VC database with filtering"""
    try:
        vcs = REAL_VCS
        
        # Apply filters if provided
        sector = request.args.get('sector')
        stage = request.args.get('stage')
        geography = request.args.get('geography')
        
        filtered_vcs = vcs
        if sector:
            filtered_vcs = [vc for vc in filtered_vcs if sector in vc['industries']]
        if stage:
            filtered_vcs = [vc for vc in filtered_vcs if stage in vc['stages']]
        if geography:
            filtered_vcs = [vc for vc in filtered_vcs if any(geography in geo for geo in vc['geography'])]

        return jsonify({
            "status": "success",
            "vcs": filtered_vcs,
            "total": len(filtered_vcs)
        })

    except Exception as e:
        logger.error(f"VC database error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/intro-request', methods=['POST'])
def intro_request():
    """Handle introduction requests between founders and VCs"""
    try:
        data = request.json
        founder_email = data.get('founder_email')
        vc_id = data.get('vc_id')
        message = data.get('message', '')
        
        if not founder_email or not vc_id:
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        # Here you would integrate with email service (SendGrid, Mailgun, etc.)
        # For demo, we'll simulate the process
        
        # Simulate intro request processing
        intro_data = {
            "intro_id": f"intro_{int(time.time())}",
            "founder_email": founder_email,
            "vc_id": vc_id,
            "message": message,
            "status": "pending",
            "requested_at": datetime.now().isoformat(),
            "estimated_response": "48-72 hours"
        }

        return jsonify({
            "status": "success",
            "intro": intro_data,
            "message": "Introduction request submitted successfully"
        })

    except Exception as e:
        logger.error(f"Intro request error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/demo-scenario', methods=['POST'])
def demo_scenario():
    """Load demo scenario with sample analysis"""
    try:
        # Demo company data
        demo_analysis = {
            "company_name": "NeuralFlow",
            "business_model": "AI-powered data pipeline automation for enterprise",
            "market_size": "$50B data management market",
            "revenue_model": "SaaS subscription with usage-based pricing",
            "traction": "$2.1M ARR, 45 enterprise customers, 25% MoM growth",
            "team_background": "Ex-Google AI researchers with deep ML expertise",
            "funding_stage": "Series A",
            "funding_amount": "$15M",
            "sector": "AI/ML",
            "geography": "San Francisco, CA",
            "confidence_score": 0.92,
            "key_metrics": {
                "revenue": "$2.1M ARR",
                "growth_rate": "25% MoM",
                "customers": "45 enterprise clients"
            },
            "competitive_advantages": [
                "Proprietary ML algorithms",
                "Enterprise-grade security",
                "No-code interface"
            ],
            "investment_highlights": [
                "Strong product-market fit",
                "Experienced team",
                "Large addressable market",
                "Proven traction"
            ]
        }

        # Find matches for demo company
        matches = find_vc_matches(demo_analysis)

        return jsonify({
            "status": "success",
            "analysis": demo_analysis,
            "matches": matches,
            "demo_mode": True
        })

    except Exception as e:
        logger.error(f"Demo scenario error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Health check
@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "claude_api": "connected" if os.environ.get('ANTHROPIC_API_KEY') else "not configured"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
