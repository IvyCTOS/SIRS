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
    
    # Check different possible data structures
    if hasattr(aggregator, 'insights'):
        insights = aggregator.insights
    elif hasattr(aggregator, 'get_all_insights'):
        insights = aggregator.get_all_insights()
    elif hasattr(aggregator, 'insights_by_label'):
        # If it's organized by label, flatten it
        insights = []
        for label, insight_list in aggregator.insights_by_label.items():
            insights.extend(insight_list)
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
    
    # Check if aggregator has insights_by_label (which is the category structure)
    if hasattr(aggregator, 'insights_by_label'):
        # Already organized by label/category
        insights_by_label = aggregator.insights_by_label
        for label, insight_list in insights_by_label.items():
            # Clean up the label (remove emoji prefix if needed for grouping)
            category = label
            insights_by_category[category] = insight_list
        return insights_by_category
    
    # Otherwise, try to organize from a flat list
    if hasattr(aggregator, 'insights'):
        insights = aggregator.insights
    elif hasattr(aggregator, 'get_all_insights'):
        insights = aggregator.get_all_insights()
    else:
        insights = getattr(aggregator, '_insights', [])
    
    for insight in insights:
        # Try different possible category field names
        category = insight.get('category', insight.get('label', insight.get('type', 'Other')))
        if category not in insights_by_category:
            insights_by_category[category] = []
        insights_by_category[category].append(insight)
    
    return insights_by_category

def render_severity_summary(insights_by_severity):
    """Render severity summary cards with modern design"""
    critical_count = len(insights_by_severity.get('critical', []))
    high_count = len(insights_by_severity.get('high', []))
    medium_count = len(insights_by_severity.get('medium', []))
    positive_count = len(insights_by_severity.get('positive', []))
    
    st.markdown("### Summary by Severity")
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); 
                    padding: 25px; border-radius: 16px; text-align: center; 
                    box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);">
            <div style="font-size: 28px; margin-bottom: 8px;">⛔</div>
            <div style="font-size: 36px; font-weight: bold; color: white; margin: 10px 0;">{critical_count}</div>
            <div style="font-size: 14px; font-weight: 600; color: rgba(255,255,255,0.9);">Critical</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fd7e14 0%, #e8590c 100%); 
                    padding: 25px; border-radius: 16px; text-align: center; 
                    box-shadow: 0 4px 12px rgba(253, 126, 20, 0.3);">
            <div style="font-size: 28px; margin-bottom: 8px;">⚠️</div>
            <div style="font-size: 36px; font-weight: bold; color: white; margin: 10px 0;">{high_count}</div>
            <div style="font-size: 14px; font-weight: 600; color: rgba(255,255,255,0.9);">High</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #ffc107 0%, #e0a800 100%); 
                    padding: 25px; border-radius: 16px; text-align: center; 
                    box-shadow: 0 4px 12px rgba(255, 193, 7, 0.3);">
            <div style="font-size: 28px; margin-bottom: 8px;">⚠️</div>
            <div style="font-size: 36px; font-weight: bold; color: white; margin: 10px 0;">{medium_count}</div>
            <div style="font-size: 14px; font-weight: 600; color: rgba(255,255,255,0.9);">Medium</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #28a745 0%, #218838 100%); 
                    padding: 25px; border-radius: 16px; text-align: center; 
                    box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);">
            <div style="font-size: 28px; margin-bottom: 8px;">✅</div>
            <div style="font-size: 36px; font-weight: bold; color: white; margin: 10px 0;">{positive_count}</div>
            <div style="font-size: 14px; font-weight: 600; color: rgba(255,255,255,0.9);">Positive</div>
        </div>
        """, unsafe_allow_html=True)

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
    """Render individual insight card with modern design"""
    severity = insight.get('severity', 'medium').lower()
    
    # Get the correct field names from your JSON structure
    label = insight.get('type', insight.get('label', 'Insight'))
    insight_text = insight.get('message', insight.get('insight', ''))
    recommendation = insight.get('recommendation', '')
    data_source = insight.get('data_source', 'CCRIS')
    
    # Define severity styling
    severity_styles = {
        'critical': {
            'bg_gradient': 'linear-gradient(135deg, rgba(220, 53, 69, 0.15) 0%, rgba(200, 35, 51, 0.1) 100%)',
            'border': '#dc3545',
            'icon': '🔴',
            'badge_bg': '#dc3545',
            'badge_text': 'Critical'
        },
        'high': {
            'bg_gradient': 'linear-gradient(135deg, rgba(253, 126, 20, 0.15) 0%, rgba(232, 89, 12, 0.1) 100%)',
            'border': '#fd7e14',
            'icon': '🟠',
            'badge_bg': '#fd7e14',
            'badge_text': 'High'
        },
        'medium': {
            'bg_gradient': 'linear-gradient(135deg, rgba(255, 193, 7, 0.15) 0%, rgba(224, 168, 0, 0.1) 100%)',
            'border': '#ffc107',
            'icon': '🟡',
            'badge_bg': '#ffc107',
            'badge_text': 'Medium'
        },
        'low': {
            'bg_gradient': 'linear-gradient(135deg, rgba(108, 117, 125, 0.15) 0%, rgba(73, 80, 87, 0.1) 100%)',
            'border': '#6c757d',
            'icon': '⚪',
            'badge_bg': '#6c757d',
            'badge_text': 'Low'
        },
        'positive': {
            'bg_gradient': 'linear-gradient(135deg, rgba(40, 167, 69, 0.15) 0%, rgba(33, 136, 56, 0.1) 100%)',
            'border': '#28a745',
            'icon': '🟢',
            'badge_bg': '#28a745',
            'badge_text': 'Positive'
        }
    }
    
    style = severity_styles.get(severity, severity_styles['medium'])
    
    # Render card with modern styling
    st.markdown(f"""
    <div style="background: {style['bg_gradient']}; 
                border-left: 4px solid {style['border']}; 
                border-radius: 12px; 
                padding: 20px; 
                margin: 16px 0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 24px;">{style['icon']}</span>
                <span style="font-size: 18px; font-weight: 600; color: #2c3e50;">{label}</span>
            </div>
            <span style="background: {style['badge_bg']}; 
                         color: white; 
                         padding: 4px 12px; 
                         border-radius: 20px; 
                         font-size: 12px; 
                         font-weight: 600;">
                {style['badge_text']}
            </span>
        </div>
        <div style="color: #495057; font-size: 15px; line-height: 1.6; margin: 12px 0;">
            {insight_text}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Recommendation box
    if recommendation:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(255, 248, 225, 0.5) 0%, rgba(255, 236, 179, 0.3) 100%); 
                    border-left: 4px solid #856404;
                    border-radius: 12px; 
                    padding: 16px; 
                    margin: 12px 0 16px 0;">
            <div style="display: flex; align-items: start; gap: 10px;">
                <span style="font-size: 20px; margin-top: 2px;">💡</span>
                <div>
                    <div style="font-weight: 600; color: #856404; margin-bottom: 6px;">Recommendation:</div>
                    <div style="color: #856404; font-size: 14px; line-height: 1.5;">{recommendation}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Data source
    st.markdown(f"""
    <div style="color: #6c757d; font-size: 12px; margin-top: 8px; margin-bottom: 20px;">
        📊 Data Source: {data_source}
    </div>
    """, unsafe_allow_html=True)

def render_ai_advisor_content():
    """Render AI Credit Advisor content (for modal)"""
    if not st.session_state.insights_loaded:
        # Initial greeting state with improved design
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(14, 124, 134, 0.2) 0%, rgba(10, 95, 104, 0.1) 100%); 
                    border-radius: 16px; 
                    padding: 30px; 
                    margin: 20px 0;
                    border-left: 4px solid #0e7c86;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <div style="display: flex; align-items: start; gap: 15px;">
                <span style="font-size: 32px;">👋</span>
                <div>
                    <h3 style="color: white; margin: 0 0 10px 0;">Hi there!</h3>
                    <p style="color: rgba(255, 255, 255, 0.9); line-height: 1.6; margin: 0;">
                        I'm your AI Credit Advisor. I can help you understand your credit score and provide personalized recommendations to improve your financial health.
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Check if XML is loaded
        if not st.session_state.xml_path:
            st.warning("⚠️ Please load a CTOS report first using the sidebar.", icon="⚠️")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.button("✨ How to improve my score?", type="primary", use_container_width=True, disabled=True)
        else:
            st.markdown("""
            <div style="text-align: center; margin: 30px 0;">
                <p style="color: rgba(255, 255, 255, 0.8); font-size: 16px; font-weight: 600; margin-bottom: 20px;">
                    Quick actions:
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                # Custom styled button
                st.markdown("""
                <style>
                button[key="improve_score_btn"] {
                    background: linear-gradient(135deg, #0e7c86 0%, #0a5f68 100%) !important;
                    color: white !important;
                    padding: 16px 32px !important;
                    border-radius: 12px !important;
                    font-size: 16px !important;
                    font-weight: 600 !important;
                    border: none !important;
                    box-shadow: 0 6px 20px rgba(14, 124, 134, 0.4) !important;
                    transition: all 0.3s ease !important;
                }
                button[key="improve_score_btn"]:hover {
                    transform: translateY(-2px) !important;
                    box-shadow: 0 8px 25px rgba(14, 124, 134, 0.6) !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                if st.button("✨ How to improve my score?", type="primary", use_container_width=True, key="improve_score_btn"):
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
        # Show insights header
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(14, 124, 134, 0.2) 0%, rgba(10, 95, 104, 0.1) 100%); 
                    border-radius: 16px; 
                    padding: 20px; 
                    margin: 20px 0;
                    border-left: 4px solid #0e7c86;">
            <p style="color: rgba(255, 255, 255, 0.9); font-size: 16px; margin: 0; line-height: 1.6;">
                Based on your credit profile, here are personalized insights and recommendations to help you improve your score:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.session_state.insights_data:
            aggregator = st.session_state.insights_data
            
            # Organize insights
            insights_by_severity = organize_insights_by_severity(aggregator)
            insights_by_category = organize_insights_by_category(aggregator)
            
            # Render severity summary
            render_severity_summary(insights_by_severity)
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            
            # Render insights by category with improved styling
            st.markdown("""
            <style>
            /* Style the expanders */
            .streamlit-expanderHeader {
                background: linear-gradient(135deg, rgba(14, 124, 134, 0.1) 0%, rgba(10, 95, 104, 0.05) 100%);
                border-radius: 10px;
                padding: 12px 16px;
                font-weight: 600;
                font-size: 16px;
                border-left: 4px solid #0e7c86;
            }
            
            .streamlit-expanderHeader:hover {
                background: linear-gradient(135deg, rgba(14, 124, 134, 0.15) 0%, rgba(10, 95, 104, 0.1) 100%);
            }
            
            /* Add spacing between expanders */
            .streamlit-expander {
                margin-bottom: 16px;
                border: none;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                border-radius: 10px;
            }
            </style>
            """, unsafe_allow_html=True)
            
            category_icons = {
                '🟠 Moderate Utilization': '🟠',
                '🔴 Serious Delinquency': '🔴',
                '⚠️ Worsening Payment Pattern': '⚠️',
                '🟠 Missed Payments': '🟠',
                '🟢 Low Utilization': '🟢',
                '🟢 Long Credit History': '🟢',
                '🟢 Low Application Rate': '🟢',
                '🟢 Diverse Credit Mix': '🟢',
                '🟢 Clean Legal Record': '🟢',
                '🟢 Positive Pattern': '🟢',
                'ℹ️ Fair CTOS Score': 'ℹ️',
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
                
                # Use category name directly since it already has emoji
                display_name = category
                
                with st.expander(f"{display_name} ({len(insights)})", expanded=True):
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
    
    # Always show main page
    if not st.session_state.show_advisor:
        render_ctos_score_page()
        
        # Add spacing
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Style the Ask AI button with green theme  
        st.markdown("""
        <style>
        /* Style the Ask AI button with CTOS green - target primary buttons */
        button[kind="primary"] {
            background-color: #0e7c86 !important;
            color: white !important;
            border: none !important;
            padding: 12px 20px !important;
            border-radius: 50px !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            box-shadow: 0 4px 12px rgba(14, 124, 134, 0.4) !important;
            transition: all 0.3s ease !important;
        }
        button[kind="primary"]:hover {
            background-color: #0a5f68 !important;
            box-shadow: 0 6px 16px rgba(14, 124, 134, 0.6) !important;
            transform: translateY(-2px) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Position button at bottom right using columns
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("🤖 Ask AI", key="ask_ai_button", type="primary", use_container_width=True):
                st.session_state.show_advisor = True
                st.rerun()
    else:
        # Show modal-style overlay with improved styling
        st.markdown("""
        <style>
        /* Modal styling */
        .stApp > header {
            background-color: transparent !important;
        }
        
        .main .block-container {
            max-width: 1400px;
            padding-top: 2rem;
            animation: fadeIn 0.3s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Gradient background for modal */
        .main {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        }
        
        /* Style close button */
        div[data-testid="stButton"] button[key="close_advisor"] {
            background-color: #dc3545;
            color: white;
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        div[data-testid="stButton"] button[key="close_advisor"]:hover {
            background-color: #c82333;
            transform: scale(1.05);
        }
        
        /* Improve scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: rgba(14, 124, 134, 0.6);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(14, 124, 134, 0.8);
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header with close button
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown("""
            <h1 style="color: white; display: flex; align-items: center; gap: 15px; margin-bottom: 10px;">
                <span style="font-size: 36px;">🤖</span>
                <span>AI Credit Advisor</span>
            </h1>
            <p style="color: rgba(255, 255, 255, 0.7); margin-bottom: 20px;">
                Personalized insights to help improve your credit score
            </p>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("✕ Close", key="close_advisor", use_container_width=True):
                st.session_state.show_advisor = False
                st.session_state.insights_loaded = False
                st.rerun()
        
        st.markdown("---")
        
        # Render advisor content
        render_ai_advisor_content()

if __name__ == "__main__":
    main()