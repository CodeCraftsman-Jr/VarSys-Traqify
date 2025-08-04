"""
Plotly Theme Configuration for Dark Theme Consistency
Provides global dark theme configuration for all Plotly charts
"""

try:
    import plotly.graph_objects as go
    import plotly.io as pio
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

def configure_plotly_theme(theme='light'):
    """Configure Plotly to use the specified theme globally"""
    if not PLOTLY_AVAILABLE:
        return

    if theme == 'dark':
        configure_plotly_dark_theme()
    elif theme == 'light':
        configure_plotly_light_theme()
    elif theme == 'colorwave':
        configure_plotly_colorwave_theme()
    else:
        # Default to light theme
        configure_plotly_light_theme()

def configure_plotly_light_theme():
    """Configure Plotly to use light theme globally"""
    if not PLOTLY_AVAILABLE:
        return

    # Define light theme template
    light_template = go.layout.Template(
        layout=go.Layout(
            # Background colors
            plot_bgcolor='#ffffff',
            paper_bgcolor='#ffffff',

            # Font settings
            font=dict(
                color='#000000',
                family='Arial, sans-serif',
                size=12
            ),

            # Title settings
            title=dict(
                font=dict(
                    color='#000000',
                    size=16
                ),
                x=0.5,
                xanchor='center'
            ),

            # Axis settings
            xaxis=dict(
                gridcolor='#e0e0e0',
                linecolor='#e0e0e0',
                tickcolor='#000000',
                tickfont=dict(color='#000000'),
                zerolinecolor='#e0e0e0',
                title=dict(font=dict(color='#000000'))
            ),
            yaxis=dict(
                gridcolor='#e0e0e0',
                linecolor='#e0e0e0',
                tickcolor='#000000',
                tickfont=dict(color='#000000'),
                zerolinecolor='#e0e0e0',
                title=dict(font=dict(color='#000000'))
            ),

            # Legend settings
            legend=dict(
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='#e0e0e0',
                borderwidth=1,
                font=dict(color='#000000')
            ),

            # Colorway for consistent colors
            colorway=[
                '#0e639c', '#1177bb', '#4caf50', '#ff9800',
                '#f44336', '#9c27b0', '#607d8b', '#795548'
            ],

            # Hover settings
            hoverlabel=dict(
                bgcolor='#ffffff',
                bordercolor='#e0e0e0',
                font=dict(color='#000000')
            )
        )
    )

    # Register the template
    pio.templates['light_theme'] = light_template
    pio.templates.default = 'light_theme'

    print("Plotly light theme configured successfully")

def configure_plotly_dark_theme():
    """Configure Plotly to use dark theme globally"""
    if not PLOTLY_AVAILABLE:
        return

    # Define dark theme template
    dark_template = go.layout.Template(
        layout=go.Layout(
            # Background colors
            plot_bgcolor='#252526',
            paper_bgcolor='#1e1e1e',

            # Font settings
            font=dict(
                color='#ffffff',
                family='Arial, sans-serif',
                size=12
            ),

            # Title settings
            title=dict(
                font=dict(
                    color='#ffffff',
                    size=16
                ),
                x=0.5,
                xanchor='center'
            ),

            # Axis settings
            xaxis=dict(
                gridcolor='#3e3e42',
                linecolor='#3e3e42',
                tickcolor='#ffffff',
                tickfont=dict(color='#ffffff'),
                zerolinecolor='#3e3e42',
                title=dict(font=dict(color='#ffffff'))
            ),
            yaxis=dict(
                gridcolor='#3e3e42',
                linecolor='#3e3e42',
                tickcolor='#ffffff',
                tickfont=dict(color='#ffffff'),
                zerolinecolor='#3e3e42',
                title=dict(font=dict(color='#ffffff'))
            ),

            # Legend settings
            legend=dict(
                bgcolor='rgba(30, 30, 30, 0.8)',
                bordercolor='#3e3e42',
                borderwidth=1,
                font=dict(color='#ffffff')
            ),

            # Colorway for consistent colors
            colorway=[
                '#0e639c', '#1177bb', '#4caf50', '#ff9800',
                '#f44336', '#9c27b0', '#607d8b', '#795548'
            ],

            # Hover settings
            hoverlabel=dict(
                bgcolor='#252526',
                bordercolor='#3e3e42',
                font=dict(color='#ffffff')
            )
        )
    )

    # Register the template
    pio.templates['dark_theme'] = dark_template
    pio.templates.default = 'dark_theme'

    print("Plotly dark theme configured successfully")

def configure_plotly_colorwave_theme():
    """Configure Plotly to use colorwave theme globally"""
    if not PLOTLY_AVAILABLE:
        return

    # Define colorwave theme template
    colorwave_template = go.layout.Template(
        layout=go.Layout(
            # Background colors
            plot_bgcolor='#1a1a2e',
            paper_bgcolor='#0a0a1a',

            # Font settings
            font=dict(
                color='#ffffff',
                family='Arial, sans-serif',
                size=12
            ),

            # Title settings
            title=dict(
                font=dict(
                    color='#ffffff',
                    size=16
                ),
                x=0.5,
                xanchor='center'
            ),

            # Axis settings
            xaxis=dict(
                gridcolor='#4a3c5a',
                linecolor='#4a3c5a',
                tickcolor='#ffffff',
                tickfont=dict(color='#ffffff'),
                zerolinecolor='#4a3c5a',
                title=dict(font=dict(color='#ffffff'))
            ),
            yaxis=dict(
                gridcolor='#4a3c5a',
                linecolor='#4a3c5a',
                tickcolor='#ffffff',
                tickfont=dict(color='#ffffff'),
                zerolinecolor='#4a3c5a',
                title=dict(font=dict(color='#ffffff'))
            ),

            # Legend settings
            legend=dict(
                bgcolor='rgba(26, 26, 46, 0.8)',
                bordercolor='#4a3c5a',
                borderwidth=1,
                font=dict(color='#ffffff')
            ),

            # Colorway for consistent colors
            colorway=[
                '#c2185b', '#00bcd4', '#4caf50', '#ff9800',
                '#f44336', '#9c27b0', '#607d8b', '#795548'
            ],

            # Hover settings
            hoverlabel=dict(
                bgcolor='#1a1a2e',
                bordercolor='#4a3c5a',
                font=dict(color='#ffffff')
            )
        )
    )

    # Register the template
    pio.templates['colorwave_theme'] = colorwave_template
    pio.templates.default = 'colorwave_theme'

    print("Plotly colorwave theme configured successfully")

def apply_dark_theme_to_figure(fig):
    """Apply dark theme to a specific Plotly figure"""
    if not PLOTLY_AVAILABLE:
        return fig
    
    fig.update_layout(
        plot_bgcolor='#252526',
        paper_bgcolor='#1e1e1e',
        font=dict(color='#ffffff'),
        title=dict(font=dict(color='#ffffff')),
        xaxis=dict(
            gridcolor='#3e3e42',
            linecolor='#3e3e42',
            tickcolor='#ffffff',
            tickfont=dict(color='#ffffff'),
            title=dict(font=dict(color='#ffffff'))
        ),
        yaxis=dict(
            gridcolor='#3e3e42',
            linecolor='#3e3e42',
            tickcolor='#ffffff',
            tickfont=dict(color='#ffffff'),
            title=dict(font=dict(color='#ffffff'))
        ),
        legend=dict(
            bgcolor='rgba(30, 30, 30, 0.8)',
            bordercolor='#3e3e42',
            font=dict(color='#ffffff')
        )
    )
    
    return fig

def get_dark_theme_html_template(html_content):
    """Wrap Plotly HTML content with dark theme styling"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: Arial, sans-serif;
            }}
            .plotly-graph-div {{
                height: 100vh;
                width: 100vw;
                background-color: #1e1e1e;
            }}
            .modebar {{
                background-color: #252526 !important;
            }}
            .modebar-btn {{
                color: #ffffff !important;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

# Initialize light theme by default when module is imported
if PLOTLY_AVAILABLE:
    configure_plotly_light_theme()
