COLORS = {
    # Primary colors
    'primary': '#1f77b4',
    'primary_dark': '#1a629c',
    'primary_light': '#e3f2fd',

    # Secondary colors
    'secondary': '#6c757d',
    'secondary_light': '#f8f9fa',

    # Status colors
    'success': '#28a745',
    'warning': '#ffc107',
    'danger': '#dc3545',
    'info': '#17a2b8',

    # Neutral colors
    'white': '#ffffff',
    'light_gray': '#f8f9fa',
    'medium_gray': '#6c757d',
    'dark_gray': '#343a40',
    'black': '#000000',

    # Border colors
    'border_light': '#e9ecef',
    'border_medium': '#dee2e6',
    'border_dark': '#ced4da',
}

# Typography Settings
TYPOGRAPHY = {
    'font_family': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    'sizes': {
        'xs': '0.75rem',
        'sm': '0.875rem',
        'base': '1rem',
        'lg': '1.125rem',
        'xl': '1.25rem',
        '2xl': '1.5rem',
        '3xl': '1.875rem',
        '4xl': '2.25rem',
    },
    'weights': {
        'light': '300',
        'normal': '400',
        'medium': '500',
        'semibold': '600',
        'bold': '700',
    }
}

# Spacing Constants (in rem)
SPACING = {
    'xs': '0.25rem',
    'sm': '0.5rem',
    'md': '1rem',
    'lg': '1.5rem',
    'xl': '2rem',
    '2xl': '3rem',
    '3xl': '4rem',
}

# Animation Settings
ANIMATIONS = {
    'duration': {
        'fast': '150ms',
        'base': '200ms',
        'slow': '300ms',
    },
    'easing': 'cubic-bezier(0.4, 0, 0.2, 1)',
}

# Professional CSS Styles
def get_professional_css():
    """Returns professional CSS styling for the application"""
    return f"""
    <style>
    /* Hide Streamlit default styling */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Professional transitions */
    .stMetric, .stSelectbox, .stButton {{
        transition: all {ANIMATIONS['duration']['base']} {ANIMATIONS['easing']};
    }}
    
    /* Professional button styling */
    .stButton > button {{
        background-color: {COLORS['primary']};
        color: {COLORS['white']};
        border: none;
        border-radius: 6px;
        font-weight: {TYPOGRAPHY['weights']['medium']};
        transition: all {ANIMATIONS['duration']['base']} {ANIMATIONS['easing']};
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }}
    
    .stButton > button:hover {{
        background-color: {COLORS['primary_dark']};
        box-shadow: 0 4px 12px rgba(31, 119, 180, 0.15);
        transform: translateY(-1px);
    }}
    
    /* Professional metric cards */
    [data-testid="metric-container"] {{
        background-color: {COLORS['white']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 8px;
        padding: {SPACING['md']};
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: all {ANIMATIONS['duration']['base']} {ANIMATIONS['easing']};
    }}
    
    [data-testid="metric-container"]:hover {{
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }}
    
    /* Professional sidebar styling */
    .css-1d391kg {{
        background-color: {COLORS['light_gray']};
        border-right: 1px solid {COLORS['border_medium']};
    }}
    
    /* Status pill styling */
    .status-pill {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: {TYPOGRAPHY['sizes']['sm']};
        font-weight: {TYPOGRAPHY['weights']['medium']};
        text-align: center;
    }}
    
    .status-online {{
        background-color: {COLORS['success']};
        color: {COLORS['white']};
    }}
    
    .status-offline {{
        background-color: {COLORS['danger']};
        color: {COLORS['white']};
    }}
    
    .status-warning {{
        background-color: {COLORS['warning']};
        color: {COLORS['white']};
    }}
    
    /* Fade-in animation for main content */
    .main-content {{
        animation: fadeIn {ANIMATIONS['duration']['slow']} {ANIMATIONS['easing']};
    }}
    
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    /* Professional data tables */
    .stDataFrame {{
        border-radius: 8px;
        border: 1px solid {COLORS['border_light']};
        overflow: hidden;
    }}
    
    /* Professional expander styling */
    .streamlit-expanderHeader {{
        background-color: {COLORS['light_gray']};
        border-radius: 6px;
        border: 1px solid {COLORS['border_light']};
    }}
    
    /* Chart container styling */
    .js-plotly-plot {{
        border-radius: 8px;
        border: 1px solid {COLORS['border_light']};
        background-color: {COLORS['white']};
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }}
    </style>
    """

# Professional color scheme for charts
CHART_COLORS = [
    COLORS['primary'],
    COLORS['secondary'],
    COLORS['success'],
    COLORS['info'],
    COLORS['warning'],
    '#8c564b',
    '#e377c2',
    '#7f7f7f',
    '#bcbd22',
    '#17becf'
]