"""
Streamlit Frontend for CTOS Credit Behavior Insight Engine
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import sys

# Import your existing backend modules
from engine.credit_rule_engine import RuleEngine
from engine.data_input import extract_data_from_xml, normalize_data
from engine.output_aggregator import ConsoleOutputAggregator

# Page configuration
st.set_page_config(
    page_title="CTOS Score",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container styling */
    .main {
        background-color: #e8f4f5;
        padding: 0;
    }
    
    /* CTOS Score Card */
    .score-card {
        background: white;
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 20px auto;
        max-width: 600px;
    }
    
    .score-header {
        color: #5a9aa8;
        font-size: 14px;
        margin-bottom: 20px;
    }
    
    .score-gauge {
        width: 200px;
        height: 100px;
        margin: 20px auto;
    }
    
    .score-number {
        font-size: 72px;
        font-weight: bold;
        color: #2c3e50;
        margin: 10px 0;
    }
    
    .score-label {
        color: #7f8c8d;
        font-size: 14px;
        margin-bottom: 10px;
    }
    
    .score-date {
        color: #95a5a6;
        font-size: 12px;
        margin-bottom: 30px;
    }
    
    .ctos-button {
        background-color: #0e7c86;
        color: white;
        padding: 12px 24px;
        border-radius: 6px;
        border: none;
        width: 100%;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        margin-bottom: 10px;
    }
    
    .ctos-button-secondary {
        background-color: #f8f9fa;
        color: #495057;
        padding: 12px 24px;
        border-radius: 6px;
        border: 1px solid #dee2e6;
        width: 100%;
        font-size: 14px;
        cursor: pointer;
    }
    
    /* Info sections */
    .info-section {
        background: white;
        border-radius: 12px;
        padding: 30px;
        margin: 20px auto;
        max-width: 900px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .info-title {
        font-size: 18px;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 20px;
    }
    
    .info-subtitle {
        font-size: 16px;
        font-weight: 600;
        color: #0e7c86;
        margin: 20px 0 15px 0;
    }
    
    .radio-option {
        padding: 10px 0;
        color: #495057;
        font-size: 14px;
    }
    
    /* AI Button */
    .ai-button {
        position: fixed;
        bottom: 30px;
        right: 30px;
        background-color: #0e7c86;
        color: white;
        padding: 15px 25px;
        border-radius: 50px;
        box-shadow: 0 4px 12px rgba(14, 124, 134, 0.4);
        cursor: pointer;
        font-weight: 600;
        z-index: 1000;
        border: none;
        font-size: 16px;
    }
    
    /* AI Advisor Modal */
    .advisor-header {
        background-color: #e8f4f5;
        padding: 20px;
        border-radius: 8px 8px 0 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .advisor-icon {
        color: #0e7c86;
        font-size: 24px;
    }
    
    .advisor-title {
        font-size: 20px;
        font-weight: 600;
        color: #2c3e50;
    }
    
    .advisor-intro {
        background-color: #e8f4f5;
        padding: 20px;
        border-radius: 8px;
        margin: 20px 0;
        color: #495057;
    }
    
    /* Severity Summary */
    .severity-summary {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 15px;
        margin: 20px 0;
    }
    
    .severity-card {
        padding: 20px;
        border-radius: 8px;
        text-align: center;
    }
    
    .severity-critical {
        background-color: #fee;
        border: 1px solid #fcc;
    }
    
    .severity-high {
        background-color: #ffe8e8;
        border: 1px solid #ffcccc;
    }
    
    .severity-medium {
        background-color: #fff8e1;
        border: 1px solid #ffe082;
    }
    
    .severity-positive {
        background-color: #e8f5e9;
        border: 1px solid #a5d6a7;
    }
    
    .severity-number {
        font-size: 32px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    
    .severity-label {
        font-size: 14px;
        font-weight: 500;
    }
    
    /* Insight Cards */
    .insight-category {
        background-color: white;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
    }
    
    .insight-category-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: pointer;
    }
    
    .category-title {
        font-size: 16px;
        font-weight: 600;
        color: #2c3e50;
    }
    
    .insight-card {
        background-color: #f8f9fa;
        border-left: 4px solid #0e7c86;
        padding: 20px;
        margin: 15px 0;
        border-radius: 4px;
    }
    
    .insight-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    
    .insight-title {
        font-size: 16px;
        font-weight: 600;
        color: #2c3e50;
    }
    
    .badge {
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .badge-critical {
        background-color: #dc3545;
        color: white;
    }
    
    .badge-high {
        background-color: #fd7e14;
        color: white;
    }
    
    .badge-medium {
        background-color: #ffc107;
        color: #333;
    }
    
    .badge-low {
        background-color: #6c757d;
        color: white;
    }
    
    .badge-positive {
        background-color: #28a745;
        color: white;
    }
    
    .insight-description {
        color: #495057;
        font-size: 14px;
        margin: 10px 0;
    }
    
    .recommendation-box {
        background-color: #fff8e1;
        padding: 15px;
        border-radius: 6px;
        margin: 15px 0;
    }
    
    .recommendation-label {
        font-weight: 600;
        color: #856404;
        margin-bottom: 8px;
    }
    
    .recommendation-text {
        color: #856404;
        font-size: 14px;
    }
    
    .data-source {
        color: #6c757d;
        font-size: 12px;
        margin-top: 10px;
    }
    
    /* Category badge colors */
    .category-badge {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }
    
    .badge-utilization { background-color: #ff9800; }
    .badge-payment { background-color: #f44336; }
    .badge-history { background-color: #2196f3; }
    .badge-legal { background-color: #9c27b0; }
    .badge-positive { background-color: #4caf50; }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'show_advisor' not in st.session_state:
        st.session_state.show_advisor = False
    if 'insights_loaded' not in st.session_state:
        st.session_state.insights_loaded = False
    if 'insights_data' not in st.session_state:
        st.session_state.insights_data = None
    if 'personal_info' not in st.session_state:
        st.session_state.personal_info = {}

def load_and_process_report(xml_path: str):
    """Load and process CTOS XML report"""
    try:
        # Extract data from XML
        extracted_data = extract_data_from_xml(xml_path)
        if not extracted_data:
            return None, None
        
        # Normalize data
        normalized_data = normalize_data(extracted_data)
        
        # Store personal info
        st.session_state.personal_info = normalized_data.get('personal_info', {})
        
        # Load rules and process
        base_dir = Path(__file__).resolve().parent
        rules_file = base_dir / "rules" / "rules.json"
        
        engine = RuleEngine(str(rules_file))
        matches = engine.process_data(normalized_data)
        
        # Aggregate insights
        aggregator = ConsoleOutputAggregator()
        for match in matches:
            aggregator.add_insight(match)
        
        return aggregator, normalized_data
        
    except Exception as e:
        st.error(f"Error processing report: {str(e)}")
        return None, None

def render_gauge(score: int):
    """Render score gauge using HTML/CSS"""
    # Determine color based on score
    if score >= 750:
        color = "#4caf50"  # Green
    elif score >= 650:
        color = "#8bc34a"  # Light green
    elif score >= 550:
        color = "#ffc107"  # Yellow
    else:
        color = "#ff5722"  # Red
    
    gauge_html = f"""
    <div style="position: relative; width: 200px; height: 100px; margin: 0 auto;">
        <svg viewBox="0 0 200 100" style="width: 100%; height: 100%;">
            <defs>
                <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" style="stop-color:#ff5722;stop-opacity:1" />
                    <stop offset="50%" style="stop-color:#ffc107;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#4caf50;stop-opacity:1" />
                </linearGradient>
            </defs>
            <path d="M 20 90 A 80 80 0 0 1 180 90" fill="none" stroke="url(#gaugeGradient)" stroke-width="20" stroke-linecap="round"/>
            <line x1="100" y1="90" x2="100" y2="30" stroke="{color}" stroke-width="3" 
                  transform="rotate({-90 + (score/850)*180} 100 90)" stroke-linecap="round"/>
        </svg>
    </div>
    """
    return gauge_html

def render_ctos_score_page():
    """Render the main CTOS Score page"""
    # Get score from session state or use default
    score = st.session_state.personal_info.get('ctos_score', 696)
    name = st.session_state.personal_info.get('name', 'User')
    
    st.markdown(f"""
    <div class="score-card">
        <div class="score-header">
            Your last generated CTOS Score was {score}. Get an updated MyCTOS Score Report to know where you stand today!
        </div>
        
        {render_gauge(score)}
        
        <div class="score-number">{score}</div>
        <div class="score-label">👁️ Disclaimer</div>
        <div class="score-date">📅 Next Update: 15th November 2025</div>
        
        <button class="ctos-button">Get Your CTOS Score</button>
        <button class="ctos-button-secondary">📄 View Your Report Summary</button>
    </div>
    """, unsafe_allow_html=True)
    
    # What is Affecting My Score section
    st.markdown("""
    <div class="info-section">
        <div class="info-title">What is Affecting My Score?</div>
        <div class="radio-option">⚪ Your utilization of credit limit on revolving/charge loans is higher than average.</div>
        <div class="radio-option">⚪ The number of credit enquiries on you is high relative to other credit users.</div>
        <div class="radio-option">⚪ There is not enough recent auto loan information on your credit report.</div>
        <div class="radio-option">⚪ The age of your credit facilities is shorter than average.</div>
    </div>
    """, unsafe_allow_html=True)
    
    # How Can I Improve My Score section
    st.markdown("""
    <div class="info-section">
        <div class="info-title">How Can I Improve My Score?</div>
        <div class="radio-option">🔵 Try to avoid maxing out or utilizing close to your credit limit.</div>
        <div class="radio-option">🔵 Try to space out your loan requests or normalize your credit usage.</div>
        <div class="radio-option">🔵 Build up your credit profile with 1 year of good payment conduct.</div>
        <div class="radio-option">🔵 Maintain good payment conduct on these facilities for some time longer.</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Where do you stand section
    st.markdown("""
    <div class="info-section">
        <div class="info-title" style="color: #0e7c86;">Where do you stand?</div>
        <div class="info-subtitle">📈 Comparing to your last score</div>
        <div class="radio-option">📊 Fair</div>
        
        <div class="info-subtitle" style="margin-top: 30px;">Your CTOS Score of ranks among Malaysians</div>
        <div class="radio-option">👥 You vs. Malaysians</div>
        <div class="radio-option">👤 By Gender</div>
        <div class="radio-option">📅 Your age group</div>
    </div>
    """, unsafe_allow_html=True)

def render_severity_summary(insights_by_severity):
    """Render severity summary cards"""
    critical_count = len(insights_by_severity.get('critical', []))
    high_count = len(insights_by_severity.get('high', []))
    medium_count = len(insights_by_severity.get('medium', []))
    positive_count = len(insights_by_severity.get('positive', []))
    
    st.markdown("""
    <div style="margin: 20px 0;">
        <h3 style="color: #2c3e50; margin-bottom: 20px;">Summary by Severity</h3>
        <div class="severity-summary">
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="severity-card severity-critical">
            <div style="color: #dc3545;">⛔</div>
            <div class="severity-number" style="color: #dc3545;">{critical_count}</div>
            <div class="severity-label" style="color: #dc3545;">Critical</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="severity-card severity-high">
            <div style="color: #fd7e14;">⚠️</div>
            <div class="severity-number" style="color: #fd7e14;">{high_count}</div>
            <div class="severity-label" style="color: #fd7e14;">High</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="severity-card severity-medium">
            <div style="color: #ffc107;">⚠️</div>
            <div class="severity-number" style="color: #ffc107;">{medium_count}</div>
            <div class="severity-label" style="color: #ffc107;">Medium</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="severity-card severity-positive">
            <div style="color: #28a745;">✅</div>
            <div class="severity-number" style="color: #28a745;">{positive_count}</div>
            <div class="severity-label" style="color: #28a745;">Positive</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)

def get_category_info(category: str):
    """Get category display information"""
    category_map = {
        'Credit Utilization': ('🟠', 'badge-utilization'),
        'Moderate Utilization': ('🟠', 'badge-utilization'),
        'Payment History': ('🔴', 'badge-payment'),
        'Missed Payments': ('🔴', 'badge-payment'),
        'Credit Age': ('🔵', 'badge-history'),
        'Legal Issues': ('🟣', 'badge-legal'),
        'Positive Indicators': ('🟢', 'badge-positive')
    }
    return category_map.get(category, ('⚪', 'badge-utilization'))

def render_insight_card(insight: dict):
    """Render individual insight card"""
    severity = insight.get('severity', 'medium').lower()
    badge_class = f"badge-{severity}"
    
    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-header">
            <div class="insight-title">{insight.get('label', 'Insight')}</div>
            <span class="badge {badge_class}">{severity.title()}</span>
        </div>
        <div class="insight-description">
            {insight.get('insight', '')}
        </div>
    """, unsafe_allow_html=True)
    
    # Recommendation section
    if insight.get('recommendation'):
        st.markdown(f"""
        <div class="recommendation-box">
            <div class="recommendation-label">💡 Recommendation:</div>
            <div class="recommendation-text">{insight['recommendation']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Data source
    data_source = insight.get('data_source', 'CCRIS')
    st.markdown(f"""
        <div class="data-source">📊 Data Source: {data_source}</div>
    </div>
    """, unsafe_allow_html=True)

def render_ai_advisor():
    """Render AI Credit Advisor modal"""
    if not st.session_state.insights_loaded:
        # Initial greeting state
        st.markdown("""
        <div class="advisor-header">
            <span class="advisor-icon">🤖</span>
            <span class="advisor-title">AI Credit Advisor</span>
        </div>
        <div class="advisor-intro">
            <p>Hi there! 👋 I'm your AI Credit Advisor. I can help you understand your credit score and provide personalized recommendations.</p>
            <p style="margin-top: 15px;"><strong>Quick actions:</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("✨ How to improve my score?", use_container_width=True):
            st.session_state.insights_loaded = True
            st.rerun()
    else:
        # Show insights
        st.markdown("""
        <div class="advisor-header">
            <span class="advisor-icon">🤖</span>
            <span class="advisor-title">AI Credit Advisor</span>
        </div>
        <div class="advisor-intro">
            Based on your credit profile, here are personalized insights and recommendations to help you improve your score:
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.insights_data:
            aggregator = st.session_state.insights_data
            insights_by_severity = aggregator.get_insights_by_severity()
            insights_by_category = aggregator.get_insights_by_category()
            
            # Render severity summary
            render_severity_summary(insights_by_severity)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Render insights by category
            for category, insights in insights_by_category.items():
                if not insights:
                    continue
                
                icon, badge_class = get_category_info(category)
                
                with st.expander(f"{icon} {category} ({len(insights)})", expanded=True):
                    for insight in insights:
                        render_insight_card(insight)

def main():
    """Main application"""
    initialize_session_state()
    
    # Sidebar for file upload (hidden by default)
    with st.sidebar:
        st.title("📁 Upload CTOS Report")
        uploaded_file = st.file_uploader("Upload XML Report", type=['xml'])
        
        if uploaded_file:
            # Save uploaded file temporarily
            temp_path = Path("temp_upload.xml")
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.read())
            
            # Process the report
            with st.spinner("Processing report..."):
                aggregator, normalized_data = load_and_process_report(str(temp_path))
                
                if aggregator:
                    st.session_state.insights_data = aggregator
                    st.success("✅ Report processed successfully!")
                else:
                    st.error("❌ Failed to process report")
            
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
        
        # Use sample data button
        if st.button("📊 Use Sample Report"):
            base_dir = Path(__file__).resolve().parent
            sample_xml = base_dir / "data" / "sample_2.xml"
            
            if sample_xml.exists():
                with st.spinner("Loading sample report..."):
                    aggregator, normalized_data = load_and_process_report(str(sample_xml))
                    
                    if aggregator:
                        st.session_state.insights_data = aggregator
                        st.success("✅ Sample report loaded!")
                    else:
                        st.error("❌ Failed to load sample report")
            else:
                st.error("Sample report not found")
    
    # Main content area
    if not st.session_state.show_advisor:
        # Show CTOS Score page
        render_ctos_score_page()
        
        # Floating AI button
        if st.button("🤖 Ask AI", key="ask_ai_btn"):
            st.session_state.show_advisor = True
            st.rerun()
        
    else:
        # Show AI Advisor
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col2:
            # Back button
            if st.button("← Back to CTOS Score"):
                st.session_state.show_advisor = False
                st.session_state.insights_loaded = False
                st.rerun()
            
            render_ai_advisor()

if __name__ == "__main__":
    main()