import os
import time
import datetime
import random
import base64
import io
import traceback
import time
import streamlit as st
import pandas as pd
from PIL import Image
from dotenv import load_dotenv
from contextlib import contextmanager  # for any local context managers

from database_pool import get_db_cursor, db_pool  # ↪ use the Postgres pool!

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

def send_submission_confirmation_email(recipient: str, student_name: str, roll_no: str, profile: str, drive_link: str):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    email_from = os.getenv("EMAIL_FROM")

    # Build message
    msg = MIMEMultipart("related")
    msg["Subject"] = f"CV Submission Confirmed - {student_name}"
    msg["From"]    = email_from
    msg["To"]      = recipient

    # Create alternative container for HTML and text
    msg_alternative = MIMEMultipart("alternative")
    msg.attach(msg_alternative)

    # Embed logo image
    try:
        with open("Logo/CQlogo2.png", "rb") as f:
            img_data = f.read()
        
        image = MIMEImage(img_data)
        image.add_header("Content-ID", "<cq_logo>")
        image.add_header("Content-Disposition", "inline", filename="CQlogo2.png")
        msg.attach(image)
        
        logo_src = "cid:cq_logo"
    except:
        # Fallback if logo file not found
        logo_src = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjYwIiB2aWV3Qm94PSIwIDAgMjAwIDYwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iNjAiIGZpbGw9IiM0ZmFjZmUiLz48dGV4dCB4PSIxMDAiIHk9IjM1IiBmaWxsPSJ3aGl0ZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE4IiBmb250LXdlaWdodD0iYm9sZCIgdGV4dC1hbmNob3I9Im1pZGRsZSI+Q29tbXVuaXF1w6k8L3RleHQ+PC9zdmc+"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CV Submission Confirmed</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh;">
        <div style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);">
            
            <!-- Header with Logo -->
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px 20px; text-align: center; position: relative;">
                <div style="background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; display: inline-block; margin-bottom: 15px;">
                    <img src="{logo_src}" alt="Communiqué Logo" style="max-width: 200px; height: auto; border-radius: 8px; background-color: #ffffff; padding: 10px;">
                </div>
                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    ✅ CV Submission Confirmed!
                </h1>
                <p style="color: rgba(255, 255, 255, 0.9); margin: 10px 0 0 0; font-size: 16px;">
                    Your CV has been successfully submitted for review
                </p>
            </div>
            
            <!-- Main Content -->
            <div style="padding: 40px 30px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h2 style="color: #2c3e50; margin: 0 0 10px 0; font-size: 24px; font-weight: 600;">
                        Thank you, {student_name}! 🎉
                    </h2>
                    <p style="color: #5a6c7d; font-size: 16px; line-height: 1.6; margin: 0;">
                        We have received your CV submission and it will be reviewed by one of our experienced seniors.
                    </p>
                </div>
                
                <!-- Submission Details Section -->
                <div style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); border-radius: 12px; padding: 25px; margin: 30px 0; position: relative; overflow: hidden;">
                    <h3 style="color: #ffffff; margin: 0 0 20px 0; font-size: 20px; font-weight: 600; text-align: center;">
                        📋 Submission Details
                    </h3>
                    
                    <div style="background-color: rgba(255, 255, 255, 0.95); border-radius: 8px; padding: 20px; margin: 15px 0;">
                        <div style="display: grid; gap: 15px;">
                            <div style="border-left: 4px solid #3b82f6; padding-left: 15px;">
                                <h4 style="color: #3b82f6; margin: 0 0 5px 0; font-size: 16px; font-weight: 600;">
                                    👤 Student Name
                                </h4>
                                <p style="color: #374151; margin: 0; font-size: 15px;">
                                    {student_name}
                                </p>
                            </div>
                            
                            <div style="border-left: 4px solid #10b981; padding-left: 15px;">
                                <h4 style="color: #10b981; margin: 0 0 5px 0; font-size: 16px; font-weight: 600;">
                                    🎓 Roll Number
                                </h4>
                                <p style="color: #374151; margin: 0; font-size: 15px;">
                                    {roll_no}
                                </p>
                            </div>
                            
                            <div style="border-left: 4px solid #f59e0b; padding-left: 15px;">
                                <h4 style="color: #f59e0b; margin: 0 0 5px 0; font-size: 16px; font-weight: 600;">
                                    🎯 Target Profile
                                </h4>
                                <p style="color: #374151; margin: 0; font-size: 15px;">
                                    {profile}
                                </p>
                            </div>
                            
                            <div style="border-left: 4px solid #8b5cf6; padding-left: 15px;">
                                <h4 style="color: #8b5cf6; margin: 0 0 5px 0; font-size: 16px; font-weight: 600;">
                                    📧 Email Address
                                </h4>
                                <p style="color: #374151; margin: 0; font-size: 15px;">
                                    {recipient}
                                </p>
                            </div>
                            
                            <div style="border-left: 4px solid #ef4444; padding-left: 15px;">
                                <h4 style="color: #ef4444; margin: 0 0 5px 0; font-size: 16px; font-weight: 600;">
                                    📁 CV Drive Link
                                </h4>
                                <p style="color: #374151; margin: 0; font-size: 15px;">
                                    <a href="{drive_link}" style="color: #3b82f6; text-decoration: none;">View CV on Drive</a>
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- What's Next Section -->
                <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); border-radius: 12px; padding: 25px; margin: 30px 0; position: relative; overflow: hidden;">
                    <h3 style="color: #ffffff; margin: 0 0 15px 0; font-size: 20px; font-weight: 600; text-align: center;">
                        🚀 What Happens Next?
                    </h3>
                    
                    <div style="background-color: rgba(255, 255, 255, 0.95); border-radius: 8px; padding: 20px; margin: 15px 0;">
                        <div style="color: #374151; font-size: 15px; line-height: 1.7;">
                            <p style="margin: 0 0 15px 0;">
                                <strong>1. Assignment:</strong> Your CV will be assigned to a senior reviewer who specializes in the <strong>{profile}</strong> domain.
                            </p>
                            <p style="margin: 0 0 15px 0;">
                                <strong>2. Review Process:</strong> The reviewer will provide detailed feedback across multiple categories including structure, content, and domain relevance.
                            </p>
                            <p style="margin: 0 0 15px 0;">
                                <strong>3. Feedback Delivery:</strong> You'll receive a comprehensive email with structured feedback within 2-3 business days.
                            </p>
                            <p style="margin: 0;">
                                <strong>4. Implementation:</strong> Use the feedback to enhance your CV and improve your chances in future applications.
                            </p>
                        </div>
                    </div>
                </div>
                
                <!-- PrepNest Section -->
                <div style="background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); border-radius: 12px; padding: 25px; margin: 30px 0; position: relative; overflow: hidden;">
                    <h2 style="font-size: 22px; color: #8b4513; margin: 0 0 15px 0; font-weight: 600;">
                        🚀 Meanwhile, Explore PrepNest Platform
                    </h2>
                    
                    <p style="font-size: 16px; line-height: 1.6; margin: 0 0 20px 0; color: #6b4423;">
                        While you wait for your CV review, we recommend exploring <strong>PrepNest.in</strong> - a comprehensive platform built specifically for internships and placements. Get instant AI-powered feedback and enhance your preparation!
                    </p>
                    
                    <h3 style="font-size: 18px; color: #8b4513; margin: 20px 0 15px 0; font-weight: 600;">
                        PrepNest offers four key features:
                    </h3>
                    
                    <div style="margin: 20px 0;">
                        <div style="background-color: rgba(255, 255, 255, 0.7); padding: 15px; border-radius: 8px; margin: 12px 0; border-left: 4px solid #10b981;">
                            <h4 style="font-size: 16px; color: #10b981; margin: 0 0 8px 0; font-weight: 600;">
                                🤖 1. AI Resume Review
                            </h4>
                            <p style="font-size: 14px; line-height: 1.6; margin: 0; color: #374151;">
                                Get instant, comprehensive feedback on your resume with AI-powered analysis. Receive detailed insights on content, formatting, ATS compatibility, and industry-specific recommendations.
                            </p>
                        </div>
                        
                        <div style="background-color: rgba(255, 255, 255, 0.7); padding: 15px; border-radius: 8px; margin: 12px 0; border-left: 4px solid #3b82f6;">
                            <h4 style="font-size: 16px; color: #3b82f6; margin: 0 0 8px 0; font-weight: 600;">
                                🎤 2. AI Interviews
                            </h4>
                            <p style="font-size: 14px; line-height: 1.6; margin: 0; color: #374151;">
                                Practice with AI-powered mock interviews tailored to your target role. Get real-time feedback on your responses, communication skills, and interview performance.
                            </p>
                        </div>
                        
                        <div style="background-color: rgba(255, 255, 255, 0.7); padding: 15px; border-radius: 8px; margin: 12px 0; border-left: 4px solid #f59e0b;">
                            <h4 style="font-size: 16px; color: #f59e0b; margin: 0 0 8px 0; font-weight: 600;">
                                📚 3. Resource Hub
                            </h4>
                            <p style="font-size: 14px; line-height: 1.6; margin: 0; color: #374151;">
                                Access a comprehensive library of career resources including interview guides, resume templates, industry insights, and preparation materials for various domains.
                            </p>
                        </div>
                        
                        <div style="background-color: rgba(255, 255, 255, 0.7); padding: 15px; border-radius: 8px; margin: 12px 0; border-left: 4px solid #ef4444;">
                            <h4 style="font-size: 16px; color: #ef4444; margin: 0 0 8px 0; font-weight: 600;">
                                👥 4. Mentorship & Jobs Portal
                            </h4>
                            <p style="font-size: 14px; line-height: 1.6; margin: 0; color: #374151;">
                                Connect with industry mentors for personalized career guidance and explore curated job opportunities from top companies across various sectors.
                            </p>
                        </div>
                    </div>
                    
                    <div style="text-align: center; margin: 25px 0 0 0;">
                        <a href="https://prepnest.in/?refercode=PrepGrow-sahib-singhprepgrowthpartner-02" 
                           style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; padding: 15px 30px; 
                                  text-decoration: none; border-radius: 25px; font-size: 16px; font-weight: 600;
                                  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4); transition: all 0.3s ease;
                                  border: 2px solid transparent;">
                            🌟 Explore PrepNest Platform
                        </a>
                    </div>
                </div>
                
                <!-- Closing -->
                <div style="text-align: center; padding: 25px 0; border-top: 2px solid #e5e7eb; margin-top: 30px;">
                    <p style="font-size: 16px; line-height: 1.6; margin: 0 0 15px 0; color: #5a6c7d;">
                        Thank you for choosing <span style="color: #667eea; font-weight: 600;">Communiqué's CDC Companion</span>. We're excited to help you enhance your CV!
                    </p>
                    
                    <p style="font-size: 16px; line-height: 1.6; margin: 0; color: #2c3e50;">
                        Best regards,<br>
                        <strong style="color: #667eea;">Communiqué</strong>
                    </p>
                </div>
            </div>
        </div>
        
        <!-- Floating elements for visual appeal -->
        <div style="position: fixed; top: 10%; left: 5%; width: 20px; height: 20px; background: rgba(255, 255, 255, 0.3); border-radius: 50%; animation: float 3s ease-in-out infinite;"></div>
        <div style="position: fixed; top: 60%; right: 10%; width: 15px; height: 15px; background: rgba(255, 255, 255, 0.2); border-radius: 50%; animation: float 4s ease-in-out infinite reverse;"></div>
        
        <style>
            @keyframes float {{
                0%, 100% {{ transform: translateY(0px); }}
                50% {{ transform: translateY(-10px); }}
            }}
            @media only screen and (max-width: 600px) {{
                .container {{ width: 95% !important; margin: 10px auto !important; }}
                .content {{ padding: 20px !important; }}
            }}
        </style>
    </body>
    </html>
    """
    part = MIMEText(html, "html")
    msg_alternative.attach(part)

    # Send
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(email_from, [recipient], msg.as_string())
        return True
    except Exception as e:
        print(f"Error sending confirmation email: {e}")
        return False

def send_review_email(recipient: str, student_name: str, review_data: dict):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    email_from = os.getenv("EMAIL_FROM")

    # Build message
    msg = MIMEMultipart("related")
    msg["Subject"] = f"Your CV Review is Ready {student_name}"
    msg["From"]    = email_from
    msg["To"]      = recipient

    # Create alternative container for HTML and text
    msg_alternative = MIMEMultipart("alternative")
    msg.attach(msg_alternative)

    # Embed logo image
    try:
        with open("Logo/CQlogo2.png", "rb") as f:
            img_data = f.read()
        
        image = MIMEImage(img_data)
        image.add_header("Content-ID", "<cq_logo>")
        image.add_header("Content-Disposition", "inline", filename="CQlogo2.png")
        msg.attach(image)
        
        logo_src = "cid:cq_logo"
    except:
        # Fallback if logo file not found
        logo_src = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjYwIiB2aWV3Qm94PSIwIDAgMjAwIDYwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iNjAiIGZpbGw9IiM0ZmFjZmUiLz48dGV4dCB4PSIxMDAiIHk9IjM1IiBmaWxsPSJ3aGl0ZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE4IiBmb250LXdlaWdodD0iYm9sZCIgdGV4dC1hbmNob3I9Im1pZGRsZSI+Q29tbXVuaXF1w6k8L3RleHQ+PC9zdmc+"

    # Format structured review sections
    review_sections_html = ""
    sections = [
        ("structure_format", "📐 Structure & Format", "#3B82F6"),
        ("domain_relevance", "🎯 Relevance to Domain", "#10B981"),
        ("depth_explanation", "📊 Depth of Explanation", "#F59E0B"),
        ("language_grammar", "✍️ Language and Grammar", "#EF4444"),
        ("project_improvements", "🚀 Improvements in Projects", "#8B5CF6"),
        ("additional_suggestions", "💡 Additional Suggestions", "#06B6D4")
    ]
    
    for key, title, color in sections:
        content = review_data.get(key, "").strip()
        if content:
            review_sections_html += f"""
            <div style="background-color: rgba(255, 255, 255, 0.95); border-radius: 8px; padding: 20px; margin: 15px 0;">
                <div style="display: grid; gap: 15px;">
                    <div style="border-left: 4px solid {color}; padding-left: 15px;">
                        <h4 style="color: {color}; margin: 0 0 5px 0; font-size: 16px; font-weight: 600;">
                            {title}
                        </h4>
                        <p style="color: #374151; margin: 0; font-size: 15px;">
                            {content}
                        </p>
                    </div>
                </div>
            </div>
            """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CV Review Ready</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh;">
        <div style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);">
            
            <!-- Header with Logo -->
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 30px 20px; text-align: center; position: relative;">
                <div style="background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; display: inline-block; margin-bottom: 15px;">
                    <img src="{logo_src}" alt="Communiqué Logo" style="max-width: 200px; height: auto; border-radius: 8px; background-color: #ffffff; padding: 10px;">
                </div>
                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    🎯 CV Review Complete!
                </h1>
                <p style="color: rgba(255, 255, 255, 0.9); margin: 10px 0 0 0; font-size: 16px;">
                    Your personalized feedback is ready
                </p>
            </div>
            
            <!-- Main Content -->
            <div style="padding: 40px 30px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h2 style="color: #2c3e50; margin: 0 0 10px 0; font-size: 24px; font-weight: 600;">
                        Hi {student_name}! 👋
                    </h2>
                    <p style="color: #5a6c7d; font-size: 16px; line-height: 1.6; margin: 0;">
                        Great news! Your CV has been thoroughly reviewed by one of our experienced seniors.
                    </p>
                </div>
                
                <!-- Review Section -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 25px; margin: 30px 0; position: relative; overflow: hidden;">
                    <h3 style="color: #ffffff; margin: 0 0 20px 0; font-size: 20px; font-weight: 600; text-align: center;">
                        📝 Detailed Expert Feedback
                    </h3>
                    {review_sections_html}
                </div>
                
                <p style="font-size: 16px; line-height: 1.6; margin: 25px 0; color: #5a6c7d; text-align: center; font-style: italic;">
                    💡 We recommend implementing the feedback provided to strengthen your CV for future applications.
                </p>
                
                <!-- PrepNest Section -->
                <div style="background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); border-radius: 12px; padding: 25px; margin: 30px 0; position: relative; overflow: hidden;">
                    <h2 style="font-size: 22px; color: #8b4513; margin: 0 0 15px 0; font-weight: 600;">
                        🚀 Meanwhile, Explore PrepNest Platform
                    </h2>
                    
                    <p style="font-size: 16px; line-height: 1.6; margin: 0 0 20px 0; color: #6b4423;">
                        While you wait for your CV review, we recommend exploring <strong>PrepNest.in</strong> - a comprehensive platform built specifically for internships and placements. Get instant AI-powered feedback and enhance your preparation!
                    </p>
                    
                    <h3 style="font-size: 18px; color: #8b4513; margin: 20px 0 15px 0; font-weight: 600;">
                        PrepNest offers four key features:
                    </h3>
                    
                    <div style="margin: 20px 0;">
                        <div style="background-color: rgba(255, 255, 255, 0.7); padding: 15px; border-radius: 8px; margin: 12px 0; border-left: 4px solid #10b981;">
                            <h4 style="font-size: 16px; color: #10b981; margin: 0 0 8px 0; font-weight: 600;">
                                🤖 1. AI Resume Review
                            </h4>
                            <p style="font-size: 14px; line-height: 1.6; margin: 0; color: #374151;">
                                Get instant, comprehensive feedback on your resume with AI-powered analysis. Receive detailed insights on content, formatting, ATS compatibility, and industry-specific recommendations.
                            </p>
                        </div>
                        
                        <div style="background-color: rgba(255, 255, 255, 0.7); padding: 15px; border-radius: 8px; margin: 12px 0; border-left: 4px solid #3b82f6;">
                            <h4 style="font-size: 16px; color: #3b82f6; margin: 0 0 8px 0; font-weight: 600;">
                                🎤 2. AI Interviews
                            </h4>
                            <p style="font-size: 14px; line-height: 1.6; margin: 0; color: #374151;">
                                Practice with AI-powered mock interviews tailored to your target role. Get real-time feedback on your responses, communication skills, and interview performance.
                            </p>
                        </div>
                        
                        <div style="background-color: rgba(255, 255, 255, 0.7); padding: 15px; border-radius: 8px; margin: 12px 0; border-left: 4px solid #f59e0b;">
                            <h4 style="font-size: 16px; color: #f59e0b; margin: 0 0 8px 0; font-weight: 600;">
                                📚 3. Resource Hub
                            </h4>
                            <p style="font-size: 14px; line-height: 1.6; margin: 0; color: #374151;">
                                Access a comprehensive library of career resources including interview guides, resume templates, industry insights, and preparation materials for various domains.
                            </p>
                        </div>
                        
                        <div style="background-color: rgba(255, 255, 255, 0.7); padding: 15px; border-radius: 8px; margin: 12px 0; border-left: 4px solid #ef4444;">
                            <h4 style="font-size: 16px; color: #ef4444; margin: 0 0 8px 0; font-weight: 600;">
                                👥 4. Mentorship & Jobs Portal
                            </h4>
                            <p style="font-size: 14px; line-height: 1.6; margin: 0; color: #374151;">
                                Connect with industry mentors for personalized career guidance and explore curated job opportunities from top companies across various sectors.
                            </p>
                        </div>
                    </div>
                    
                    <div style="text-align: center; margin: 25px 0 0 0;">
                        <a href="https://prepnest.in/?refercode=PrepGrow-sahib-singhprepgrowthpartner-02" 
                           style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; padding: 15px 30px; 
                                  text-decoration: none; border-radius: 25px; font-size: 16px; font-weight: 600;
                                  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4); transition: all 0.3s ease;
                                  border: 2px solid transparent;">
                            🌟 Explore PrepNest Platform
                        </a>
                    </div>
                </div>
                
                <!-- Closing -->
                <div style="text-align: center; padding: 25px 0; border-top: 2px solid #e5e7eb; margin-top: 30px;">
                    <p style="font-size: 16px; line-height: 1.6; margin: 0 0 15px 0; color: #5a6c7d;">
                        Thank you for using <span style="color: #667eea; font-weight: 600;">Communiqué's CDC Companion</span>. We wish you the best of luck in your career journey!
                    </p>
                    
                    <p style="font-size: 16px; line-height: 1.6; margin: 0; color: #2c3e50;">
                        Best regards,<br>
                        <strong style="color: #667eea;">Communiqué</strong>
                    </p>
                </div>
            </div>
        </div>
        
        <!-- Floating elements for visual appeal -->
        <div style="position: fixed; top: 10%; left: 5%; width: 20px; height: 20px; background: rgba(255, 255, 255, 0.3); border-radius: 50%; animation: float 3s ease-in-out infinite;"></div>
        <div style="position: fixed; top: 60%; right: 10%; width: 15px; height: 15px; background: rgba(255, 255, 255, 0.2); border-radius: 50%; animation: float 4s ease-in-out infinite reverse;"></div>
        
        <style>
            @keyframes float {{
                0%, 100% {{ transform: translateY(0px); }}
                50% {{ transform: translateY(-10px); }}
            }}
            @media only screen and (max-width: 600px) {{
                .container {{ width: 95% !important; margin: 10px auto !important; }}
                .content {{ padding: 20px !important; }}
            }}
        </style>
    </body>
    </html>
    """
    part = MIMEText(html, "html")
    msg_alternative.attach(part)

    # Send
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(email_from, [recipient], msg.as_string())


# Streamlit page config
st.set_page_config(
    page_title="Communiqué | CDC Companion",
    page_icon='./Logo/favicon.ico',
)

# ========== PERFORMANCE MONITORING ==========

# def timing_decorator(func):
#     def wrapper(*args, **kwargs):
#         start = time.time()
#         result = func(*args, **kwargs)
#         elapsed = (time.time() - start) * 1000
#         if st.session_state.get('show_performance', False):
#             st.sidebar.text(f"• {func.__name__}: {elapsed:.2f}ms")
#         return result
#     return wrapper

# @st.cache_data(ttl=60)
# def get_app_performance_stats():
#     return {"cache_hits": st.cache_data.clear.__doc__,
#             "timestamp": datetime.datetime.now()}

def timing_decorator(func):
    """Dummy decorator - performance monitoring disabled"""
    return func

@timing_decorator
def load_reviewer_names():
    """Load reviewer names without caching to avoid connection issues"""
    with get_db_cursor() as (_, cur):
        cur.execute("SELECT DISTINCT name FROM reviewer_data ORDER BY name;")
        return [r["name"] for r in cur.fetchall()]

@st.cache_data(ttl=300)
def load_profiles():
    return ['Data', 'Software', 'Consult', 'Finance/Quant', 'Product', 'FMCG', 'Core']

@timing_decorator
@st.cache_data(show_spinner=False)
def pdf_to_base64(path: str):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except FileNotFoundError:
        return None

@timing_decorator
def get_reviewer_info(name: str):
    """Get reviewer info without caching to avoid connection issues"""
    with get_db_cursor() as (_, cur):
        cur.execute("""
            SELECT reviewsnumber, rprofilez, linkedin, email
            FROM reviewer_data WHERE UPPER(name)=UPPER(%s);
        """, (name,))
        return cur.fetchone()

@timing_decorator
def get_reviewer_count(name: str):
    """Get reviewer count without caching to avoid connection issues"""
    with get_db_cursor() as (_, cur):
        cur.execute("SELECT COUNT(*) AS cnt FROM reviews_data WHERE reviewer_name=%s;", (name,))
        return cur.fetchone()['cnt']

def get_table_download_link(df, filename, text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'

def show_pdf(path):
    b64 = pdf_to_base64(path)
    if b64:
        st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="700" height="1000"></iframe>',
                    unsafe_allow_html=True)
    else:
        st.warning("PDF preview unavailable.")

# def course_recommender(course_list):
#     st.subheader("**Courses & Certificates Recommendations 🎓**")
#     c = 0
#     rec_course = []
#     no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 5)
#     random.shuffle(course_list)
#     for c_name, c_link in course_list:
#         c += 1
#         st.markdown(f"({c}) [{c_name}]({c_link})")
#         rec_course.append(c_name)
#         if c == no_of_reco:
#             break
#     return rec_course

#CONNECT TO DATABASE

load_dotenv()

def insert_data_simple(name, roll_no, email, drive_link, profile):
    """Optimized user data insertion"""
    insert_sql = """
        INSERT INTO user_data (name, roll_no, email_id, drive_link, status_num, profiles)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    with get_db_cursor() as (_, cursor):  # ✅ Uses context manager
        cursor.execute(insert_sql, (name, roll_no, email, drive_link, 1, profile))
        # ✅ No manual commit/rollback - context manager handles it

def insert_data_reviewers(name, pwd, reviewsnum, cvsreviewed, linkedin, email, rprofilez=None):
    """Optimized reviewer insertion - now uses Name instead of UserName"""
    insert_sql = """
        INSERT INTO reviewer_data (name, password, reviewsnumber, cvsreviewed, linkedin, email, rprofilez)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    with get_db_cursor() as (_, cursor):
        cursor.execute(insert_sql, (name, pwd, reviewsnum, cvsreviewed, linkedin, email, rprofilez))

def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills, courses, drive_link, status, profile):
    """Legacy function - maintained for compatibility"""
    if name and email and drive_link and profile:
        insert_data_simple(name, email, email, drive_link, profile)
    else:
        st.error("Missing required fields for user data insertion")

def display_error_details(error_msg, exception):
    """Display detailed error information for debugging"""
    st.error(f"💥 {error_msg}")
    st.exception(exception)  # Shows full traceback in Streamlit
    print(f"\n{'='*50}")
    print(f"ERROR: {error_msg}")
    print(f"{'='*50}")
    print(traceback.format_exc())  # Logs to console
    print(f"{'='*50}\n")

def run():
    # Initialize both session state keys at the very top
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False
    if 'admin_user' not in st.session_state:
        st.session_state.admin_user = ""
    # if 'show_performance' not in st.session_state:
    #     st.session_state.show_performance = False
    
    img = Image.open('./Logo/CQlogo2.png')
    img = img.resize((1000, 300))
    st.image(img)
    st.title("Communiqué | CDC Companion")
    st.sidebar.markdown("# Choose User")
    activities = ["User", "Reviewer" ,"Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    
    # Performance monitoring section in sidebar
    # st.sidebar.markdown("---")
    # st.sidebar.markdown("### 🔧 Debug Tools")
    # st.session_state.show_performance = st.sidebar.checkbox(
    #     "Show Performance Metrics", 
    #     value=st.session_state.show_performance,
    #     help="Display execution times for database queries and other operations"
    # )
    
    # if st.session_state.show_performance:
    #     st.sidebar.markdown("**Performance Metrics:**")
    #     if 'performance_metrics' not in st.session_state:
    #         st.session_state.performance_metrics = {}
    
    link = '[Developed by ©Communiqué](https://www.cqiitkgp.com/)'
    st.sidebar.markdown(link, unsafe_allow_html=True)


    # ✅ No DB initialization here - done once at startup
    # Continue with UI logic...

    if choice == 'User':
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Enter your Name:", placeholder="Jhonny Bravo")
        with col2:
            roll_no = st.text_input("Enter your Roll Number:", placeholder="22XX9999")
        
        if name and roll_no:
            # --- START VALIDATIONS ---
            # 1. Roll number format validation
            is_valid_roll_format = False
            if len(roll_no) > 4:
                if (roll_no.startswith("22") and roll_no[4] == '3') or \
                   (roll_no.startswith("23") and roll_no[4] == '1'):
                    is_valid_roll_format = True

            # 2. Check for existing submission in database
            is_duplicate = False
            with get_db_cursor() as (_, cursor):
                cursor.execute("SELECT id FROM user_data WHERE roll_no = %s", (roll_no,))
                if cursor.fetchone():
                    is_duplicate = True
            
            # --- RENDER UI BASED ON VALIDATION ---
            if not is_valid_roll_format:
                st.error("You are not permitted to use this portal. Please ensure your roll number is correct (e.g., starts with '22...3...' or '23...1...').")
            elif is_duplicate:
                st.warning("⚠️ You have already submitted a CV for review.")
                st.info("Each student may only submit once. If you believe this is an error, please contact the administrators.")
            else:
                # --- VALIDATED: SHOW THE REST OF THE FORM ---
                st.markdown('''
                    <h3 style='text-align: left; color: #FF4B4B; margin-top: 20px; margin-bottom: 20px;'>
                        📄 Drop your Resume here to get it reviewed by seniors
                    </h3>
                    <p style='text-align: left; color: #FFF; font-size: 16px;'>
                        Get personalized feedback from seniors in your chosen field
                    </p>
                    ''', unsafe_allow_html=True)
                
                pdf_file = st.file_uploader("Upload your Resume (PDF format)", type=["pdf"])
                if pdf_file is not None and roll_no:
                    # Enforce 2 MB max
                    if pdf_file.size > 2 * 1024 * 1024:
                        st.error("🚨 File too large—please upload a PDF under 2 MB.")
                    else:
                        # Always save as <roll_no>.pdf so display_code can find it
                        save_path = f'./Uploaded_Resumes/{roll_no}.pdf'
                        with st.spinner('Processing your Resume...'):
                            os.makedirs(os.path.dirname(save_path), exist_ok=True)
                            with open(save_path, "wb") as f:
                                f.write(pdf_file.getbuffer())
                        show_pdf(save_path)

                # Move profile selection here, after file upload and preview
                profile = st.selectbox("Select your target profile:", load_profiles(), 
                                     help="Choose the profile you're interested in for your career")
                
                st.markdown(
                    """
                    <div style='background-color: #1E1E1E; padding: 20px; border-radius: 10px; margin: 20px 0;'>
                        <h2 style='color: #FF4B4B;'>Almost there! 🎯</h2>
                        <p style='color: #FFF; font-size: 16px;'>Please provide your contact details below to receive your review.</p>
                        <p style='color: #888; font-size: 14px;'>Note: You can submit only one CV for review</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

                # ✅ FIXED: Always show inputs, check duplicates only on Submit
                st.write("( Make sure you have provided access to your CV in the drive link )")
                email_input = st.text_input("Enter your KGP EmailID here: ", placeholder="yourname@kgpian.iitkgp.ac.in")
                
                # Email validation
                is_valid_email = False
                if email_input:
                    if email_input.endswith("@kgpian.iitkgp.ac.in"):
                        is_valid_email = True
                        st.success("✅ Valid KGP email format")
                    else:
                        st.error("❌ Please use your KGP email ending with @kgpian.iitkgp.ac.in")
                
                drive_link = st.text_input("Enter your Drive Link: ")
                
                if st.button("Submit for Review", type="primary"):
                    try:
                        # 1️⃣ Validate email format first
                        if not email_input:
                            st.error("Please enter your KGP email address.")
                        elif not email_input.endswith("@kgpian.iitkgp.ac.in"):
                            st.error("❌ Please use your official KGP email ending with @kgpian.iitkgp.ac.in")
                        elif not drive_link:
                            st.error("Please provide your drive link.")
                        else:
                            # All validations passed - proceed with submission
                            insert_data_simple(name, roll_no, email_input, drive_link, profile)
                            
                            # Send confirmation email
                            email_sent = send_submission_confirmation_email(
                                email_input, name, roll_no, profile, drive_link
                            )
                            
                            # ✅ Persistent success message
                            st.success("🎉 **CV Submission Successful!**")
                            
                            if email_sent:
                                st.info("📧 **Confirmation email sent!** Check your inbox for submission details.")
                            else:
                                st.warning("⚠️ **CV submitted successfully, but confirmation email failed.** Please contact support if needed.")
                            
                            st.markdown(
                                f"""
                                <div style='background-color: #1E3A8A; padding: 20px; border-radius: 10px; margin: 20px 0;'>
                                    <h3 style='color: #60A5FA; margin-bottom: 15px; text-align: center;'>✅ Thank you, {name}!</h3>
                                    <div style='color: #FFF; font-size: 16px; text-align: center;'>
                                        <p><strong>Your CV for the {profile} profile has been submitted successfully!</strong></p>
                                        <p>📧 You'll receive detailed feedback from our expert reviewers soon.</p>
                                        <p style='color: #60A5FA;'>💡 Check your email for submission confirmation and next steps!</p>
                                    </div>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )
                            
                            # AI CV Review Link
                            st.markdown(
                                """
                                <div style='background-color: #2D1B69; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #8B5CF6;'>
                                    <p style='color: #FFF; font-size: 16px; margin: 0;'>
                                        🤖 While you wait for your CV to get reviewed by a senior, get your CV reviewed by AI via the following link: 
                                        <a href='https://prepnest.in/?refercode=PrepGrow-sahib-singhprepgrowthpartner-02' target='_blank' style='color: #A78BFA; text-decoration: underline;'>PrepNest AI CV Review</a>
                                    </p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            
                            # PrepNest Platform Details
                            st.markdown(
                                """
                                <div style='background-color: #1F2937; padding: 20px; border-radius: 10px; margin: 20px 0; border: 1px solid #374151;'>
                                    <h3 style='color: #F3F4F6; margin-bottom: 15px; text-align: center;'>🚀 About PrepNest Platform</h3>
                                    <p style='color: #D1D5DB; font-size: 16px; text-align: center; margin-bottom: 20px;'>
                                        <strong>PrepNest.in</strong> is a comprehensive platform built specifically for internships and placements. 
                                        PrepNest is designed to empower students and professionals in their career journey with cutting-edge AI technology and expert guidance.
                                    </p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            
                            # Feature cards using separate markdown blocks
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown(
                                    """
                                    <div style='background-color: #111827; padding: 15px; border-radius: 8px; border-left: 4px solid #10B981; margin-bottom: 15px;'>
                                        <h4 style='color: #10B981; margin: 0 0 8px 0; font-size: 18px;'>🤖 AI Resume Review</h4>
                                        <p style='color: #D1D5DB; font-size: 14px; margin: 0;'>
                                            Get instant, comprehensive feedback on your resume with AI-powered analysis. 
                                            Receive detailed insights on content, formatting, ATS compatibility, and industry-specific recommendations.
                                        </p>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                                
                                st.markdown(
                                    """
                                    <div style='background-color: #111827; padding: 15px; border-radius: 8px; border-left: 4px solid #F59E0B;'>
                                        <h4 style='color: #F59E0B; margin: 0 0 8px 0; font-size: 18px;'>📚 Resource Hub</h4>
                                        <p style='color: #D1D5DB; font-size: 14px; margin: 0;'>
                                            Access a comprehensive library of career resources including interview guides, 
                                            resume templates, industry insights, and preparation materials for various domains.
                                        </p>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                            
                            with col2:
                                st.markdown(
                                    """
                                    <div style='background-color: #111827; padding: 15px; border-radius: 8px; border-left: 4px solid #3B82F6; margin-bottom: 15px;'>
                                        <h4 style='color: #3B82F6; margin: 0 0 8px 0; font-size: 18px;'>🎤 AI Interviews</h4>
                                        <p style='color: #D1D5DB; font-size: 14px; margin: 0;'>
                                            Practice with AI-powered mock interviews tailored to your target role. 
                                            Get real-time feedback on your responses, communication skills, and interview performance.
                                        </p>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                                
                                st.markdown(
                                    """
                                    <div style='background-color: #111827; padding: 15px; border-radius: 8px; border-left: 4px solid #EF4444;'>
                                        <h4 style='color: #EF4444; margin: 0 0 8px 0; font-size: 18px;'>👥 Mentorship & Jobs Portal</h4>
                                        <p style='color: #D1D5DB; font-size: 14px; margin: 0;'>
                                            Connect with industry mentors for personalized career guidance and explore 
                                            curated job opportunities from top companies across various sectors.
                                        </p>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                            
                            # Call-to-action button
                            st.markdown(
                                """
                                <div style='text-align: center; margin: 20px 0;'>
                                    <a href='https://prepnest.in/?refercode=PrepGrow-sahib-singhprepgrowthpartner-02' target='_blank' 
                                       style='background-color: #8B5CF6; color: white; padding: 12px 24px; text-decoration: none; 
                                              border-radius: 6px; font-weight: bold; display: inline-block;'>
                                        🌟 Explore PrepNest Platform
                                    </a>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            
                            st.balloons()

                    except Exception as e:
                        display_error_details("CV submission failed", e)
    elif choice == 'Admin':
        # First check session state
        if not st.session_state.admin_logged_in:
            st.success('Welcome to Admin Side')
            user = st.text_input("Username", key="admin_user_input")
            pwd = st.text_input("Password", type="password", key="admin_pass_input")
            if st.button("Login"):
                if user == "sujay" and pwd == "sujay123":
                    st.session_state.admin_logged_in = True
                    st.session_state.admin_user = user
                    st.rerun()
                else:
                    st.error("Wrong ID & Password")
            return  # Don't render anything else until they're logged in

        # ---- LOGGED IN! ----
        st.success(f"Welcome {st.session_state.admin_user}!")
        
        # Logout button
        if st.button("🚪 Logout"):
            st.session_state.admin_logged_in = False
            st.rerun()

        # 1) Always re-fetch your tables here
        with get_db_cursor() as (_, cursor):
            try:
                # 📊 EDITABLE USER DATA
                st.header("**User's Data (Editable)**")
                cursor.execute("""
                    SELECT
                        id,
                        name,
                        roll_no,
                        email_id,
                        drive_link,
                        status_num,
                        profiles,
                        assigned_to
                    FROM user_data
                """)
                user_data = cursor.fetchall()
                user_df = pd.DataFrame(user_data, columns=[
                    'id', 'name', 'roll_no', 'email_id', 'drive_link', 
                    'status_num', 'profiles', 'assigned_to'
                ])

                # Get list of reviewers for the dropdown
                reviewer_names = load_reviewer_names()
                
                # Configure column types for better editing experience
                column_config = {
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "status_num": st.column_config.SelectboxColumn(
                        "Status",
                        options=[0, 1, 2],
                        help="0=Submitted, 1=Pending Review, 2=Reviewed"
                    ),
                    "profiles": st.column_config.SelectboxColumn(
                        "Profile",
                        options=load_profiles()
                    ),
                    "assigned_to": st.column_config.TextColumn(
                        "Assigned To",
                        help="Reviewer who has claimed this CV"
                    ),
                    "drive_link": st.column_config.LinkColumn("Drive Link"),
                }

                # 2) Show the editor
                edited_user_df = st.data_editor(
                    user_df,
                    column_config=column_config,
                    num_rows="dynamic",
                    use_container_width=True,
                    key="user_data_editor"
                )

                # 3) Save button
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("💾 Save User Data Changes", type="primary"):
                        try:
                            # 🔧 FIX: Normalize ID columns to handle int/float mismatch
                            original_ids = set(user_df['id'].tolist())
                            edited_ids = {
                                int(x) for x in edited_user_df['id'].tolist()
                                if not pd.isna(x)
                            }
                            deleted_ids = original_ids - edited_ids
                            
                            # Delete removed rows
                            for deleted_id in deleted_ids:
                                cursor.execute("DELETE FROM user_data WHERE id = %s", (deleted_id,))
                            
                            # Update/Insert rows
                            for _, row in edited_user_df.iterrows():
                                if pd.isna(row['id']):
                                    # New row - INSERT
                                    cursor.execute("""
                                        INSERT INTO user_data (name, roll_no, email_id, drive_link, status_num, profiles, assigned_to)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                                    """, (row['name'], row['roll_no'], row['email_id'], row['drive_link'], 
                                          row['status_num'], row['profiles'], row['assigned_to']))
                                else:
                                    # Existing row - UPDATE
                                    cursor.execute("""
                                        UPDATE user_data 
                                        SET name=%s, roll_no=%s, email_id=%s, drive_link=%s, 
                                            status_num=%s, profiles=%s, assigned_to=%s
                                        WHERE id=%s
                                    """, (row['name'], row['roll_no'], row['email_id'], row['drive_link'],
                                          row['status_num'], row['profiles'], row['assigned_to'], int(row['id'])))
                            
                            st.success("✅ User data saved successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error saving user data: {e}")

                with col2:
                    st.markdown(get_table_download_link(edited_user_df,'User_Data.csv','📥 Download User Data'), unsafe_allow_html=True)

                st.markdown("---")

                # 👥 EDITABLE REVIEWER DATA  
                st.header("**Reviewer's Data (Editable)**")
                cursor.execute("""
                    SELECT
                        rd.id,
                        rd.name,
                        rd.password,
                        rd.reviewsnumber,
                        COALESCE(rv.completed, 0) AS cvsreviewed,
                        rd.linkedin,
                        rd.email,
                        rd.rprofilez
                    FROM reviewer_data rd
                    LEFT JOIN (
                        SELECT reviewer_name, COUNT(*) as completed
                        FROM reviews_data
                        GROUP BY reviewer_name
                    ) rv
                    ON rv.reviewer_name = rd.name
                """)
                reviewer_data = cursor.fetchall()
                reviewer_df = pd.DataFrame(reviewer_data, columns=[
                    'id', 'name', 'password', 'reviewsnumber', 'cvsreviewed', 'linkedin', 'email', 'rprofilez'
                ])

                reviewer_column_config = {
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "reviewsnumber": st.column_config.NumberColumn("Review Quota", min_value=0, max_value=100),
                    "cvsreviewed": st.column_config.NumberColumn("CVs Reviewed", min_value=0, disabled=True),
                    "rprofilez": st.column_config.SelectboxColumn(
                        "Domain",
                        options=load_profiles()
                    ),
                    "linkedin": st.column_config.LinkColumn("LinkedIn Profile"),
                    "email": st.column_config.TextColumn("Email"),
                    "password": st.column_config.TextColumn("Password", help="Reviewer login password")
                }

                edited_reviewer_df = st.data_editor(
                    reviewer_df,
                    column_config=reviewer_column_config,
                    num_rows="dynamic",
                    use_container_width=True,
                    key="reviewer_data_editor"
                )

                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("💾 Save Reviewer Data Changes", type="primary"):
                        try:
                            # 🔧 FIX: Normalize ID columns
                            original_ids = set(reviewer_df['id'].tolist())
                            edited_ids = {
                                int(x) for x in edited_reviewer_df['id'].tolist()
                                if not pd.isna(x)
                            }
                            deleted_ids = original_ids - edited_ids
                            
                            # Delete removed rows
                            for deleted_id in deleted_ids:
                                cursor.execute("DELETE FROM reviewer_data WHERE id = %s", (deleted_id,))
                            
                            # Update/Insert rows - Note: Cvsreviewed is now derived, not stored
                            for _, row in edited_reviewer_df.iterrows():
                                if pd.isna(row['id']):
                                    # New row - INSERT
                                    cursor.execute("""
                                        INSERT INTO reviewer_data (name, password, reviewsnumber, linkedin, email, rprofilez)
                                        VALUES (%s, %s, %s, %s, %s, %s)
                                    """, (row['name'], row['password'], row['reviewsnumber'], 
                                          row['linkedin'], row['email'], row['rprofilez']))
                                else:
                                    # Existing row - UPDATE
                                    cursor.execute("""
                                        UPDATE reviewer_data 
                                        SET name=%s, password=%s, reviewsnumber=%s, 
                                            linkedin=%s, email=%s, rprofilez=%s
                                        WHERE id=%s
                                    """, (row['name'], row['password'], row['reviewsnumber'],
                                          row['linkedin'], row['email'], row['rprofilez'], int(row['id'])))
                            
                            st.success("✅ Reviewer data saved successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error saving reviewer data: {e}")

                with col2:
                    st.markdown(get_table_download_link(edited_reviewer_df,'Reviewer_Data.csv','📥 Download Reviewer Data'), unsafe_allow_html=True)

                st.markdown("---")

                # 📝 EDITABLE REVIEWS DATA
                st.header("**Reviews Data (Editable)**")
                # 1) Fetch all columns from reviews table including structured sections
                cursor.execute("""
                  SELECT
                    id, name, roll_no, email_id, reviewer_name, reviewer_linkedin, reviewer_email,
                    drive_link, review, structure_format, domain_relevance, depth_explanation,
                    language_grammar, project_improvements, additional_suggestions, submission_time
                  FROM reviews_data
                  ORDER BY submission_time DESC
                """)
                cols = ["id","name","roll_no","email_id","reviewer_name","reviewer_linkedin","reviewer_email",
                       "drive_link","review","structure_format","domain_relevance","depth_explanation",
                       "language_grammar","project_improvements","additional_suggestions","submission_time"]
                reviews_df = pd.DataFrame(cursor.fetchall(), columns=cols)

                reviews_column_config = {
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "roll_no": st.column_config.TextColumn("Roll Number"),
                    "email_id": st.column_config.TextColumn("Candidate Email"),
                    "reviewer_linkedin": st.column_config.LinkColumn("Reviewer LinkedIn"),
                    "reviewer_email": st.column_config.TextColumn("Reviewer Email"),
                    "drive_link": st.column_config.LinkColumn("Drive Link"),
                    "review": st.column_config.TextColumn("Legacy Review", width="medium", help="Old single review field"),
                    "structure_format": st.column_config.TextColumn("Structure & Format", width="large"),
                    "domain_relevance": st.column_config.TextColumn("Domain Relevance", width="large"),
                    "depth_explanation": st.column_config.TextColumn("Depth Explanation", width="large"),
                    "language_grammar": st.column_config.TextColumn("Language & Grammar", width="large"),
                    "project_improvements": st.column_config.TextColumn("Project Improvements", width="large"),
                    "additional_suggestions": st.column_config.TextColumn("Additional Suggestions", width="large"),
                    "submission_time": st.column_config.DatetimeColumn("Submission Time", disabled=True),
                }

                edited_reviews_df = st.data_editor(
                    reviews_df,
                    column_config=reviews_column_config,
                    num_rows="dynamic",
                    use_container_width=True,
                    key="reviews_data_editor"
                )

                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("💾 Save Reviews Data Changes", type="primary"):
                        try:
                            # Handle row deletions first
                            original_ids = set(reviews_df['id'].tolist())
                            edited_ids = {
                                int(x) for x in edited_reviews_df['id'].tolist()
                                if not pd.isna(x)
                            }
                            deleted_ids = original_ids - edited_ids
                            
                            # Delete removed rows
                            for deleted_id in deleted_ids:
                                cursor.execute("DELETE FROM reviews_data WHERE id = %s", (deleted_id,))
                            
                            # Process each row for insert/update
                            for _, row in edited_reviews_df.iterrows():
                                # map blank → None
                                def norm(v):
                                    return None if (pd.isna(v) or str(v).strip()=="") else v

                                email_id = norm(row["email_id"])
                                reviewer_linkedin = norm(row["reviewer_linkedin"])
                                reviewer_email = norm(row["reviewer_email"])
                                drive_link = norm(row["drive_link"])
                                review_text = norm(row["review"])
                                structure_format = norm(row["structure_format"])
                                domain_relevance = norm(row["domain_relevance"])
                                depth_explanation = norm(row["depth_explanation"])
                                language_grammar = norm(row["language_grammar"])
                                project_improvements = norm(row["project_improvements"])
                                additional_suggestions = norm(row["additional_suggestions"])

                                if pd.isna(row["id"]):
                                    # New row - INSERT (submission_time will be auto-set by database)
                                    cursor.execute("""
                                      INSERT INTO reviews_data 
                                      (name, roll_no, email_id, reviewer_name, reviewer_linkedin, reviewer_email, 
                                       drive_link, review, structure_format, domain_relevance, depth_explanation,
                                       language_grammar, project_improvements, additional_suggestions)
                                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    """, (row["name"], row["roll_no"], email_id, row["reviewer_name"],
                                          reviewer_linkedin, reviewer_email, drive_link, review_text,
                                          structure_format, domain_relevance, depth_explanation,
                                          language_grammar, project_improvements, additional_suggestions))
                                else:
                                    # Existing row - UPDATE (don't update submission_time)
                                    cursor.execute("""
                                      UPDATE reviews_data SET 
                                      name=%s, roll_no=%s, email_id=%s, reviewer_name=%s, 
                                      reviewer_linkedin=%s, reviewer_email=%s, drive_link=%s, review=%s,
                                      structure_format=%s, domain_relevance=%s, depth_explanation=%s,
                                      language_grammar=%s, project_improvements=%s, additional_suggestions=%s
                                      WHERE id=%s
                                    """, (row["name"], row["roll_no"], email_id, row["reviewer_name"],
                                          reviewer_linkedin, reviewer_email, drive_link, review_text,
                                          structure_format, domain_relevance, depth_explanation,
                                          language_grammar, project_improvements, additional_suggestions, int(row["id"])))
                            
                            st.success("✅ Reviews data saved successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error saving reviews data: {e}")

                with col2:
                    st.markdown(get_table_download_link(edited_reviews_df,'Reviews_Data.csv','📥 Download Reviews Data'), unsafe_allow_html=True)

                st.markdown("---")

                # 🚀 NEW: CV ALLOCATION MANAGEMENT
                st.header("**CV Allocation Management 🎯**")
                
                # Debug section to show domain matching
                st.subheader("🔍 Domain Debug Information")
                allocation_stats = get_allocation_stats()
                if allocation_stats:
                    debug_df = pd.DataFrame([
                        {
                            "Reviewer": stat["name"], 
                            "Domains": stat["rprofilez"],
                            "Capacity": stat["remaining_capacity"],
                            "Total Assigned": stat["total_assigned"]
                        }
                        for stat in allocation_stats
                    ])
                    st.dataframe(debug_df, use_container_width=True)
                
                # Get allocation statistics for the download functionality
                allocation_stats = get_allocation_stats()
                
                # Unassigned CVs count
                with get_db_cursor() as (_, cur):
                    cur.execute("""
                        SELECT profiles, COUNT(*) as count
                        FROM user_data 
                        WHERE status_num = 1 AND assigned_to IS NULL
                        GROUP BY profiles
                    """)
                    unassigned_stats = cur.fetchall()
                
                if unassigned_stats:
                    st.subheader("Unassigned CVs by Profile")
                    unassigned_df = pd.DataFrame([
                        {"Profile": stat["profiles"], "Unassigned CVs": stat["count"]}
                        for stat in unassigned_stats
                    ])
                    st.dataframe(unassigned_df, use_container_width=True)
                
                # Allocation controls
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🚀 Run Smart Allocation", type="primary"):
                        allocation_result = smart_cv_allocation()
                        if allocation_result["allocated"] > 0:
                            st.success(f"✅ {allocation_result['message']}")
                            st.info("Details: " + ", ".join(allocation_result["details"]))
                            st.rerun()
                        else:
                            st.info("ℹ️ No CVs available for allocation")
                
                with col2:
                    if st.button("📊 Refresh Stats"):
                        # Force refresh of data
                        st.rerun()
                
                with col3:
                    if st.button("📥 Download Allocation Report"):
                        if allocation_stats:
                            report_df = pd.DataFrame(allocation_stats)
                            st.markdown(
                                get_table_download_link(report_df, 'allocation_report.csv', '📥 Download Report'),
                                unsafe_allow_html=True
                            )
                        else:
                            st.warning("No allocation data available to download.")

            except Exception as e:
                display_error_details("Admin dashboard data loading failed", e)
    else:
        #Reviewer Side of the page:
        def reviewer_login():
            if 'logged_in' not in st.session_state:
                st.session_state['logged_in'] = False

            if not st.session_state['logged_in']:
                st.success('Welcome to the Reviewers Side')
                reviewer_name = st.text_input("Enter your full name:")
                ad_password = st.text_input("Password", type='password')

                if st.button('Login'):
                    with get_db_cursor() as (conn, cursor):
                        try:
                            # Case-insensitive name lookup
                            cursor.execute(
                                "SELECT name, password FROM reviewer_data WHERE UPPER(name) = UPPER(%s)",
                                (reviewer_name,)
                            )
                            row = cursor.fetchone()
                            if row and ad_password == row['password']:
                                st.session_state['logged_in'] = True
                                st.session_state['ad_user'] = row['name']  # Use the exact name from DB
                                st.success(f"Welcome {row['name']}!")
                                st.rerun()
                            else:
                                st.error("Invalid name or password")
                        except Exception as e:
                            display_error_details("Reviewer login failed", e)
            else:
                display_review_section(st.session_state['ad_user'])

        # Function to display the review section
        def display_review_section(ad_user):
            if st.button('Logout'):
                st.session_state['logged_in'] = False
                st.rerun()

            st.success(f'Hello {ad_user}!')

            # Show any persisted success message
            if 'review_success_msg' in st.session_state:
                st.success(st.session_state['review_success_msg'])
                # Clear the message after showing it
                del st.session_state['review_success_msg']

            # 🔧 Get reviewer's quota & profile
            info = get_reviewer_info(ad_user)
            if not info:
                st.error("Reviewer not found!")
                return

            ReviewsNumber = info["reviewsnumber"]
            domain = info["rprofilez"]
            linkedin = info["linkedin"]
            reviewer_email = info["email"]

            # ✅ Compute the actual number of reviews this reviewer has already submitted
            reviewed_count = get_reviewer_count(ad_user)
            remaining = ReviewsNumber - reviewed_count

            if remaining <= 0:
                st.success("🎉 You've completed all your assigned reviews!")
                return

            # 🚀 NEW: Show allocation statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Reviews Completed", reviewed_count)
            with col2:
                st.metric("Remaining Capacity", remaining)
            with col3:
                st.metric("Your Domain", domain)

            # 🚀 NEW: Admin allocation control
            if st.button("🔄 Run Smart Allocation", help="Automatically assign unassigned CVs to best reviewers"):
                allocation_result = smart_cv_allocation()
                if allocation_result["allocated"] > 0:
                    st.success(f"✅ {allocation_result['message']}")
                    if st.session_state.show_performance:
                        st.info("Allocation details: " + ", ".join(allocation_result["details"]))
                else:
                    st.info("ℹ️ No CVs available for allocation")

            st.info(f"📝 You can review **{remaining}** more CV(s) in **{domain}**.")

            # 🔗 LinkedIn Profile Section (One-time setup)
            st.markdown("---")
            st.markdown("### 🔗 Your LinkedIn Profile")
            
            with st.form(key="linkedin_form"):
                current_linkedin = linkedin if linkedin else ""
                linkedin_input = st.text_input(
                    "LinkedIn URL (Optional)", 
                    value=current_linkedin,
                    placeholder="https://linkedin.com/in/your-profile",
                    help="Your LinkedIn profile will be shared with reviewees for networking opportunities"
                )
                
                linkedin_submitted = st.form_submit_button("💾 Update LinkedIn Profile")
                
                if linkedin_submitted:
                    final_linkedin = linkedin_input.strip() if linkedin_input.strip() else None
                    
                    # Update reviewer's LinkedIn profile
                    with get_db_cursor() as (_, cur):
                        cur.execute(
                            "UPDATE reviewer_data SET linkedin = %s WHERE name = %s",
                            (final_linkedin, ad_user)
                        )
                        # Clear cache to get updated LinkedIn info
                        get_reviewer_info.clear()
                        
                        if final_linkedin:
                            st.success("✅ LinkedIn profile updated successfully!")
                        else:
                            st.success("✅ LinkedIn profile cleared!")
                        
                        time.sleep(1)
                        st.rerun()

            st.markdown("---")

            # 🚀 NEW: Use improved CV fetching
            cvs = get_reviewer_assigned_cvs(ad_user, ReviewsNumber)

            if not cvs:
                st.warning("No CVs assigned to you right now.")
                st.info("💡 Click 'Run Smart Allocation' to get new CVs or wait for admin to assign them.")
                return

            # 4️⃣ Loop & render one form per CV
            for cv in cvs:
                roll, student, link, email_id, status = (
                    cv["roll_no"], cv["name"], cv["drive_link"], cv["email_id"], cv["status_num"]
                )
                
                # Get existing review data
                existing_reviews = {
                    "structure_format": cv.get("structure_format", ""),
                    "domain_relevance": cv.get("domain_relevance", ""),
                    "depth_explanation": cv.get("depth_explanation", ""),
                    "language_grammar": cv.get("language_grammar", ""),
                    "project_improvements": cv.get("project_improvements", ""),
                    "additional_suggestions": cv.get("additional_suggestions", "")
                }
                
                has_existing_review = any(existing_reviews.values())

                st.markdown("---")
                
                # 🚀 NEW: Enhanced CV header with submission time
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.image("./Logo/CVlogo.png", width=120)
                    st.write(f"**{student}**  (Roll: {roll})")
                with col2:
                    status_emoji = "✅" if status == 2 else "⏳"
                    status_text = "Reviewed" if status == 2 else "Pending"
                    st.write(f"{status_emoji} {status_text}")
                
                try:
                    show_pdf(f"./Uploaded_Resumes/{roll}.pdf")
                except FileNotFoundError:
                    st.warning("📄 PDF preview not available locally.")
                    st.markdown(f"[View on Drive]({link})")

                # Structured review form
                with st.form(key=f"form_{roll}", clear_on_submit=False):
                    st.markdown("### ✍️ Structured Review Sections")
                    
                    # Create tabs for better organization
                    tab1, tab2, tab3 = st.tabs(["📐 Format & Structure", "🎯 Content & Domain", "💡 Language & Suggestions"])
                    
                    with tab1:
                        structure_format = st.text_area(
                            "📐 Structure & Format",
                            value=existing_reviews["structure_format"] or "",
                            height=120,
                            placeholder="Comment on CV layout, formatting, whitespace usage, section organization, visual hierarchy, etc.",
                            help="Evaluate the overall visual presentation and structural organization of the CV"
                        )
                        
                        language_grammar = st.text_area(
                            "✍️ Language and Grammar",
                            value=existing_reviews["language_grammar"] or "",
                            height=120,
                            placeholder="Point out grammar issues, language clarity, professional tone, word choice, etc.",
                            help="Assess the quality of written communication and language usage"
                        )
                    
                    with tab2:
                        domain_relevance = st.text_area(
                            "🎯 Relevance to Domain",
                            value=existing_reviews["domain_relevance"] or "",
                            height=120,
                            placeholder="Assess how well the CV aligns with the target domain/profile, relevant skills highlighted, etc.",
                            help="Evaluate how well the CV matches the chosen career domain"
                        )
                        
                        depth_explanation = st.text_area(
                            "📊 Depth of Explanation",
                            value=existing_reviews["depth_explanation"] or "",
                            height=120,
                            placeholder="Comment on the detail level of project descriptions, achievements quantification, impact demonstration, etc.",
                            help="Assess the thoroughness and depth of content descriptions"
                        )
                        
                        project_improvements = st.text_area(
                            "🚀 Improvements in Projects",
                            value=existing_reviews["project_improvements"] or "",
                            height=120,
                            placeholder="Suggest specific improvements for project descriptions, technical details, outcomes, etc.",
                            help="Provide specific suggestions for enhancing project presentations"
                        )
                    
                    with tab3:
                        additional_suggestions = st.text_area(
                            "💡 Additional Suggestions",
                            value=existing_reviews["additional_suggestions"] or "",
                            height=140,
                            placeholder="Any other recommendations, missing sections, skills to add, certifications to pursue, etc.",
                            help="Provide any other valuable advice or recommendations"
                        )
                    
                    # Validation helper
                    review_sections = {
                        "structure_format": structure_format,
                        "domain_relevance": domain_relevance,
                        "depth_explanation": depth_explanation,
                        "language_grammar": language_grammar,
                        "project_improvements": project_improvements,
                        "additional_suggestions": additional_suggestions
                    }
                    
                    filled_sections = sum(1 for content in review_sections.values() if content.strip())
                    
                    # Progress indicator
                    st.progress(filled_sections / 6, text=f"Sections completed: {filled_sections}/6")
                    
                    # Submit button
                    btn_label = "✏️ Update Review" if has_existing_review else "🚀 Submit Review"
                    submitted = st.form_submit_button(btn_label, type="primary")

                # Handle submission
                if submitted:
                    if filled_sections == 0:
                        st.error("❌ Please fill at least one review section before submitting.")
                    else:
                        with get_db_cursor() as (_, cur2):
                            # Get current LinkedIn from reviewer profile
                            current_info = get_reviewer_info(ad_user)
                            current_linkedin = current_info["linkedin"] if current_info else linkedin
                            
                            if has_existing_review:
                                # Update existing review
                                cur2.execute("""
                                    UPDATE reviews_data SET 
                                    structure_format=%s, domain_relevance=%s, depth_explanation=%s,
                                    language_grammar=%s, project_improvements=%s, additional_suggestions=%s,
                                    reviewer_linkedin=%s
                                    WHERE roll_no=%s AND reviewer_name=%s
                                """, (
                                    structure_format.strip() or None,
                                    domain_relevance.strip() or None,
                                    depth_explanation.strip() or None,
                                    language_grammar.strip() or None,
                                    project_improvements.strip() or None,
                                    additional_suggestions.strip() or None,
                                    current_linkedin,
                                    roll, ad_user
                                ))
                                st.session_state['review_success_msg'] = f"✅ Updated review for {student}!"
                            else:
                                # Insert new review
                                cur2.execute("""
                                    INSERT INTO reviews_data
                                      (name, roll_no, email_id, reviewer_name, reviewer_linkedin,
                                       reviewer_email, drive_link, structure_format, domain_relevance,
                                       depth_explanation, language_grammar, project_improvements, 
                                       additional_suggestions)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """, (
                                    student, roll, email_id, ad_user, current_linkedin,
                                    reviewer_email or None, link,
                                    structure_format.strip() or None,
                                    domain_relevance.strip() or None,
                                    depth_explanation.strip() or None,
                                    language_grammar.strip() or None,
                                    project_improvements.strip() or None,
                                    additional_suggestions.strip() or None
                                ))
                                cur2.execute(
                                    "UPDATE user_data SET status_num = 2 WHERE roll_no = %s",
                                    (roll,)
                                )
                                st.session_state['review_success_msg'] = f"✅ Submitted review for {student}!"
                        
                        # Send structured email
                        send_review_email(email_id, student, review_sections)
                        
                        time.sleep(1.5)
                        st.rerun()

        reviewer_login()


# @contextmanager
# def get_db_cursor():
#     conn = db_pool.get_connection()
#     cursor = conn.cursor(pymysql.cursors.DictCursor)
#     try:
#         yield conn, cursor
#         conn.commit()
#     except:
#         conn.rollback()
#         raise
#     finally:
#         cursor.close()
#         conn.close()

# ========== IMPROVED CV ALLOCATION SYSTEM ==========

def get_allocation_stats():
    """Get current allocation statistics for load balancing"""
    try:
        with get_db_cursor() as (_, cur):
            cur.execute("""
                SELECT 
                    r.name,
                    r.rprofilez,
                    r.reviewsnumber,
                    COALESCE(rv.completed, 0) as completed_reviews,
                    COALESCE(rv.completed, 0) + COALESCE(pending.pending_count, 0) as total_assigned,
                    r.reviewsnumber - COALESCE(rv.completed, 0) as remaining_capacity
                FROM reviewer_data r
                LEFT JOIN (
                    SELECT reviewer_name, COUNT(*) as completed
                    FROM reviews_data
                    GROUP BY reviewer_name
                ) rv ON rv.reviewer_name = r.name
                LEFT JOIN (
                    SELECT assigned_to, COUNT(*) as pending_count
                    FROM user_data 
                    WHERE status_num = 1 AND assigned_to IS NOT NULL
                    GROUP BY assigned_to
                ) pending ON pending.assigned_to = r.name
                WHERE r.reviewsnumber > COALESCE(rv.completed, 0)
                ORDER BY r.rprofilez, total_assigned ASC
            """)
            return cur.fetchall()
    except Exception as e:
        print(f"Error getting allocation stats: {e}")
        return []

def smart_cv_allocation():
    """Intelligent CV allocation system with load balancing"""
    with get_db_cursor() as (_, cur):
        # Get unassigned CVs by profile
        cur.execute("""
            SELECT roll_no, profiles
            FROM user_data 
            WHERE status_num = 1 AND assigned_to IS NULL
            ORDER BY profiles, id ASC
        """)
        unassigned_cvs = cur.fetchall()
        
        if not unassigned_cvs:
            return {"allocated": 0, "message": "No unassigned CVs"}
        
        # Get available reviewers
        allocation_stats = get_allocation_stats()
        
        allocated_count = 0
        allocations_made = []
        
        for cv in unassigned_cvs:
            roll_no = cv["roll_no"]
            profile = cv["profiles"]
            
            # Find best reviewer for this profile
            best_reviewer = None
            min_workload = float('inf')
            
            for reviewer in allocation_stats:
                # Handle comma-separated domains in reviewer profiles
                reviewer_domains = [domain.strip() for domain in (reviewer["rprofilez"] or "").split(",")]
                
                # Check if the user's profile matches any of the reviewer's domains
                profile_match = False
                for domain in reviewer_domains:
                    # Normalize both strings for comparison (handle Finance-Quant vs Finance/Quant)
                    normalized_domain = domain.replace("/", "-").replace("-", "/").lower()
                    normalized_profile = profile.replace("/", "-").replace("-", "/").lower()
                    
                    if (domain.lower() == profile.lower() or 
                        normalized_domain == normalized_profile.lower() or
                        profile.lower() in domain.lower() or 
                        domain.lower() in profile.lower()):
                        profile_match = True
                        break
                
                if (profile_match and 
                    reviewer["remaining_capacity"] > 0 and
                    reviewer["total_assigned"] < min_workload):
                    best_reviewer = reviewer["name"]
                    min_workload = reviewer["total_assigned"]
            
            if best_reviewer:
                # Assign CV to best reviewer
                cur.execute(
                    "UPDATE user_data SET assigned_to = %s WHERE roll_no = %s",
                    (best_reviewer, roll_no)
                )
                allocated_count += 1
                allocations_made.append(f"{roll_no} → {best_reviewer}")
                
                # Update local stats to prevent double-assignment in this batch
                for reviewer in allocation_stats:
                    if reviewer["name"] == best_reviewer:
                        reviewer["total_assigned"] += 1
                        reviewer["remaining_capacity"] -= 1
                        break
        
        return {
            "allocated": allocated_count,
            "message": f"Allocated {allocated_count} CVs",
            "details": allocations_made
        }

@timing_decorator
def get_reviewer_assigned_cvs(reviewer_name: str, max_capacity: int):
    """Get CVs assigned to a specific reviewer with structured review data"""
    with get_db_cursor() as (_, cur):
        cur.execute("""
            SELECT u.roll_no, u.name, u.drive_link, u.email_id, u.status_num,
                   r.structure_format, r.domain_relevance, r.depth_explanation,
                   r.language_grammar, r.project_improvements, r.additional_suggestions
              FROM user_data u
              LEFT JOIN reviews_data r 
                ON u.roll_no = r.roll_no 
               AND r.reviewer_name = %s
             WHERE u.assigned_to = %s
             ORDER BY u.status_num ASC, u.id ASC
             LIMIT %s
        """, (reviewer_name, reviewer_name, max_capacity))
        return cur.fetchall()

if __name__ == "__main__":
    # ✅ Initialize database once at startup
    # init_db()
    
    # ✅ Run the main application
    run()