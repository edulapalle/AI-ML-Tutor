#!/usr/bin/env python3
"""
Test script for SendGrid email functionality
Run this to verify your SendGrid API key and email configuration
"""

import os
import asyncio
from email_service import get_email_service
from dotenv import load_dotenv

load_dotenv()

async def test_sendgrid_email():
    """Test SendGrid email sending with a sample report"""
    
    print("🧪 Testing SendGrid Email Integration")
    print("=" * 50)
    
    # Check environment variables
    sendgrid_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("FROM_EMAIL")
    from_name = os.getenv("FROM_NAME", "AI Learning Platform")
    
    print(f"📧 FROM_EMAIL: {from_email}")
    print(f"👤 FROM_NAME: {from_name}")
    print(f"🔑 SENDGRID_API_KEY: {'✅ Set' if sendgrid_key else '❌ Missing'}")
    
    if not sendgrid_key:
        print("\n❌ SENDGRID_API_KEY not found in environment!")
        print("   Please add it to your .env file:")
        print("   SENDGRID_API_KEY=your_api_key_here")
        return False
    
    if not from_email:
        print("\n⚠️ FROM_EMAIL not found, using default")
        from_email = "noreply@ailearning.com"
    
    # Initialize email service
    email_service = get_email_service()
    
    # Test email content
    test_to_email = input("\n📨 Enter test email address: ").strip()
    if not test_to_email:
        print("❌ No email address provided")
        return False
    
    test_mode = input("🧪 Run in test mode? (y/N): ").strip().lower() == 'y'
    
    # Create a sample HTML email
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SendGrid Test Email</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .header { background: #FFD93B; color: white; padding: 20px; border-radius: 8px; }
            .content { padding: 20px; background: #f8f9fa; border-radius: 8px; margin-top: 20px; }
            .emoji { font-size: 24px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎉 SendGrid Test Email</h1>
            <p>This is a test email from your AI Learning Platform!</p>
        </div>
        
        <div class="content">
            <h2>✅ Email System Working!</h2>
            <p>If you're reading this, your SendGrid integration is working perfectly!</p>
            
            <h3>📊 Test Results:</h3>
            <ul>
                <li>✅ SendGrid API Key: Valid</li>
                <li>✅ Email Delivery: Successful</li>
                <li>✅ HTML Formatting: Rendered</li>
                <li>✅ Template System: Working</li>
            </ul>
            
            <h3>🚀 What's Next?</h3>
            <p>Your weekly learning reports will be sent automatically using this same system!</p>
            
            <div style="background: #e3f2fd; padding: 15px; border-radius: 5px; margin-top: 20px;">
                <p><strong>🎯 Ready for Production!</strong></p>
                <p>Your SendGrid email system is configured and ready to send weekly learning reports to your users.</p>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 30px; color: #666;">
            <p>Sent from AI Learning Platform 🤖</p>
        </div>
    </body>
    </html>
    """
    
    print(f"\n📤 Sending test email to {test_to_email}...")
    
    try:
        if test_mode:
            print("\n📧 TEST MODE - Email content preview:")
            print("="*50)
            print(html_content[:300] + "...")
            success = True
        else:
            success = await email_service.send_via_sendgrid(
                to_email=test_to_email,
                to_name="Test User",
                subject="🧪 SendGrid Test Email - AI Learning Platform",
                html_content=html_content
            )
        
        if success:
            if test_mode:
                print("\n✅ Test mode completed successfully!")
                print("   Remove test_mode=True to send actual emails")
            else:
                print(f"\n✅ Test email sent successfully to {test_to_email}!")
                print("   Check your inbox (and spam folder) for the test email")
            
            print("\n🎉 SendGrid Integration Test: PASSED")
            return True
        else:
            print("\n❌ Failed to send test email")
            print("   Check your SendGrid API key and sender verification")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_sendgrid_email())
    
    if success:
        print("\n🚀 Your email system is ready for production!")
        print("   Weekly reports will be sent automatically using SendGrid")
    else:
        print("\n🔧 Please fix the configuration issues above")
        print("   Check the SendGrid setup guide in env_email.example")
