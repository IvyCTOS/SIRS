"""
Streamlit Frontend for CTOS Credit Behavior Insight Engine
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import sys
import time

# Import your existing backend modules
try:
    from engine.credit_rule_engine import RuleEngine
    from engine.data_input import extract_data_from_xml, normalize_data
    from engine.output_aggregator import ConsoleOutputAggregator
except ImportError:
    st.error("⚠️ Backend modules not found. Please ensure engine package is available.")

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
    
    /* Main container styling */
    .main {
        background-color: #e8f4f5;
        padding: 0;
    }
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
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
    
    .score-number {
        font-size: 72px;
        font-weight: bold;
        color: #2c3e50;
        margin: 20px 0;
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
    
    /* Severity Summary */
    .severity-grid {
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
        margin: 10px 0;
    }
    
    .severity-label {
        font-size: 14px;
        font-weight: 500;
    }
    
    /* Insight Cards */
    .insight-card {
        background-color: #f8f9fa;
        border-left: 4px solid #0e7c86;
        padding: 20px;
        margin: 15px 0;
        border-radius: 4px;
    }
    
    .insight-title {
        font-size: 16px;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 10px;
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
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 6px;
        padding: 12px 24px;
        font-weight: 500;
    }
    
    div[data-testid="stButton"] {
        margin-bottom: 10px;
    }
    
    /* Progress indicator */
    .progress-step {
        background: white;
        padding: 15px 20px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #0e7c86;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .progress-icon {
        font-size: 20px;
    }
    
    .progress-text {
        color: #2c3e50;
        font-size: 14px;
    }
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
    if 'xml_path' not in st.session_state:
        st.session_state.xml_path = None
    if 'processing' not in st.session_state:
        st.session_state.processing = False

def load_xml_file(xml_path: str):
    """Load XML file and extract basic info for display"""
    try:
        # Just extract basic data for the score page
        extracted_data = extract_data_from_xml(xml_path)
        if not extracted_data:
            return False
        
        # Store basic personal info and XML path
        st.session_state.personal_info = {
            'name': extracted_data.get('name', 'User'),
            'ic_number': extracted_data.get('ic_number', 'N/A'),
            'ctos_score': extracted_data.get('ctos_score', 696),
        }
        st.session_state.xml_path = xml_path
        
        return True
        
    except Exception as e:
        st.error(f"Error loading XML: {str(e)}")
        return False

def process_report_with_engine(xml_path: str):
    """Process CTOS XML report with rule engine"""
    try:
        # Progress indicator placeholder
        progress_container = st.container()
        
        with progress_container:
            st.info("🔄 **Processing Your Credit Report...**")
            
            # Step 1: Extract data
            with st.spinner("📄 Extracting data from XML report..."):
                time.sleep(0.5)
                extracted_data = extract_data_from_xml(xml_path)
                if not extracted_data:
                    st.error("❌ Failed to extract data from XML")
                    return None
            
            st.success("✅ Data extracted successfully")
            
            # Step 2: Normalize data
            with st.spinner("🔄 Normalizing data structure..."):
                time.sleep(0.5)
                normalized_data = normalize_data(extracted_data)
            
            st.success("✅ Data normalized successfully")
            
            # Step 3: Load rules
            with st.spinner("📋 Loading credit analysis rules..."):
                time.sleep(0.5)
                base_dir = Path(__file__).resolve().parent
                rules_file = base_dir / "rules" / "rules.json"
                
                if not rules_file.exists():
                    st.error(f"❌ Rules file not found: {rules_file}")
                    return None
                
                engine = RuleEngine(str(rules_file))
            
            st.success(f"✅ Loaded {len(engine.rules)} analysis rules")
            
            # Step 4: Process rules
            with st.spinner("🎯 Evaluating credit behavior patterns..."):
                time.sleep(1.0)
                matches = engine.process_data(normalized_data)
            
            # Step 5: Aggregate insights
            with st.spinner("📊 Generating personalized insights..."):
                time.sleep(0.5)
                aggregator = ConsoleOutputAggregator()
                for match in matches:
                    aggregator.add_insight(match)
            
            st.success(f"✅ Found {len(matches)} insights and recommendations")
            time.sleep(0.5)
            
        return aggregator
        
    except Exception as e:
        st.error(f"❌ Error processing report: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None

def render_gauge_svg(score: int):
    """Render score gauge using SVG"""
    # Determine color based on score
    if score >= 750:
        needle_color = "#4caf50"
    elif score >= 650:
        needle_color = "#8bc34a"
    elif score >= 550:
        needle_color = "#ffc107"
    else:
        needle_color = "#ff5722"
    
    # Calculate rotation angle (-90 to 90 degrees)
    rotation = -90 + (score / 850) * 180
    
    svg = f'''
    <svg viewBox="0 0 200 120" style="width: 200px; height: 120px; margin: 20px auto; display: block;">
        <defs>
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" style="stop-color:#ff5722;stop-opacity:1" />
                <stop offset="50%" style="stop-color:#ffc107;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#4caf50;stop-opacity:1" />
            </linearGradient>
        </defs>
        <path d="M 20 90 A 80 80 0 0 1 180 90" fill="none" stroke="url(#gaugeGradient)" stroke-width="20" stroke-linecap="round"/>
        <line x1="100" y1="90" x2="100" y2="30" stroke="{needle_color}" stroke-width="3" 
              transform="rotate({rotation} 100 90)" stroke-linecap="round"/>
        <circle cx="100" cy="90" r="5" fill="{needle_color}"/>
    </svg>
    '''
    return svg

def render_ctos_score_page():
    """Render the main CTOS Score page"""
    # Get score from session state or use default
    score = st.session_state.personal_info.get('ctos_score', 696)
    
    # Score Card with gauge
    st.markdown(f"""
    <div class="score-card">
        <div class="score-header">
            Your last generated CTOS Score was {score}. Get an updated MyCTOS Score Report to know where you stand today!
        </div>
        {render_gauge_svg(score)}
    </div>
    """, unsafe_allow_html=True)
    
    # Display score using Streamlit native components
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown(f"<h1 style='text-align: center; font-size: 72px; margin: 0;'>{score}</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #7f8c8d;'>👁️ Disclaimer</p>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #95a5a6; font-size: 12px;'>📅 Next Update: 15th November 2025</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.button("🔒 Get Your CTOS Score", type="primary", use_container_width=True, disabled=True)
        st.button("📄 View Your Report Summary", use_container_width=True, disabled=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
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

def organize_insights_by_severity(aggregator):
    """Organize insights by severity level"""
    insights_by_severity = {
        'critical': [],
        'high': [],
        'medium': [],
        'low': [],
        'positive': []
    }
    
    # Check if aggregator has insights attribute
    if hasattr(aggregator, 'insights'):
        insights = aggregator.insights
    elif hasattr(aggregator, 'get_all_insights'):
        insights = aggregator.get_all_insights()
    else:
        # Try to get insights from the object directly
        insights = getattr(aggregator, '_insights', [])
    
    for insight in insights:
        severity = insight.get('severity', 'medium').lower()
        if severity in insights_by_severity:
            insights_by_severity[severity].append(insight)
    
    return insights_by_severity

def organize_insights_by_category(aggregator):
    """Organize insights by category"""
    insights_by_category = {}
    
    # Check if aggregator has insights attribute
    if hasattr(aggregator, 'insights'):
        insights = aggregator.insights
    elif hasattr(aggregator, 'get_all_insights'):
        insights = aggregator.get_all_insights()
    else:
        # Try to get insights from the object directly
        insights = getattr(aggregator, '_insights', [])
    
    for insight in insights:
        category = insight.get('category', 'Other')
        if category not in insights_by_category:
            insights_by_category[category] = []
        insights_by_category[category].append(insight)
    
    return insights_by_category

def render_severity_summary(insights_by_severity):
    """Render severity summary cards"""
    critical_count = len(insights_by_severity.get('critical', []))
    high_count = len(insights_by_severity.get('high', []))
    medium_count = len(insights_by_severity.get('medium', []))
    positive_count = len(insights_by_severity.get('positive', []))
    
    st.markdown("### Summary by Severity")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="⛔ Critical", value=critical_count)
    
    with col2:
        st.metric(label="⚠️ High", value=high_count)
    
    with col3:
        st.metric(label="⚠️ Medium", value=medium_count)
    
    with col4:
        st.metric(label="✅ Positive", value=positive_count)

def get_severity_badge(severity: str):
    """Get colored badge for severity"""
    colors = {
        'critical': '#dc3545',
        'high': '#fd7e14',
        'medium': '#ffc107',
        'low': '#6c757d',
        'positive': '#28a745'
    }
    color = colors.get(severity.lower(), '#6c757d')
    return f'<span style="background-color: {color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">{severity.title()}</span>'

def render_insight_card(insight: dict):
    """Render individual insight card using Streamlit native components"""
    severity = insight.get('severity', 'medium').lower()
    label = insight.get('label', 'Insight')
    insight_text = insight.get('insight', '')
    recommendation = insight.get('recommendation', '')
    data_source = insight.get('data_source', 'CCRIS')
    
    # Create a container with custom styling
    with st.container():
        # Create columns for title and badge
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.subheader(label)
        
        with col2:
            # Color-coded badge
            colors = {
                'critical': '🔴',
                'high': '🔴',
                'medium': '🟡',
                'low': '⚪',
                'positive': '🟢'
            }
            badge_text = {
                'critical': 'Critical',
                'high': 'High',
                'medium': 'Medium',
                'low': 'Low',
                'positive': 'Positive'
            }
            icon = colors.get(severity, '⚪')
            text = badge_text.get(severity, severity.title())
            st.markdown(f"### {icon} {text}")
        
        # Description - use st.write to ensure it displays
        if insight_text:
            st.write(insight_text)
        
        # Recommendation section
        if recommendation:
            st.info(f"💡 **Recommendation:** {recommendation}")
        
        # Data source
        st.caption(f"📊 Data Source: {data_source}")
        
        # Add spacing
        st.divider()

def render_ai_advisor():
    """Render AI Credit Advisor modal"""
    if not st.session_state.insights_loaded:
        # Initial greeting state
        st.info("🤖 **AI Credit Advisor**")
        st.write("Hi there! 👋 I'm your AI Credit Advisor. I can help you understand your credit score and provide personalized recommendations.")
        st.write("**Quick actions:**")
        
        # Check if XML is loaded
        if not st.session_state.xml_path:
            st.warning("⚠️ Please load a CTOS report first using the sidebar.")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.button("✨ How to improve my score?", type="primary", use_container_width=True, disabled=True)
        else:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("✨ How to improve my score?", type="primary", use_container_width=True):
                    st.session_state.processing = True
                    st.rerun()
            
            # Process if button was clicked
            if st.session_state.processing:
                aggregator = process_report_with_engine(st.session_state.xml_path)
                
                if aggregator:
                    st.session_state.insights_data = aggregator
                    st.session_state.insights_loaded = True
                    st.session_state.processing = False
                    
                    st.success("✅ Analysis complete! Loading your personalized insights...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.session_state.processing = False
                    st.error("❌ Failed to process report. Please try again.")
    else:
        # Show insights
        st.info("🤖 **AI Credit Advisor**")
        st.write("Based on your credit profile, here are personalized insights and recommendations to help you improve your score:")
        
        st.markdown("---")
        
        if st.session_state.insights_data:
            aggregator = st.session_state.insights_data
            
            # Organize insights
            insights_by_severity = organize_insights_by_severity(aggregator)
            insights_by_category = organize_insights_by_category(aggregator)
            
            # Render severity summary
            render_severity_summary(insights_by_severity)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Render insights by category
            category_icons = {
                'Credit Utilization': '🟠',
                'Moderate Utilization': '🟠',
                'Payment History': '🔴',
                'Missed Payments': '🔴',
                'Credit Age': '🔵',
                'Legal Issues': '🟣',
                'Positive Indicators': '🟢'
            }
            
            for category, insights in insights_by_category.items():
                if not insights:
                    continue
                
                icon = category_icons.get(category, '⚪')
                
                with st.expander(f"{icon} {category} ({len(insights)})", expanded=True):
                    for insight in insights:
                        render_insight_card(insight)

def main():
    """Main application"""
    initialize_session_state()
    
    # Sidebar for file upload
    with st.sidebar:
        st.title("📁 Upload CTOS Report")
        st.markdown("---")
        
        uploaded_file = st.file_uploader("Upload XML Report", type=['xml'])
        
        if uploaded_file:
            # Save uploaded file temporarily
            temp_path = Path("temp_upload.xml")
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.read())
            
            # Load the XML file (just basic info)
            with st.spinner("Loading report..."):
                if load_xml_file(str(temp_path)):
                    st.success("✅ Report loaded successfully!")
                    st.info("💡 Click 'Ask AI' to get personalized insights")
                else:
                    st.error("❌ Failed to load report")
            
            # Keep temp file for later processing
            if not st.session_state.xml_path:
                st.session_state.xml_path = str(temp_path)
        
        st.markdown("---")
        
        # Use sample data button
        if st.button("📊 Use Sample Report", use_container_width=True):
            base_dir = Path(__file__).resolve().parent
            sample_xml = base_dir / "data" / "sample_2.xml"
            
            if sample_xml.exists():
                with st.spinner("Loading sample report..."):
                    if load_xml_file(str(sample_xml)):
                        st.success("✅ Sample report loaded!")
                        st.info("💡 Click 'Ask AI' to get personalized insights")
                    else:
                        st.error("❌ Failed to load sample report")
            else:
                st.warning("⚠️ Sample report not found at data/sample_2.xml")
        
        # Info
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("CTOS Credit Behavior Insight Engine")
        st.markdown("Powered by AI")
        
        if st.session_state.xml_path:
            st.markdown("---")
            st.markdown("### 📊 Status")
            st.success("✅ Report loaded")
            if st.session_state.insights_loaded:
                st.success("✅ Insights generated")
    
    # Main content area
    if not st.session_state.show_advisor:
        # Show CTOS Score page
        render_ctos_score_page()
        
        # Floating AI button at bottom
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([3, 1, 3])
        with col2:
            if st.button("🤖 Ask AI", type="primary", use_container_width=True):
                st.session_state.show_advisor = True
                st.rerun()
        
    else:
        # Show AI Advisor
        # Back button at top
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("← Back", use_container_width=True):
                st.session_state.show_advisor = False
                st.rerun()
        
        render_ai_advisor()

if __name__ == "__main__":
    main()