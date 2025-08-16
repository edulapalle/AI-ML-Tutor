#!/usr/bin/env python3
"""
Weekly Learning Email Service using SendGrid
Sends personalized learning reports to users based on their progress
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import jinja2
import httpx
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    """Handles sending learning reports and notifications using SendGrid"""
    
    def __init__(self):
        # SendGrid configuration
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@ailearning.com")
        self.from_name = os.getenv("FROM_NAME", "AI Learning Platform")
        
        # Supabase configuration
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        # Template engine
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader('email_templates'),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        if not self.sendgrid_api_key:
            print("⚠️ Warning: SENDGRID_API_KEY not found in environment variables")
            print("   Email functionality will not work without SendGrid API key")
        else:
            print(f"📧 Email service initialized with SendGrid API")
    
    async def get_user_weekly_data(self, user_id: str) -> Dict[str, Any]:
        """Get user's learning data for the past week"""
        
        # Calculate date range for the past week
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # Get user profile
                user_response = await client.get(
                    f"{self.supabase_url}/rest/v1/users",
                    headers=headers,
                    params={"id": f"eq.{user_id}", "select": "*"}
                )
                user_data = user_response.json()
                if not user_data:
                    return None
                user = user_data[0]
                
                # Get learning path progress (topics explored this week)
                learning_response = await client.get(
                    f"{self.supabase_url}/rest/v1/user_learning_path",
                    headers=headers,
                    params={
                        "user_id": f"eq.{user_id}",
                        "explored_at": f"gte.{start_date.isoformat()}",
                        "order": "explored_at.desc",
                        "select": "*"
                    }
                )
                weekly_topics = learning_response.json()
                
                # Get chat history (learning activity this week)
                chat_response = await client.get(
                    f"{self.supabase_url}/rest/v1/chat_history",
                    headers=headers,
                    params={
                        "user_id": f"eq.{user_id}",
                        "message_timestamp": f"gte.{start_date.isoformat()}",
                        "order": "message_timestamp.desc",
                        "limit": "50",
                        "select": "*"
                    }
                )
                weekly_chats = chat_response.json()
                
                # Get bookmarks/stars
                stars_response = await client.get(
                    f"{self.supabase_url}/rest/v1/user_stars",
                    headers=headers,
                    params={
                        "user_id": f"eq.{user_id}",
                        "created_at": f"gte.{start_date.isoformat()}",
                        "select": "*"
                    }
                )
                weekly_stars = stars_response.json()
                
                # Get all learning path for next concepts
                all_topics_response = await client.get(
                    f"{self.supabase_url}/rest/v1/user_learning_path",
                    headers=headers,
                    params={
                        "user_id": f"eq.{user_id}",
                        "order": "explored_at.desc",
                        "limit": "20",
                        "select": "topic"
                    }
                )
                all_topics = [item['topic'] for item in all_topics_response.json()]
                
                return {
                    "user": user,
                    "weekly_topics": weekly_topics,
                    "weekly_chats": weekly_chats,
                    "weekly_stars": weekly_stars,
                    "all_topics": all_topics,
                    "week_start": start_date,
                    "week_end": end_date
                }
                
            except Exception as e:
                print(f"❌ Error fetching user data: {e}")
                return None
    
    def generate_next_concepts(self, explored_topics: List[str]) -> List[str]:
        """Generate next learning concepts based on explored topics"""
        
        # ML learning progression map
        concept_progressions = {
            "machine learning": ["supervised learning", "unsupervised learning", "model evaluation"],
            "supervised learning": ["linear regression", "logistic regression", "decision trees"],
            "unsupervised learning": ["clustering", "dimensionality reduction", "anomaly detection"],
            "linear regression": ["polynomial regression", "regularization", "feature selection"],
            "logistic regression": ["classification metrics", "confusion matrix", "roc curve"],
            "decision trees": ["random forests", "ensemble methods", "boosting"],
            "neural networks": ["deep learning", "backpropagation", "activation functions"],
            "deep learning": ["convolutional neural networks", "recurrent neural networks", "transformers"],
            "clustering": ["k-means", "hierarchical clustering", "dbscan"],
            "dimensionality reduction": ["pca", "t-sne", "feature selection"],
            "model evaluation": ["cross validation", "overfitting", "bias variance tradeoff"]
        }
        
        next_concepts = set()
        
        # Generate suggestions based on what they've learned
        for topic in explored_topics:
            if topic.lower() in concept_progressions:
                next_concepts.update(concept_progressions[topic.lower()])
        
        # Remove concepts they've already explored
        explored_lower = [t.lower() for t in explored_topics]
        next_concepts = [c for c in next_concepts if c not in explored_lower]
        
        # If no progressions found, suggest fundamentals
        if not next_concepts:
            next_concepts = ["machine learning", "supervised learning", "data preprocessing"]
        
        return list(next_concepts)[:5]  # Return top 5 suggestions
    
    def generate_learning_insights(self, weekly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights and recommendations from weekly data"""
        
        user = weekly_data["user"]
        weekly_topics = weekly_data["weekly_topics"]
        weekly_chats = weekly_data["weekly_chats"]
        weekly_stars = weekly_data["weekly_stars"]
        all_topics = weekly_data["all_topics"]
        
        # Calculate metrics
        topics_learned = len(weekly_topics)
        questions_asked = len([chat for chat in weekly_chats if chat.get('role') == 'user'])
        concepts_bookmarked = len(weekly_stars)
        total_learning_time = topics_learned * 5 + questions_asked * 2  # Rough estimate in minutes
        
        # Generate achievements
        achievements = []
        if topics_learned >= 5:
            achievements.append("🏆 Explorer: Learned 5+ new concepts this week!")
        if questions_asked >= 10:
            achievements.append("🤔 Curious Mind: Asked 10+ thoughtful questions!")
        if concepts_bookmarked >= 3:
            achievements.append("⭐ Collector: Bookmarked 3+ important concepts!")
        if topics_learned >= 3 and questions_asked >= 5:
            achievements.append("🚀 Super Learner: Great balance of exploration and inquiry!")
        
        # Learning streak
        unique_days = len(set(
            datetime.fromisoformat(chat['message_timestamp'].replace('Z', '+00:00')).date()
            for chat in weekly_chats
        ))
        
        # Get next concepts
        next_concepts = self.generate_next_concepts(all_topics)
        
        # Progress level
        total_concepts = len(all_topics)
        if total_concepts < 5:
            level = "Beginner Explorer"
            level_emoji = "🌱"
        elif total_concepts < 15:
            level = "Growing Learner"
            level_emoji = "🌿"
        elif total_concepts < 30:
            level = "Advanced Student"  
            level_emoji = "🌳"
        else:
            level = "ML Expert"
            level_emoji = "🧠"
        
        return {
            "topics_learned": topics_learned,
            "questions_asked": questions_asked,
            "concepts_bookmarked": concepts_bookmarked,
            "total_learning_time": total_learning_time,
            "achievements": achievements,
            "learning_days": unique_days,
            "next_concepts": next_concepts,
            "total_concepts": total_concepts,
            "level": level,
            "level_emoji": level_emoji,
            "weekly_topics_list": [topic['topic'] for topic in weekly_topics],
            "favorite_topics": [star.get('note', 'Interesting concept!') for star in weekly_stars[:3]]
        }
    
    async def send_weekly_report(self, user_id: str, test_mode: bool = False) -> bool:
        """Send weekly learning report to user using SendGrid"""
        
        print(f"📧 Generating weekly report for user {user_id}")
        
        # Check SendGrid API key
        if not self.sendgrid_api_key:
            print("❌ SENDGRID_API_KEY not configured")
            return False
        
        # Get user data
        weekly_data = await self.get_user_weekly_data(user_id)
        if not weekly_data:
            print("❌ Could not fetch user data")
            return False
        
        user = weekly_data["user"]
        email = user.get("email")
        if not email:
            print("❌ User email not found")
            return False
        
        # Generate insights
        insights = self.generate_learning_insights(weekly_data)
        
        # Prepare template context
        context = {
            "user": user,
            "insights": insights,
            "week_start": weekly_data["week_start"].strftime("%B %d"),
            "week_end": weekly_data["week_end"].strftime("%B %d, %Y"),
            "age_group": user.get("age_group", "student"),
            "username": user.get("username", "Learner"),
            "current_year": datetime.now().year
        }
        
        try:
            # Load and render template
            template = self.template_env.get_template("weekly_report.html")
            html_content = template.render(context)
            
            subject = f"🎓 Your Weekly Learning Report - {insights['topics_learned']} New Concepts!"
            
            # Send email (or print in test mode)
            if test_mode:
                print("📧 TEST MODE - Email content:")
                print(f"To: {email}")
                print(f"Subject: {subject}")
                print("="*50)
                print(html_content[:500] + "..." if len(html_content) > 500 else html_content)
                return True
            else:
                # Send via SendGrid API
                return await self.send_via_sendgrid(
                    to_email=email,
                    to_name=user.get("username", "Learner"),
                    subject=subject,
                    html_content=html_content
                )
                
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False
    
    async def send_via_sendgrid(self, to_email: str, to_name: str, subject: str, html_content: str) -> bool:
        """Send email using SendGrid API"""
        
        sendgrid_url = "https://api.sendgrid.com/v3/mail/send"
        
        # Prepare SendGrid payload
        payload = {
            "personalizations": [
                {
                    "to": [
                        {
                            "email": to_email,
                            "name": to_name
                        }
                    ],
                    "subject": subject
                }
            ],
            "from": {
                "email": self.from_email,
                "name": self.from_name
            },
            "content": [
                {
                    "type": "text/html",
                    "value": html_content
                }
            ],
            "tracking_settings": {
                "click_tracking": {
                    "enable": True,
                    "enable_text": False
                },
                "open_tracking": {
                    "enable": True
                }
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.sendgrid_api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    sendgrid_url,
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 202:
                    print(f"✅ Email sent successfully to {to_email}")
                    return True
                else:
                    print(f"❌ SendGrid API error: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error calling SendGrid API: {e}")
            return False
    
    async def send_bulk_weekly_reports(self, test_mode: bool = False) -> Dict[str, int]:
        """Send weekly reports to all active users"""
        
        print("📧 Starting bulk weekly report generation...")
        
        # Get all users who have been active in the past week
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # Get users who were active this week
                active_users_response = await client.get(
                    f"{self.supabase_url}/rest/v1/chat_history",
                    headers=headers,
                    params={
                        "message_timestamp": f"gte.{start_date.isoformat()}",
                        "select": "user_id",
                        "order": "user_id"
                    }
                )
                
                active_user_ids = list(set(
                    chat["user_id"] for chat in active_users_response.json()
                ))
                
                print(f"📊 Found {len(active_user_ids)} active users this week")
                
                # Send reports
                results = {"sent": 0, "failed": 0, "total": len(active_user_ids)}
                
                for user_id in active_user_ids:
                    try:
                        success = await self.send_weekly_report(user_id, test_mode)
                        if success:
                            results["sent"] += 1
                        else:
                            results["failed"] += 1
                        
                        # Small delay to avoid overwhelming SMTP server
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        print(f"❌ Failed to send report to user {user_id}: {e}")
                        results["failed"] += 1
                
                print(f"📊 Bulk email results: {results['sent']} sent, {results['failed']} failed")
                return results
                
            except Exception as e:
                print(f"❌ Error in bulk email sending: {e}")
                return {"sent": 0, "failed": 0, "total": 0, "error": str(e)}

# Global email service instance
email_service = None

def get_email_service() -> EmailService:
    """Get or create email service instance"""
    global email_service
    if email_service is None:
        email_service = EmailService()
    return email_service
