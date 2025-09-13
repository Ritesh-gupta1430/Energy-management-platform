import streamlit as st
import plotly.graph_objects as go
from typing import Optional, Dict, Any, List
from .theme import COLORS, TYPOGRAPHY, SPACING, get_professional_css, CHART_COLORS

def apply_professional_theme():
    st.markdown(get_professional_css(), unsafe_allow_html=True)

def professional_header(title: str, subtitle: Optional[str] = None, icon: Optional[str] = None):
    header_html = f"""
    <div class="main-content" style="margin-bottom: {SPACING['lg']};">
        <h1 style="
            color: {COLORS['dark_gray']};
            font-family: {TYPOGRAPHY['font_family']};
            font-weight: {TYPOGRAPHY['weights']['bold']};
            font-size: {TYPOGRAPHY['sizes']['3xl']};
            margin-bottom: {SPACING['sm']};
            line-height: 1.2;
        ">
            {icon + ' ' if icon else ''}{title}
        </h1>
        {f'''<p style="
            color: {COLORS['medium_gray']};
            font-family: {TYPOGRAPHY['font_family']};
            font-size: {TYPOGRAPHY['sizes']['lg']};
            margin: 0;
            font-weight: {TYPOGRAPHY['weights']['normal']};
        ">{subtitle}</p>''' if subtitle else ''}
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

def professional_subheader(title: str, description: Optional[str] = None):
    subheader_html = f"""
    <div style="
        margin: {SPACING['xl']} 0 {SPACING['lg']} 0;
        padding-bottom: {SPACING['sm']};
        border-bottom: 2px solid {COLORS['primary']};
    ">
        <h2 style="
            color: {COLORS['dark_gray']};
            font-family: {TYPOGRAPHY['font_family']};
            font-weight: {TYPOGRAPHY['weights']['semibold']};
            font-size: {TYPOGRAPHY['sizes']['2xl']};
            margin: 0 0 {SPACING['xs']} 0;
        ">{title}</h2>
        {f'''<p style="
            color: {COLORS['medium_gray']};
            font-family: {TYPOGRAPHY['font_family']};
            font-size: {TYPOGRAPHY['sizes']['base']};
            margin: 0;
        ">{description}</p>''' if description else ''}
    </div>
    """
    st.markdown(subheader_html, unsafe_allow_html=True)

def status_pill(status: str, label: str) -> str:
    """
    Create a professional status pill

    Args:
        status: Status type ('online', 'offline', 'warning', 'info')
        label: Text to display in pill

    Returns:
        HTML string for status pill
    """
    status_class = f"status-{status.lower()}"
    
    return f"""
    <span class="status-pill {status_class}" style="
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: {TYPOGRAPHY['sizes']['sm']};
        font-weight: {TYPOGRAPHY['weights']['medium']};
        text-align: center;
    ">{label}</span>
    """

def professional_metric_card(
    title: str, 
    value: str, 
    delta: Optional[str] = None,
    delta_color: str = "normal",
    help_text: Optional[str] = None
):
    """
    Create a professional metric card with enhanced styling
    
    Args:
        title: Metric title
        value: Metric value
        delta: Optional delta value
        delta_color: Delta color ('normal', 'positive', 'negative')
        help_text: Optional help text
    """
    # Use Streamlit's metric but with professional styling
    st.metric(
        label=title,
        value=value,
        delta=delta,
        help=help_text
    )

def professional_navigation(pages: List[Dict[str, str]], current_page: str) -> str:
    """
    Create professional navigation sidebar
    
    Args:
        pages: List of page dictionaries with 'name' and 'label' keys
        current_page: Currently selected page name
    
    Returns:
        Selected page name
    """
    # Create clean navigation without emojis
    st.sidebar.markdown(f"""
    <div style="
        background-color: {COLORS['white']};
        padding: {SPACING['lg']};
        border-radius: 8px;
        margin-bottom: {SPACING['lg']};
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    ">
        <h3 style="
            color: {COLORS['dark_gray']};
            font-family: {TYPOGRAPHY['font_family']};
            font-weight: {TYPOGRAPHY['weights']['semibold']};
            font-size: {TYPOGRAPHY['sizes']['lg']};
            margin-bottom: {SPACING['md']};
        ">Navigation</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Create radio buttons with page labels
    page_labels = [page['label'] for page in pages]
    selected_label = st.sidebar.radio(
        "Navigate to:",
        options=page_labels,
        index=page_labels.index(next(page['label'] for page in pages if page['name'] == current_page)),
        label_visibility="collapsed"
    )
    
    # Return the page name corresponding to selected label
    return next(page['name'] for page in pages if page['label'] == selected_label)

def professional_info_box(message: str, box_type: str = "info"):
    """
    Create a professional information box
    
    Args:
        message: Message to display
        box_type: Type of box ('info', 'success', 'warning', 'error')
    """
    colors = {
        'info': COLORS['info'],
        'success': COLORS['success'],
        'warning': COLORS['warning'],
        'error': COLORS['danger']
    }
    
    bg_colors = {
        'info': f"{COLORS['info']}15",
        'success': f"{COLORS['success']}15",
        'warning': f"{COLORS['warning']}15",
        'error': f"{COLORS['danger']}15"
    }
    
    info_html = f"""
    <div style="
        background-color: {bg_colors.get(box_type, bg_colors['info'])};
        border-left: 4px solid {colors.get(box_type, colors['info'])};
        padding: {SPACING['md']};
        border-radius: 6px;
        margin: {SPACING['md']} 0;
    ">
        <p style="
            color: {COLORS['dark_gray']};
            font-family: {TYPOGRAPHY['font_family']};
            font-size: {TYPOGRAPHY['sizes']['base']};
            margin: 0;
            line-height: 1.5;
        ">{message}</p>
    </div>
    """
    st.markdown(info_html, unsafe_allow_html=True)

def create_professional_chart(
    figure: go.Figure,
    title: Optional[str] = None,
    height: int = 400
) -> go.Figure:
    """
    Apply professional styling to Plotly charts
    
    Args:
        figure: Plotly figure object
        title: Optional chart title
        height: Chart height in pixels
    
    Returns:
        Styled Plotly figure
    """
    figure.update_layout(
        title={
            'text': title,
            'font': {
                'family': TYPOGRAPHY['font_family'],
                'size': 20,
                'color': COLORS['dark_gray']
            },
            'x': 0.02,
            'xanchor': 'left'
        },
        font={
            'family': TYPOGRAPHY['font_family'],
            'color': COLORS['dark_gray']
        },
        plot_bgcolor=COLORS['white'],
        paper_bgcolor=COLORS['white'],
        height=height,
        margin=dict(l=40, r=40, t=60, b=40),
        showlegend=True,
        legend=dict(
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor=COLORS['border_light'],
            borderwidth=1
        ),
        colorway=CHART_COLORS
    )
    
    # Style axes
    figure.update_xaxes(
        gridcolor=COLORS['border_light'],
        showgrid=True,
        linecolor=COLORS['border_medium'],
        title_font={'color': COLORS['medium_gray']}
    )
    
    figure.update_yaxes(
        gridcolor=COLORS['border_light'],
        showgrid=True,
        linecolor=COLORS['border_medium'],
        title_font={'color': COLORS['medium_gray']}
    )
    
    return figure

def professional_data_table(df, title: Optional[str] = None):
    """
    Display a professional data table
    
    Args:
        df: Pandas DataFrame
        title: Optional table title
    """
    if title:
        professional_subheader(title)
    
    # Style the dataframe
    styled_df = df.style.set_table_styles([
        {'selector': 'thead th', 'props': [
            ('background-color', COLORS['light_gray']),
            ('color', COLORS['dark_gray']),
            ('font-weight', TYPOGRAPHY['weights']['semibold']),
            ('border-bottom', f"2px solid {COLORS['primary']}")
        ]},
        {'selector': 'tbody td', 'props': [
            ('color', COLORS['dark_gray']),
            ('border-bottom', f"1px solid {COLORS['border_light']}")
        ]},
        {'selector': 'tbody tr:hover', 'props': [
            ('background-color', COLORS['primary_light'])
        ]}
    ])
    
    st.dataframe(styled_df, width="stretch")