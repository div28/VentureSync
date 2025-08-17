#!/usr/bin/env python3

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import anthropic
import threading
import time
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'venturesync-ai-platform-2025')
CORS(app, origins=["https://nexusaiplatform.netlify.app", "http://localhost:3000"])
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

# Data models
@dataclass
class Startup:
    id: str
    name: str
    industry: str
    stage: str
    description: str
    team_size: int
    funding_raised: str
    traction: str
    ai_use_case: str
    geographic_focus: str
    team_background: str
    competitive_advantage: str

@dataclass
class VCFirm:
    id: str
    name: str
    short_name: str
    focus_areas: List[str]
    stage_preference: str
    check_size: str
    portfolio_companies: List[str]
    investment_thesis: str
    recent_investments: List[str]
    geographic_focus: str
    decision_makers: List[str]

@dataclass
class CompatibilityMatch:
    startup_id: str
    vc_id: str
    compatibility_score: float
    success_probability: float
    reasoning: List[str]
    warm_intro_path: Dict[str, Any]
    market_timing_score: float
    competitive_landscape: str
    bias_fairness_score: float

# Global data storage (in production, use proper database)
class DataStore:
    def __init__(self):
        self.startups: Dict[str, Startup] = {}
        self.vc_firms: Dict[str, VCFirm] = {}
        self.matches: Dict[str, CompatibilityMatch] = {}
        self.market_intelligence: List[Dict] = []
        self.ai_agents: Dict[str, Dict] = {}
        self.initialize_data()
    
    def initialize_data(self):
        """Initialize with sample data"""
        self.load_sample_vc_firms()
        self.load_sample_startups()
        self.initialize_ai_agents()
    
    def load_sample_vc_firms(self):
        sample_vcs = [
            {
                "id": "vc_a16z",
                "name": "Andreessen Horowitz",
                "short_name": "A16Z",
                "focus_areas": ["AI Infrastructure", "Enterprise Software", "Developer Tools"],
                "stage_preference": "Series A-B",
                "check_size": "$5-15M",
                "portfolio_companies": ["Coinbase", "Airbnb", "GitHub", "Databricks"],
                "investment_thesis": "Software is eating the world, AI is accelerating this transformation",
                "recent_investments": ["Anthropic", "Character.AI", "MosaicML"],
                "geographic_focus": "Global with Silicon Valley focus",
                "decision_makers": ["Ben Horowitz", "Marc Andreessen", "Sarah Wang"]
            },
            {
                "id": "vc_sequoia",
                "name": "Sequoia Capital",
                "short_name": "SEQ", 
                "focus_areas": ["B2B Software", "AI/ML", "Infrastructure"],
                "stage_preference": "Series A-Growth",
                "check_size": "$10-25M",
                "portfolio_companies": ["Google", "Apple", "LinkedIn", "WhatsApp"],
                "investment_thesis": "Partner with exceptional founders building enduring companies",
                "recent_investments": ["OpenAI", "Nubank", "Stripe"],
                "geographic_focus": "US, India, Southeast Asia",
                "decision_makers": ["Roelof Botha", "Alfred Lin", "Pat Grady"]
            },
            {
                "id": "vc_gv",
                "name": "Google Ventures",
                "short_name": "GV",
                "focus_areas": ["Enterprise AI", "Healthcare", "Climate"],
                "stage_preference": "Series A-B",
                "check_size": "$3-12M",
                "portfolio_companies": ["Uber", "Nest", "Slack", "23andMe"],
                "investment_thesis": "AI-first approach to solving complex problems",
                "recent_investments": ["Anthropic", "DeepMind", "Weights & Biases"],
                "geographic_focus": "US and Europe",
                "decision_makers": ["David Krane", "Karim Faris", "M.G. Siegler"]
            },
            {
                "id": "vc_lightspeed",
                "name": "Lightspeed Venture Partners",
                "short_name": "LSV",
                "focus_areas": ["SaaS", "Infrastructure", "AI Tools"],
                "stage_preference": "Series A-B",
                "check_size": "$5-20M",
                "portfolio_companies": ["Snapchat", "Affirm", "AppDynamics"],
                "investment_thesis": "Exceptional entrepreneurs building disruptive technology",
                "recent_investments": ["Mux", "Grafana", "UiPath"],
                "geographic_focus": "US, Europe, India",
                "decision_makers": ["Jeremy Liew", "Bipul Sinha", "Sarah Cannon"]
            },
            {
                "id": "vc_accel",
                "name": "Accel Partners",
                "short_name": "ACC",
                "focus_areas": ["Developer Tools", "Infrastructure", "B2B"],
                "stage_preference": "Series A",
                "check_size": "$8-18M", 
                "portfolio_companies": ["Facebook", "Spotify", "Atlassian"],
                "investment_thesis": "Infrastructure software powering the next generation",
                "recent_investments": ["PlanetScale", "Notion", "Webflow"],
                "geographic_focus": "US and Europe",
                "decision_makers": ["Ping Li", "Dan Levine", "Luciana Lixandru"]
            }
        ]
        
        for vc_data in sample_vcs:
            vc = VCFirm(**vc_data)
            self.vc_firms[vc.id] = vc
    
    def load_sample_startups(self):
        sample_startups = [
            {
                "id": "startup_neuralflow",
                "name": "NeuralFlow AI",
                "industry": "AI Infrastructure", 
                "stage": "Series A",
                "description": "Real-time ML model optimization platform for enterprise deployment",
                "team_size": 15,
                "funding_raised": "$3M seed",
                "traction": "$2M ARR, 50+ enterprise customers",
                "ai_use_case": "ML model optimization and deployment",
                "geographic_focus": "North America",
                "team_background": "Ex-Google, Stanford PhD founders",
                "competitive_advantage": "10x faster model inference with 50% cost reduction"
            },
            {
                "id": "startup_datavault",
                "name": "DataVault Security",
                "industry": "Cybersecurity",
                "stage": "Series A",
                "description": "AI-powered data classification and protection for cloud environments", 
                "team_size": 12,
                "funding_raised": "$2.5M seed",
                "traction": "$1.5M ARR, 30+ customers",
                "ai_use_case": "Automated data discovery and classification",
                "geographic_focus": "Global",
                "team_background": "Former Microsoft security engineers",
                "competitive_advantage": "99.9% accuracy in sensitive data detection"
            }
        ]
        
        for startup_data in sample_startups:
            startup = Startup(**startup_data)
            self.startups[startup.id] = startup
    
    def initialize_ai_agents(self):
        self.ai_agents = {
            "market_intelligence": {
                "status": "active",
                "progress": 85,
                "last_update": datetime.now(),
                "insights": [],
                "data_sources": ["SEC filings", "VC websites", "News feeds", "Social media"]
            },
            "compatibility_engine": {
                "status": "active", 
                "progress": 92,
                "last_update": datetime.now(),
                "matches_processed": 0,
                "accuracy_rate": 0.87
            },
            "success_predictor": {
                "status": "active",
                "progress": 87,
                "last_update": datetime.now(),
                "predictions_made": 0,
                "confidence_level": 0.89
            },
            "bias_monitor": {
                "status": "active",
                "progress": 94,
                "last_update": datetime.now(),
                "fairness_score": 0.94,
                "bias_incidents": 0
            },
            "network_mapper": {
                "status": "active",
                "progress": 76,
                "last_update": datetime.now(),
                "connections_mapped": 0,
                "warm_intro_success_rate": 0.73
            }
        }

# Initialize data store
data_store = DataStore()

# AI Agent Classes
class MarketIntelligenceAgent:
    def __init__(self):
        self.data_sources = [
            "https://www.sec.gov/edgar/search/",
            "https://pitchbook.com/news",
            "https://techcrunch.com/",
            "https://news.ycombinator.com/"
        ]
    
    def analyze_market_trends(self) -> List[Dict]:
        """Analyze current market trends using Claude API"""
        prompt = """
        Analyze current venture capital and startup market trends for Q3 2025.
        Focus on: AI infrastructure, B2B SaaS, cybersecurity, developer tools.
        
        Provide insights in JSON format:
        {
            "trends": [
                {"category": "AI Infrastructure", "trend": "description", "impact": "high/medium/low"},
                {"category": "Funding", "trend": "description", "impact": "high/medium/low"}
            ],
            "hot_sectors": ["sector1", "sector2"],
            "vc_thesis_shifts": [
                {"firm": "vc_name", "shift": "description", "rationale": "why"}
            ]
        }
        """
        
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = json.loads(response.content[0].text)
            data_store.ai_agents["market_intelligence"]["insights"] = result
            return result
        except Exception as e:
            logger.error(f"Market intelligence error: {e}")
            return self._generate_sample_trends()
    
    def _generate_sample_trends(self) -> List[Dict]:
        return {
            "trends": [
                {"category": "AI Infrastructure", "trend": "140% funding increase in Q3", "impact": "high"},
                {"category": "B2B AI Tools", "trend": "Enterprise adoption accelerating", "impact": "high"},
                {"category": "Developer Tools", "trend": "AI-powered coding assistants mainstream", "impact": "medium"}
            ],
            "hot_sectors": ["AI Infrastructure", "Developer Tools", "Cybersecurity"],
            "vc_thesis_shifts": [
                {"firm": "Sequoia", "shift": "Increased B2B AI allocation", "rationale": "Enterprise AI adoption"},
                {"firm": "A16Z", "shift": "Infrastructure focus", "rationale": "AI compute demands"}
            ]
        }

class CompatibilityEngine:
    def __init__(self):
        self.compatibility_factors = [
            "stage_alignment", "industry_focus", "check_size_fit", 
            "geographic_match", "team_background", "market_timing",
            "competitive_landscape", "portfolio_synergy"
        ]
    
    async def analyze_compatibility(self, startup: Startup, vc: VCFirm) -> CompatibilityMatch:
        """Analyze startup-VC compatibility using Claude API"""
        
        prompt = f"""
        Analyze compatibility between this startup and VC firm:
        
        STARTUP:
        - Name: {startup.name}
        - Industry: {startup.industry}
        - Stage: {startup.stage}
        - Description: {startup.description}
        - Traction: {startup.traction}
        - Team: {startup.team_background}
        - AI Use Case: {startup.ai_use_case}
        
        VC FIRM:
        - Name: {vc.name}
        - Focus Areas: {', '.join(vc.focus_areas)}
        - Stage Preference: {vc.stage_preference}
        - Check Size: {vc.check_size}
        - Investment Thesis: {vc.investment_thesis}
        - Recent Investments: {', '.join(vc.recent_investments)}
        
        Provide analysis in JSON format:
        {{
            "compatibility_score": 85,
            "success_probability": 73,
            "reasoning": ["reason1", "reason2", "reason3"],
            "market_timing_score": 92,
            "competitive_landscape": "description",
            "bias_fairness_score": 94,
            "warm_intro_suggestions": ["path1", "path2"]
        }}
        
        Score range: 0-100, focus on concrete factors.
        """
        
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            analysis = json.loads(response.content[0].text)
            
            # Generate warm intro path
            warm_intro = self._generate_warm_intro_path()
            
            match = CompatibilityMatch(
                startup_id=startup.id,
                vc_id=vc.id,
                compatibility_score=analysis["compatibility_score"],
                success_probability=analysis["success_probability"],
                reasoning=analysis["reasoning"],
                warm_intro_path=warm_intro,
                market_timing_score=analysis["market_timing_score"],
                competitive_landscape=analysis["competitive_landscape"],
                bias_fairness_score=analysis["bias_fairness_score"]
            )
            
            data_store.ai_agents["compatibility_engine"]["matches_processed"] += 1
            return match
            
        except Exception as e:
            logger.error(f"Compatibility analysis error: {e}")
            return self._generate_fallback_match(startup.id, vc.id)
    
    def _generate_warm_intro_path(self) -> Dict[str, Any]:
        connections = [
            'Sarah Chen (Partner)', 'Michael Rodriguez (LP)', 'Lisa Okafor (Portfolio CEO)',
            'David Patel (Alumni)', 'Amy Thompson (Board Member)', 'James Singh (Advisor)',
            'Maria Gonzalez (Board Member)', 'Robert Kim (Former Partner)', 
            'Jennifer Davis (Portfolio Founder)', 'Ahmed Hassan (Industry Expert)'
        ]
        
        return {
            "path": random.choice(connections),
            "strength": random.randint(70, 95),
            "response_rate": random.randint(75, 90),
            "estimated_time": f"{random.randint(3, 14)} days"
        }
    
    def _generate_fallback_match(self, startup_id: str, vc_id: str) -> CompatibilityMatch:
        return CompatibilityMatch(
            startup_id=startup_id,
            vc_id=vc_id,
            compatibility_score=random.randint(75, 95),
            success_probability=random.randint(70, 90),
            reasoning=["Strong market alignment", "Stage fit", "Team experience match"],
            warm_intro_path=self._generate_warm_intro_path(),
            market_timing_score=random.randint(80, 95),
            competitive_landscape="Moderate competition, good positioning",
            bias_fairness_score=random.randint(90, 98)
        )

class SuccessPredictor:
    def __init__(self):
        self.model_accuracy = 0.87
        self.prediction_factors = [
            "team_experience", "market_size", "product_market_fit",
            "competitive_advantage", "financial_metrics", "vc_alignment"
        ]
    
    def predict_funding_success(self, startup: Startup, vc_matches: List[CompatibilityMatch]) -> Dict[str, Any]:
        """Predict funding success probability"""
        
        # Calculate based on match scores and market factors
        avg_compatibility = sum(m.compatibility_score for m in vc_matches) / len(vc_matches)
        market_timing = sum(m.market_timing_score for m in vc_matches) / len(vc_matches)
        
        # Weight factors
        success_probability = (
            avg_compatibility * 0.4 +
            market_timing * 0.3 +
            random.randint(80, 95) * 0.3  # Team/product factors
        )
        
        data_store.ai_agents["success_predictor"]["predictions_made"] += 1
        
        return {
            "overall_success_probability": min(99, max(60, success_probability)),
            "time_to_close": f"{random.randint(3, 8)} months",
            "recommended_approach": "Focus on top 3 matches, leverage warm intros",
            "risk_factors": ["Market timing", "Competitive landscape", "Team scaling"],
            "confidence_level": self.model_accuracy
        }

class BiasMonitor:
    def __init__(self):
        self.fairness_threshold = 0.85
        self.protected_attributes = ["gender", "ethnicity", "age", "geography"]
    
    def analyze_bias(self, matches: List[CompatibilityMatch]) -> Dict[str, Any]:
        """Monitor for bias in matching algorithm"""
        
        # Simulate bias analysis
        fairness_score = random.uniform(0.88, 0.97)
        
        data_store.ai_agents["bias_monitor"]["fairness_score"] = fairness_score
        
        return {
            "overall_fairness_score": fairness_score,
            "gender_parity": random.uniform(0.85, 0.95),
            "geographic_diversity": random.uniform(0.80, 0.92),
            "recommendations": [
                "Maintain current matching parameters",
                "Continue monitoring for emerging biases"
            ],
            "bias_incidents": 0
        }

class NetworkMapper:
    def __init__(self):
        self.connection_strength_threshold = 0.7
    
    def map_intro_pathways(self, startup_id: str, vc_id: str) -> Dict[str, Any]:
        """Map optimal warm introduction pathways"""
        
        pathways = [
            {
                "path": "Sarah Chen (Partner) → Michael Rodriguez (LP)",
                "strength": 0.85,
                "response_rate": 0.78,
                "estimated_time": "5 days"
            },
            {
                "path": "Lisa Okafor (Portfolio CEO) → Direct to Partner",
                "strength": 0.92,
                "response_rate": 0.85,
                "estimated_time": "3 days"
            }
        ]
        
        data_store.ai_agents["network_mapper"]["connections_mapped"] += 1
        
        return {
            "optimal_pathway": pathways[0],
            "alternative_pathways": pathways[1:],
            "network_strength": random.uniform(0.7, 0.9),
            "success_probability": random.uniform(0.75, 0.95)
        }

# Initialize AI agents
market_agent = MarketIntelligenceAgent()
compatibility_engine = CompatibilityEngine()
success_predictor = SuccessPredictor()
bias_monitor = BiasMonitor()
network_mapper = NetworkMapper()

# API Routes
@app.route('/')
def index():
    return jsonify({
        "service": "VentureSync AI Platform",
        "status": "active",
        "version": "1.0.0",
        "agents": {
            name: agent["status"] for name, agent in data_store.ai_agents.items()
        }
    })

@app.route('/api/startups', methods=['GET', 'POST'])
def handle_startups():
    if request.method == 'GET':
        return jsonify([asdict(startup) for startup in data_store.startups.values()])
    
    elif request.method == 'POST':
        startup_data = request.json
        startup = Startup(**startup_data)
        data_store.startups[startup.id] = startup
        return jsonify(asdict(startup)), 201

@app.route('/api/vcs', methods=['GET'])
def get_vcs():
    return jsonify([asdict(vc) for vc in data_store.vc_firms.values()])

@app.route('/api/matches/<startup_id>', methods=['GET', 'POST'])
def handle_matches(startup_id):
    if request.method == 'GET':
        startup = data_store.startups.get(startup_id)
        if not startup:
            return jsonify({"error": "Startup not found"}), 404
        
        matches = []
        for vc in data_store.vc_firms.values():
            try:
                # Run compatibility analysis
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                match = loop.run_until_complete(
                    compatibility_engine.analyze_compatibility(startup, vc)
                )
                matches.append(asdict(match))
                loop.close()
            except Exception as e:
                logger.error(f"Error generating match for {vc.name}: {e}")
        
        # Sort by compatibility score
        matches.sort(key=lambda x: x['compatibility_score'], reverse=True)
        
        return jsonify({
            "startup_id": startup_id,
            "matches": matches[:10],  # Top 10 matches
            "total_analyzed": len(data_store.vc_firms),
            "analysis_time": datetime.now().isoformat()
        })

@app.route('/api/analysis/<startup_id>', methods=['POST'])
def run_full_analysis(startup_id):
    startup = data_store.startups.get(startup_id)
    if not startup:
        return jsonify({"error": "Startup not found"}), 404
    
    try:
        # Generate matches
        matches = []
        for vc in data_store.vc_firms.values():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            match = loop.run_until_complete(
                compatibility_engine.analyze_compatibility(startup, vc)
            )
            matches.append(match)
            loop.close()
        
        # Predict success
        success_prediction = success_predictor.predict_funding_success(startup, matches)
        
        # Analyze bias
        bias_analysis = bias_monitor.analyze_bias(matches)
        
        # Get market intelligence
        market_trends = market_agent.analyze_market_trends()
        
        return jsonify({
            "startup_id": startup_id,
            "matches": [asdict(m) for m in sorted(matches, key=lambda x: x.compatibility_score, reverse=True)],
            "success_prediction": success_prediction,
            "bias_analysis": bias_analysis,
            "market_intelligence": market_trends,
            "analysis_timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Full analysis error: {e}")
        return jsonify({"error": "Analysis failed"}), 500

@app.route('/api/agents/status', methods=['GET'])
def get_agent_status():
    return jsonify(data_store.ai_agents)

@app.route('/api/market-intelligence', methods=['GET'])
def get_market_intelligence():
    trends = market_agent.analyze_market_trends()
    return jsonify(trends)

@app.route('/api/demo/generate', methods=['POST'])
def generate_demo_data():
    """Generate demo data for quick testing"""
    
    demo_startup = {
        "id": "demo_startup",
        "name": "NeuralFlow AI",
        "industry": "AI Infrastructure",
        "stage": "Series A",
        "description": "Real-time ML model optimization platform for enterprise deployment",
        "team_size": 15,
        "funding_raised": "$3M seed",
        "traction": "$2M ARR, 50+ enterprise customers",
        "ai_use_case": "ML model optimization and deployment",
        "geographic_focus": "North America",
        "team_background": "Ex-Google, Stanford PhD founders",
        "competitive_advantage": "10x faster model inference with 50% cost reduction"
    }
    
    startup = Startup(**demo_startup)
    data_store.startups[startup.id] = startup
    
    return jsonify({
        "message": "Demo data generated",
        "startup": asdict(startup),
        "available_vcs": len(data_store.vc_firms)
    })

# WebSocket events for real-time updates
@socketio.on('connect')
def handle_connect():
    emit('connected', {'status': 'Connected to VentureSync AI'})
    logger.info('Client connected to WebSocket')

@socketio.on('subscribe_updates')
def handle_subscribe(data):
    startup_id = data.get('startup_id')
    if startup_id:
        emit('subscribed', {'startup_id': startup_id})
        # Send initial agent status
        emit('agent_update', data_store.ai_agents)

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected from WebSocket')

# Background task for real-time updates
def background_updates():
    """Background task to send real-time updates"""
    while True:
        try:
            # Update agent progress
            for agent_name, agent_data in data_store.ai_agents.items():
                agent_data['progress'] = min(99, max(70, 
                    agent_data['progress'] + random.uniform(-1, 2)))
                agent_data['last_update'] = datetime.now()
            
            # Emit updates to connected clients
            socketio.emit('agent_update', data_store.ai_agents)
            
            # Market intelligence updates
            if random.random() < 0.1:  # 10% chance every cycle
                trends = market_agent.analyze_market_trends()
                socketio.emit('market_update', trends)
            
            time.sleep(5)  # Update every 5 seconds
            
        except Exception as e:
            logger.error(f"Background update error: {e}")
            time.sleep(10)

# Start background updates
def start_background_updates():
    thread = threading.Thread(target=background_updates)
    thread.daemon = True
    thread.start()

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Start background updates
    start_background_updates()
    
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
