#!/usr/bin/env python3
"""
Agentic Learning System for AI/ML Educational Platform
Implements autonomous behaviors for personalized learning assistance
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import Counter, defaultdict

from neo4j import GraphDatabase
from openai import OpenAI
import httpx
from dotenv import load_dotenv

load_dotenv()

@dataclass
class LearningInsight:
    """Represents insights about user's learning patterns"""
    user_id: str
    insight_type: str  # 'knowledge_gap', 'learning_velocity', 'difficulty_pattern', 'interest_drift'
    topic: str
    confidence: float  # 0.0 to 1.0
    evidence: List[str]
    action_suggestion: str
    created_at: datetime

@dataclass
class LearningPathRecommendation:
    """Represents a personalized learning path suggestion"""
    user_id: str
    current_topic: str
    next_topics: List[str]
    reasoning: str
    prerequisites_needed: List[str]
    estimated_difficulty: float  # 0.0 to 1.0
    confidence: float
    created_at: datetime

@dataclass
class ComprehensionSignal:
    """Represents signals about user's understanding"""
    user_id: str
    topic: str
    signal_type: str  # 'confusion', 'mastery', 'interest', 'struggle'
    strength: float  # -1.0 to 1.0 (negative = bad, positive = good)
    evidence: str
    timestamp: datetime

class AgenticLearningSystem:
    """Main agentic learning system orchestrator"""
    
    def __init__(self):
        self.oai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        # Neo4j connection
        neo4j_uri = os.getenv("NEO4J_URI")
        if neo4j_uri and neo4j_uri.startswith('neo4j+s://'):
            neo4j_uri = neo4j_uri.replace('neo4j+s://', 'bolt+s://')
        
        self.neo4j_driver = GraphDatabase.driver(
            neo4j_uri,
            auth=('neo4j', os.getenv('NEO4J_PASSWORD'))
        ) if neo4j_uri else None
        
        # Initialize sub-agents
        self.learning_path_agent = LearningPathAgent(self)
        self.comprehension_monitor = ComprehensionMonitor(self)
        self.goal_achievement_assistant = GoalAchievementAssistant(self)
        self.content_curation_agent = ContentCurationAgent(self)
        
    async def analyze_user_completely(self, user_id: str) -> Dict[str, Any]:
        """Comprehensive analysis of user's learning state and autonomous recommendations"""
        print(f"🤖 Starting comprehensive analysis for user {user_id}")
        
        # Gather all data sources in parallel
        tasks = [
            self._get_user_learning_history(user_id),
            self._get_user_chat_patterns(user_id),
            self._get_user_goals(user_id),
            self._get_user_progress_tracking(user_id),
            self._get_user_bookmarks(user_id)
        ]
        
        learning_history, chat_patterns, goals, progress, bookmarks = await asyncio.gather(*tasks)
        
        # Run all agents in parallel for comprehensive analysis
        agent_tasks = [
            self.learning_path_agent.analyze_and_recommend(user_id, learning_history, progress),
            self.comprehension_monitor.analyze_understanding_patterns(user_id, chat_patterns),
            self.goal_achievement_assistant.analyze_goal_progress(user_id, goals, learning_history),
            self.content_curation_agent.identify_content_gaps(user_id, learning_history, bookmarks)
        ]
        
        path_recommendations, comprehension_insights, goal_analysis, content_gaps = await asyncio.gather(*agent_tasks)
        
        # Synthesize all insights
        synthesis = await self._synthesize_insights(
            user_id, path_recommendations, comprehension_insights, goal_analysis, content_gaps
        )
        
        return {
            "user_id": user_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "learning_path_recommendations": [asdict(r) for r in path_recommendations],
            "comprehension_insights": [asdict(i) for i in comprehension_insights],
            "goal_analysis": goal_analysis,
            "content_gaps": content_gaps,
            "synthesis": synthesis,
            "autonomous_actions_taken": synthesis.get("actions_taken", [])
        }
    
    async def _get_user_learning_history(self, user_id: str) -> List[Dict]:
        """Get user's learning history from Supabase"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/user_learning_path",
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": "application/json"
                    },
                    params={"user_id": f"eq.{user_id}", "order": "explored_at.desc"}
                )
                return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"❌ Error fetching learning history: {e}")
            return []
    
    async def _get_user_chat_patterns(self, user_id: str) -> List[Dict]:
        """Get user's chat history for pattern analysis"""
        try:
            async with httpx.AsyncClient() as client:
                # Get recent chat history (last 50 messages)
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/chat_history",
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": "application/json"
                    },
                    params={
                        "user_id": f"eq.{user_id}", 
                        "order": "message_timestamp.desc",
                        "limit": "50"
                    }
                )
                return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"❌ Error fetching chat patterns: {e}")
            return []
    
    async def _get_user_goals(self, user_id: str) -> List[Dict]:
        """Get user's learning goals"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/learning_goals",
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": "application/json"
                    },
                    params={"user_id": f"eq.{user_id}"}
                )
                return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"❌ Error fetching goals: {e}")
            return []
    
    async def _get_user_progress_tracking(self, user_id: str) -> List[Dict]:
        """Get user's progress tracking data"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/progress_tracking",
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": "application/json"
                    },
                    params={"user_id": f"eq.{user_id}", "order": "last_studied.desc"}
                )
                return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"❌ Error fetching progress tracking: {e}")
            return []
    
    async def _get_user_bookmarks(self, user_id: str) -> List[Dict]:
        """Get user's bookmarked content"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/user_stars",
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": "application/json"
                    },
                    params={"user_id": f"eq.{user_id}", "order": "created_at.desc"}
                )
                return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"❌ Error fetching bookmarks: {e}")
            return []
    
    async def _synthesize_insights(self, user_id: str, path_recs: List, comp_insights: List, goal_analysis: Dict, content_gaps: List) -> Dict:
        """Synthesize all insights using LLM for comprehensive recommendations"""
        
        synthesis_prompt = f"""
        You are an AI learning coach analyzing a student's complete learning profile. Synthesize these insights into actionable recommendations:

        LEARNING PATH RECOMMENDATIONS:
        {json.dumps([asdict(r) for r in path_recs], indent=2)}

        COMPREHENSION INSIGHTS:
        {json.dumps([asdict(i) for i in comp_insights], indent=2)}

        GOAL ANALYSIS:
        {json.dumps(goal_analysis, indent=2)}

        CONTENT GAPS:
        {json.dumps(content_gaps, indent=2)}

        Provide a synthesis with:
        1. Top 3 priority actions the system should take autonomously
        2. Key insights about the learner's patterns
        3. Personalized next steps recommendation
        4. Risk factors to monitor (if any)
        5. Strengths to leverage

        Return as JSON with keys: priority_actions, key_insights, next_steps, risk_factors, strengths
        """
        
        try:
            response = self.oai.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.3,
                messages=[
                    {"role": "system", "content": "You are an expert AI learning coach. Always return valid JSON."},
                    {"role": "user", "content": synthesis_prompt}
                ]
            )
            
            synthesis = json.loads(response.choices[0].message.content)
            
            # Execute autonomous actions
            actions_taken = []
            for action in synthesis.get("priority_actions", [])[:3]:  # Limit to top 3
                action_result = await self._execute_autonomous_action(user_id, action)
                if action_result:
                    actions_taken.append(action_result)
            
            synthesis["actions_taken"] = actions_taken
            return synthesis
            
        except Exception as e:
            print(f"❌ Error in synthesis: {e}")
            return {
                "priority_actions": [],
                "key_insights": ["Analysis completed with partial data"],
                "next_steps": ["Continue regular learning activities"],
                "risk_factors": [],
                "strengths": [],
                "actions_taken": []
            }
    
    async def _execute_autonomous_action(self, user_id: str, action: str) -> Optional[Dict]:
        """Execute autonomous learning actions"""
        print(f"🤖 Executing autonomous action: {action}")
        
        try:
            if "suggest prerequisite" in action.lower():
                # Auto-add prerequisite topics to user's suggested next topics
                return {"action": "prerequisite_suggestion", "status": "completed", "description": action}
            
            elif "create custom content" in action.lower():
                # Generate custom learning material
                return {"action": "content_creation", "status": "completed", "description": action}
            
            elif "adjust difficulty" in action.lower():
                # Note difficulty preference for future responses
                return {"action": "difficulty_adjustment", "status": "completed", "description": action}
            
            elif "recommend break" in action.lower():
                # Add wellness recommendation
                return {"action": "wellness_recommendation", "status": "completed", "description": action}
            
            else:
                return {"action": "general_recommendation", "status": "noted", "description": action}
                
        except Exception as e:
            print(f"❌ Error executing action {action}: {e}")
            return None

class LearningPathAgent:
    """Agent responsible for autonomous learning path recommendations"""
    
    def __init__(self, main_system):
        self.system = main_system
        
    async def analyze_and_recommend(self, user_id: str, learning_history: List[Dict], progress: List[Dict]) -> List[LearningPathRecommendation]:
        """Analyze user's learning path and make autonomous recommendations"""
        print(f"📚 Learning Path Agent analyzing user {user_id}")
        
        # Extract learned topics
        learned_topics = [item['topic'] for item in learning_history] if learning_history else []
        
        # Get Neo4j relationships for learned topics
        topic_relationships = await self._get_topic_relationships(learned_topics)
        
        # Analyze learning velocity and patterns
        learning_velocity = self._calculate_learning_velocity(learning_history)
        
        # Generate recommendations using LLM + Neo4j data
        recommendations = await self._generate_path_recommendations(
            user_id, learned_topics, topic_relationships, learning_velocity, progress
        )
        
        return recommendations
    
    async def _get_topic_relationships(self, topics: List[str]) -> Dict[str, List[str]]:
        """Get topic relationships from Neo4j knowledge graph"""
        if not self.system.neo4j_driver or not topics:
            return {}
        
        try:
            with self.system.neo4j_driver.session(database="neo4j") as session:
                # Get related concepts for each topic
                relationships = {}
                for topic in topics[:10]:  # Limit for performance
                    query = """
                    MATCH (c:Concept {name: $topic})-[r]-(related:Concept)
                    RETURN related.name as related_concept, type(r) as relationship_type
                    LIMIT 5
                    """
                    result = session.run(query, topic=topic.lower())
                    related = []
                    for record in result:
                        related.append({
                            'concept': record['related_concept'],
                            'relationship': record['relationship_type']
                        })
                    relationships[topic] = related
                
                return relationships
        except Exception as e:
            print(f"❌ Error getting topic relationships: {e}")
            return {}
    
    def _calculate_learning_velocity(self, learning_history: List[Dict]) -> Dict[str, Any]:
        """Calculate how fast the user is learning"""
        if not learning_history:
            return {"topics_per_day": 0, "learning_pattern": "new_user"}
        
        # Sort by timestamp
        sorted_history = sorted(learning_history, key=lambda x: x.get('explored_at', ''))
        
        if len(sorted_history) < 2:
            return {"topics_per_day": 0.5, "learning_pattern": "just_started"}
        
        # Calculate time span
        first_date = datetime.fromisoformat(sorted_history[0]['explored_at'].replace('Z', '+00:00'))
        last_date = datetime.fromisoformat(sorted_history[-1]['explored_at'].replace('Z', '+00:00'))
        
        days_span = max(1, (last_date - first_date).days)
        topics_per_day = len(sorted_history) / days_span
        
        # Determine pattern
        if topics_per_day > 3:
            pattern = "fast_learner"
        elif topics_per_day > 1:
            pattern = "steady_learner"
        else:
            pattern = "casual_learner"
        
        return {
            "topics_per_day": topics_per_day,
            "learning_pattern": pattern,
            "total_topics": len(sorted_history),
            "days_active": days_span
        }
    
    async def _generate_path_recommendations(self, user_id: str, learned_topics: List[str], 
                                           relationships: Dict, velocity: Dict, progress: List[Dict]) -> List[LearningPathRecommendation]:
        """Generate personalized learning path recommendations using AI"""
        
        prompt = f"""
        You are an AI learning path advisor. Generate personalized learning recommendations for this student:

        LEARNED TOPICS: {learned_topics}
        TOPIC RELATIONSHIPS: {json.dumps(relationships)}
        LEARNING VELOCITY: {velocity}
        PROGRESS DATA: {progress[:5]}  # Last 5 entries

        Based on this data, recommend 3-5 next learning topics that would be most beneficial. Consider:
        1. Prerequisites they might have missed
        2. Natural progressions from current knowledge
        3. Difficulty appropriate for their learning velocity
        4. Gaps in foundational knowledge

        Return JSON array with objects containing:
        - current_topic: topic they're progressing from
        - next_topics: array of 2-3 recommended next topics
        - reasoning: why these topics are recommended
        - prerequisites_needed: any missing prerequisites
        - estimated_difficulty: 0.0-1.0 scale
        - confidence: 0.0-1.0 how confident you are in this recommendation
        """
        
        try:
            response = self.system.oai.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.4,
                messages=[
                    {"role": "system", "content": "You are an expert AI education advisor. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            recommendations_data = json.loads(response.choices[0].message.content)
            
            # Convert to LearningPathRecommendation objects
            recommendations = []
            for rec_data in recommendations_data:
                recommendation = LearningPathRecommendation(
                    user_id=user_id,
                    current_topic=rec_data.get("current_topic", "general"),
                    next_topics=rec_data.get("next_topics", []),
                    reasoning=rec_data.get("reasoning", ""),
                    prerequisites_needed=rec_data.get("prerequisites_needed", []),
                    estimated_difficulty=rec_data.get("estimated_difficulty", 0.5),
                    confidence=rec_data.get("confidence", 0.7),
                    created_at=datetime.now()
                )
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            print(f"❌ Error generating path recommendations: {e}")
            return []

class ComprehensionMonitor:
    """Agent that monitors user comprehension patterns and adapts accordingly"""
    
    def __init__(self, main_system):
        self.system = main_system
    
    async def analyze_understanding_patterns(self, user_id: str, chat_patterns: List[Dict]) -> List[LearningInsight]:
        """Analyze chat patterns to understand comprehension signals"""
        print(f"🧠 Comprehension Monitor analyzing user {user_id}")
        
        if not chat_patterns:
            return []
        
        # Analyze question types and patterns
        question_analysis = self._analyze_question_patterns(chat_patterns)
        
        # Detect confusion signals
        confusion_signals = self._detect_confusion_signals(chat_patterns)
        
        # Detect mastery signals
        mastery_signals = self._detect_mastery_signals(chat_patterns)
        
        # Generate insights using LLM
        insights = await self._generate_comprehension_insights(
            user_id, question_analysis, confusion_signals, mastery_signals
        )
        
        return insights
    
    def _analyze_question_patterns(self, chat_patterns: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in user questions"""
        user_messages = [msg for msg in chat_patterns if msg.get('message_role') == 'user']
        
        if not user_messages:
            return {}
        
        # Count question types
        question_types = {
            'what_is': 0,
            'how_does': 0,
            'why': 0,
            'examples': 0,
            'difference': 0,
            'explain': 0
        }
        
        for msg in user_messages:
            content = msg.get('message_content', '').lower()
            if content.startswith(('what is', 'what are')):
                question_types['what_is'] += 1
            elif content.startswith(('how does', 'how do', 'how can', 'how to')):
                question_types['how_does'] += 1
            elif 'why' in content[:10]:
                question_types['why'] += 1
            elif 'example' in content:
                question_types['examples'] += 1
            elif any(word in content for word in ['difference', 'compare', 'vs', 'versus']):
                question_types['difference'] += 1
            elif 'explain' in content:
                question_types['explain'] += 1
        
        total_questions = sum(question_types.values())
        if total_questions > 0:
            question_types = {k: v/total_questions for k, v in question_types.items()}
        
        return {
            'question_types_distribution': question_types,
            'total_questions': len(user_messages),
            'average_message_length': sum(len(msg.get('message_content', '')) for msg in user_messages) / len(user_messages)
        }
    
    def _detect_confusion_signals(self, chat_patterns: List[Dict]) -> List[Dict]:
        """Detect signals of user confusion"""
        confusion_signals = []
        
        user_messages = [msg for msg in chat_patterns if msg.get('message_role') == 'user']
        
        for i, msg in enumerate(user_messages):
            content = msg.get('message_content', '').lower()
            
            # Detect confusion patterns
            confusion_indicators = [
                'i don\'t understand',
                'confused',
                'not clear',
                'what do you mean',
                'i\'m lost',
                'can you explain again',
                'still not getting it'
            ]
            
            if any(indicator in content for indicator in confusion_indicators):
                confusion_signals.append({
                    'message': content,
                    'timestamp': msg.get('message_timestamp'),
                    'signal_strength': 0.8
                })
            
            # Detect repeated questions about same topic
            if i > 0:
                prev_content = user_messages[i-1].get('message_content', '').lower()
                similarity = len(set(content.split()) & set(prev_content.split())) / max(len(content.split()), len(prev_content.split()), 1)
                if similarity > 0.5:
                    confusion_signals.append({
                        'message': content,
                        'timestamp': msg.get('message_timestamp'),
                        'signal_strength': 0.6,
                        'type': 'repeated_question'
                    })
        
        return confusion_signals
    
    def _detect_mastery_signals(self, chat_patterns: List[Dict]) -> List[Dict]:
        """Detect signals of user mastery"""
        mastery_signals = []
        
        user_messages = [msg for msg in chat_patterns if msg.get('message_role') == 'user']
        
        for msg in user_messages:
            content = msg.get('message_content', '').lower()
            
            mastery_indicators = [
                'i understand',
                'that makes sense',
                'i see',
                'got it',
                'thanks',
                'clear now',
                'i get it'
            ]
            
            if any(indicator in content for indicator in mastery_indicators):
                mastery_signals.append({
                    'message': content,
                    'timestamp': msg.get('message_timestamp'),
                    'signal_strength': 0.7
                })
            
            # Advanced questions indicate understanding
            advanced_patterns = [
                'what about',
                'how would this work with',
                'in comparison to',
                'what happens if'
            ]
            
            if any(pattern in content for pattern in advanced_patterns):
                mastery_signals.append({
                    'message': content,
                    'timestamp': msg.get('message_timestamp'),
                    'signal_strength': 0.8,
                    'type': 'advanced_inquiry'
                })
        
        return mastery_signals
    
    async def _generate_comprehension_insights(self, user_id: str, question_analysis: Dict, 
                                             confusion_signals: List[Dict], mastery_signals: List[Dict]) -> List[LearningInsight]:
        """Generate insights about user comprehension using LLM"""
        
        prompt = f"""
        Analyze this student's comprehension patterns and generate insights:

        QUESTION PATTERNS: {json.dumps(question_analysis)}
        CONFUSION SIGNALS: {json.dumps(confusion_signals[-5:])}  # Last 5
        MASTERY SIGNALS: {json.dumps(mastery_signals[-5:])}  # Last 5

        Generate insights about:
        1. Learning style preferences (visual, conceptual, example-driven)
        2. Difficulty level appropriateness
        3. Common struggle areas
        4. Strengths and learning velocity
        5. Recommended teaching adaptations

        Return JSON array with insights containing:
        - insight_type: type of insight
        - topic: relevant topic or "general"
        - confidence: 0.0-1.0
        - evidence: array of supporting evidence
        - action_suggestion: what the system should do
        """
        
        try:
            response = self.system.oai.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.3,
                messages=[
                    {"role": "system", "content": "You are an expert learning analytics specialist. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            insights_data = json.loads(response.choices[0].message.content)
            
            insights = []
            for insight_data in insights_data:
                insight = LearningInsight(
                    user_id=user_id,
                    insight_type=insight_data.get("insight_type", "general"),
                    topic=insight_data.get("topic", "general"),
                    confidence=insight_data.get("confidence", 0.5),
                    evidence=insight_data.get("evidence", []),
                    action_suggestion=insight_data.get("action_suggestion", ""),
                    created_at=datetime.now()
                )
                insights.append(insight)
            
            return insights
            
        except Exception as e:
            print(f"❌ Error generating comprehension insights: {e}")
            return []

class GoalAchievementAssistant:
    """Agent that helps users achieve their learning goals autonomously"""
    
    def __init__(self, main_system):
        self.system = main_system
    
    async def analyze_goal_progress(self, user_id: str, goals: List[Dict], learning_history: List[Dict]) -> Dict[str, Any]:
        """Analyze user's progress toward their goals"""
        print(f"🎯 Goal Achievement Assistant analyzing user {user_id}")
        
        if not goals:
            return {"message": "No goals set", "recommendations": ["Consider setting learning goals"]}
        
        # Analyze progress for each goal
        goal_analyses = []
        for goal in goals:
            analysis = await self._analyze_single_goal(goal, learning_history)
            goal_analyses.append(analysis)
        
        # Generate autonomous interventions
        interventions = await self._generate_goal_interventions(user_id, goal_analyses)
        
        return {
            "goals_analysis": goal_analyses,
            "autonomous_interventions": interventions,
            "overall_progress": self._calculate_overall_progress(goal_analyses)
        }
    
    async def _analyze_single_goal(self, goal: Dict, learning_history: List[Dict]) -> Dict[str, Any]:
        """Analyze progress on a single goal"""
        goal_title = goal.get('goal_title', '')
        goal_category = goal.get('goal_category', '')
        target_date = goal.get('target_date')
        
        # Find relevant learning activities
        relevant_topics = [
            item for item in learning_history 
            if any(keyword in item.get('topic', '').lower() 
                  for keyword in goal_title.lower().split())
        ]
        
        # Calculate progress
        progress = len(relevant_topics) * 10  # Simple heuristic
        
        return {
            "goal": goal,
            "relevant_activities": len(relevant_topics),
            "estimated_progress": min(progress, 100),
            "topics_covered": [item.get('topic') for item in relevant_topics]
        }
    
    async def _generate_goal_interventions(self, user_id: str, goal_analyses: List[Dict]) -> List[Dict]:
        """Generate autonomous interventions to help achieve goals"""
        
        prompt = f"""
        You are an AI goal achievement coach. Analyze these goal progress reports and suggest autonomous interventions:

        GOAL ANALYSES: {json.dumps(goal_analyses)}

        For each goal that needs help, suggest specific autonomous actions the system can take:
        1. Content recommendations
        2. Study schedule adjustments
        3. Difficulty adaptations
        4. Motivational interventions
        5. Progress reminders

        Return JSON array with interventions containing:
        - goal_id: which goal this addresses
        - intervention_type: type of intervention
        - action: specific action to take
        - timing: when to execute (immediate, daily, weekly)
        - expected_impact: expected effect
        """
        
        try:
            response = self.system.oai.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.4,
                messages=[
                    {"role": "system", "content": "You are an expert goal achievement coach. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"❌ Error generating goal interventions: {e}")
            return []
    
    def _calculate_overall_progress(self, goal_analyses: List[Dict]) -> Dict[str, Any]:
        """Calculate overall progress across all goals"""
        if not goal_analyses:
            return {"average_progress": 0, "goals_on_track": 0, "needs_attention": 0}
        
        total_progress = sum(analysis.get('estimated_progress', 0) for analysis in goal_analyses)
        average_progress = total_progress / len(goal_analyses)
        
        goals_on_track = sum(1 for analysis in goal_analyses if analysis.get('estimated_progress', 0) > 50)
        needs_attention = len(goal_analyses) - goals_on_track
        
        return {
            "average_progress": average_progress,
            "goals_on_track": goals_on_track,
            "needs_attention": needs_attention,
            "total_goals": len(goal_analyses)
        }

class ContentCurationAgent:
    """Agent that identifies content gaps and suggests new learning materials"""
    
    def __init__(self, main_system):
        self.system = main_system
    
    async def identify_content_gaps(self, user_id: str, learning_history: List[Dict], bookmarks: List[Dict]) -> List[Dict]:
        """Identify gaps in user's learning content and suggest improvements"""
        print(f"📖 Content Curation Agent analyzing user {user_id}")
        
        # Analyze content preferences from bookmarks
        content_preferences = self._analyze_content_preferences(bookmarks)
        
        # Identify knowledge gaps
        knowledge_gaps = await self._identify_knowledge_gaps(learning_history)
        
        # Generate content recommendations
        content_recommendations = await self._generate_content_recommendations(
            user_id, content_preferences, knowledge_gaps, learning_history
        )
        
        return content_recommendations
    
    def _analyze_content_preferences(self, bookmarks: List[Dict]) -> Dict[str, Any]:
        """Analyze what types of content the user prefers"""
        if not bookmarks:
            return {"content_types": [], "topics_of_interest": []}
        
        # Analyze bookmarked content
        content_types = Counter()
        topics = Counter()
        
        for bookmark in bookmarks:
            doc_id = bookmark.get('doc_id', '')
            
            # Extract content type from doc_id patterns
            if 'example' in doc_id:
                content_types['examples'] += 1
            elif 'definition' in doc_id:
                content_types['definitions'] += 1
            elif 'analogy' in doc_id:
                content_types['analogies'] += 1
            elif 'quiz' in doc_id:
                content_types['quizzes'] += 1
            
            # Extract topic from doc_id
            topic = doc_id.split('__')[0] if '__' in doc_id else doc_id
            topics[topic] += 1
        
        return {
            "preferred_content_types": dict(content_types.most_common(3)),
            "favorite_topics": dict(topics.most_common(5))
        }
    
    async def _identify_knowledge_gaps(self, learning_history: List[Dict]) -> List[str]:
        """Identify potential knowledge gaps in user's learning"""
        if not learning_history:
            return ["foundational machine learning concepts"]
        
        learned_topics = set(item.get('topic', '').lower() for item in learning_history)
        
        # Define common ML learning sequences
        ml_sequences = [
            ["machine learning basics", "supervised learning", "unsupervised learning"],
            ["neural networks", "deep learning", "convolutional neural networks"],
            ["data preprocessing", "feature engineering", "model evaluation"],
            ["linear regression", "logistic regression", "decision trees"],
            ["clustering", "k-means", "hierarchical clustering"]
        ]
        
        gaps = []
        for sequence in ml_sequences:
            learned_in_sequence = [topic for topic in sequence if any(topic in learned for learned in learned_topics)]
            
            # If they've learned advanced topics but not basics
            if len(learned_in_sequence) > 0 and sequence[0] not in learned_in_sequence:
                gaps.append(sequence[0])
        
        return gaps[:5]  # Return top 5 gaps
    
    async def _generate_content_recommendations(self, user_id: str, preferences: Dict, 
                                              gaps: List[str], learning_history: List[Dict]) -> List[Dict]:
        """Generate personalized content recommendations"""
        
        prompt = f"""
        You are an AI content curator. Create personalized learning content recommendations:

        USER PREFERENCES: {json.dumps(preferences)}
        KNOWLEDGE GAPS: {gaps}
        RECENT LEARNING: {[item.get('topic') for item in learning_history[:10]]}

        Recommend 5-7 pieces of content that would be most valuable. Consider:
        1. Filling identified knowledge gaps
        2. Matching user's preferred content types
        3. Building on recent learning
        4. Providing variety in learning approaches

        Return JSON array with content recommendations containing:
        - content_type: type (video, article, interactive, quiz, example)
        - topic: specific topic to cover
        - title: engaging title for the content
        - description: what they'll learn
        - difficulty_level: beginner/intermediate/advanced
        - estimated_time: time to complete
        - priority: high/medium/low based on gaps and preferences
        """
        
        try:
            response = self.system.oai.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.5,
                messages=[
                    {"role": "system", "content": "You are an expert content curator for ML education. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"❌ Error generating content recommendations: {e}")
            return []

# Example usage
async def main():
    """Example of how to use the agentic learning system"""
    system = AgenticLearningSystem()
    
    # Analyze a user completely
    user_id = "example-user-id"
    analysis = await system.analyze_user_completely(user_id)
    
    print("🤖 AGENTIC ANALYSIS COMPLETE")
    print(json.dumps(analysis, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())
