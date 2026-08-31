"""Visual system for the Streamlit shell."""


def get_custom_css() -> str:
    """Return layout and component styles shared by both color modes."""
    return """
    <style>
    :root {
        --font-ui: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 18px;
        --shadow-card: 0 1px 2px rgba(0, 0, 0, 0.04), 0 12px 32px rgba(0, 0, 0, 0.05);
        --transition: 160ms ease;
    }

    html, body, [class*="css"] {
        font-family: var(--font-ui) !important;
    }

    .stApp {
        background: var(--bg-page) !important;
        color: var(--text-primary) !important;
    }

    .stMainBlockContainer,
    .block-container {
        max-width: 1120px !important;
        padding-top: 3rem !important;
        padding-bottom: 4rem !important;
    }

    header[data-testid="stHeader"] {
        background: color-mix(in srgb, var(--bg-page) 88%, transparent) !important;
        border-bottom: 1px solid var(--border-subtle) !important;
        backdrop-filter: blur(14px);
    }

    #MainMenu, [data-testid="stToolbarActions"] {
        opacity: 0.7;
    }

    .reader-hero {
        margin: 0 0 1.75rem;
    }

    .reader-kicker {
        margin-bottom: 0.55rem;
        color: var(--accent) !important;
        font-size: 0.74rem;
        font-weight: 750;
        letter-spacing: 0.13em;
        text-transform: uppercase;
    }

    .reader-hero h1 {
        margin: 0;
        color: var(--text-primary) !important;
        font-size: clamp(2rem, 5vw, 3.25rem);
        font-weight: 720;
        letter-spacing: -0.045em;
        line-height: 1.04;
    }

    .reader-hero p {
        max-width: 620px;
        margin: 0.8rem 0 0;
        color: var(--text-secondary) !important;
        font-size: 1rem;
        line-height: 1.65;
    }

    [data-testid="stForm"] {
        padding: 1.25rem !important;
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        box-shadow: var(--shadow-card) !important;
    }

    .chapter-context {
        display: flex;
        align-items: center;
        min-height: 2.55rem;
        padding: 0.65rem 0.9rem;
        background: var(--accent-soft);
        border: 1px solid var(--accent-border);
        border-radius: var(--radius-md);
        color: var(--accent-strong) !important;
        font-size: 0.9rem;
        font-weight: 650;
    }

    .reader-empty-note {
        margin: 0.75rem 0 0;
        color: var(--text-tertiary) !important;
        font-size: 0.84rem;
    }

    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-baseweb="select"] > div {
        min-height: 2.65rem;
        background: var(--input-bg) !important;
        border-color: var(--border) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-primary) !important;
        box-shadow: none !important;
    }

    [data-testid="stTextInput"] input:focus,
    [data-testid="stNumberInput"] input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-ring) !important;
    }

    [data-testid="stWidgetLabel"] p,
    .stCaption p {
        color: var(--text-secondary);
    }

    [data-testid="stWidgetLabel"] p {
        font-size: 0.82rem !important;
        font-weight: 650 !important;
    }

    button[kind^="primary"],
    [data-testid^="stBaseButton-primary"] {
        background: var(--accent) !important;
        border: 1px solid var(--accent) !important;
        color: #fff !important;
        box-shadow: none !important;
    }

    button[kind^="primary"]:hover,
    [data-testid^="stBaseButton-primary"]:hover {
        background: var(--accent-hover) !important;
        border-color: var(--accent-hover) !important;
    }

    button[kind^="secondary"],
    [data-testid^="stBaseButton-secondary"] {
        background: var(--button-bg) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
        box-shadow: none !important;
    }

    button[kind^="secondary"]:hover,
    [data-testid^="stBaseButton-secondary"]:hover {
        background: var(--surface-hover) !important;
        border-color: var(--border-strong) !important;
        color: var(--text-primary) !important;
    }

    .stButton > button,
    [data-testid="stFormSubmitButton"] > button {
        min-height: 2.65rem;
        border-radius: var(--radius-md) !important;
        font-family: var(--font-ui) !important;
        font-size: 0.88rem !important;
        font-weight: 650 !important;
        transition: background var(--transition), border-color var(--transition), transform var(--transition) !important;
    }

    .stButton > button:active,
    [data-testid="stFormSubmitButton"] > button:active {
        transform: scale(0.985);
    }

    .stButton > button p,
    [data-testid="stFormSubmitButton"] > button p {
        color: inherit !important;
    }

    [data-testid="stAlert"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-primary) !important;
    }

    [data-testid="stExpander"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        box-shadow: none !important;
    }

    [data-baseweb="tab-list"] {
        gap: 0.25rem !important;
        padding: 0.2rem !important;
        background: var(--surface-muted) !important;
        border-radius: 10px !important;
    }

    [data-baseweb="tab"] {
        min-width: 0 !important;
        padding: 0.5rem 0.7rem !important;
        border-radius: 8px !important;
        color: var(--text-secondary) !important;
        font-size: 0.78rem !important;
    }

    [aria-selected="true"][data-baseweb="tab"] {
        background: var(--surface) !important;
        color: var(--text-primary) !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
    }

    [data-baseweb="tab-highlight"],
    [data-baseweb="tab-border"] {
        display: none !important;
    }

    [role="tablist"] {
        gap: 0.25rem !important;
        padding: 0.2rem !important;
        background: var(--surface-muted) !important;
        border-radius: 10px !important;
    }

    [data-testid="stTab"] {
        padding: 0.45rem 0.65rem !important;
        border: 0 !important;
        border-radius: 8px !important;
        color: var(--text-secondary) !important;
        font-size: 0.78rem !important;
    }

    [data-testid="stTab"][data-selected="true"] {
        background: var(--surface) !important;
        color: var(--text-primary) !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
    }

    .react-aria-SelectionIndicator {
        display: none !important;
    }

    section[data-testid="stSidebar"] {
        background: var(--sidebar-bg) !important;
        border-right: 1px solid var(--border-subtle) !important;
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1.25rem;
    }

    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: var(--text-primary);
    }

    section[data-testid="stSidebar"] hr {
        border-color: var(--border-subtle) !important;
        margin: 1rem 0 !important;
    }

    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.15rem 0 0.85rem;
    }

    .sidebar-mark {
        display: grid;
        width: 2.35rem;
        height: 2.35rem;
        place-items: center;
        background: var(--accent);
        border-radius: 11px;
        color: #fff !important;
        font-size: 1.05rem;
        font-weight: 750;
    }

    .sidebar-brand strong {
        display: block;
        color: var(--text-primary) !important;
        font-size: 0.96rem;
    }

    .sidebar-brand small {
        display: block;
        margin-top: 0.1rem;
        color: var(--text-tertiary) !important;
        font-size: 0.72rem;
    }

    .sidebar-section-label {
        margin: 0.2rem 0 0.65rem;
        color: var(--text-tertiary) !important;
        font-size: 0.7rem;
        font-weight: 750;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }

    .sidebar-stats {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.45rem;
    }

    .sidebar-stat {
        padding: 0.65rem 0.35rem;
        background: var(--surface-muted);
        border: 1px solid var(--border-subtle);
        border-radius: 10px;
        text-align: center;
    }

    .sidebar-stat b {
        display: block;
        color: var(--text-primary) !important;
        font-size: 1rem;
    }

    .sidebar-stat span {
        display: block;
        margin-top: 0.12rem;
        color: var(--text-tertiary) !important;
        font-size: 0.65rem;
    }

    .sidebar-footer {
        margin-top: 1.5rem;
        color: var(--text-tertiary) !important;
        font-size: 0.7rem;
        line-height: 1.5;
        text-align: center;
    }

    iframe[title="st.iframe"] {
        border-radius: var(--radius-lg);
    }

    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: var(--scroll-thumb);
        border: 2px solid transparent;
        border-radius: 999px;
        background-clip: padding-box;
    }

    @media (max-width: 740px) {
        .stMainBlockContainer,
        .block-container {
            padding: 1.6rem 1rem 3rem !important;
        }

        .reader-hero { margin-bottom: 1.25rem; }
        .reader-hero h1 { font-size: 2.15rem; }
        [data-testid="stForm"] { padding: 1rem !important; }

        [data-testid="stHorizontalBlock"] {
            gap: 0.55rem !important;
        }

        [data-testid="stColumn"] {
            min-width: 0 !important;
        }
    }

    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            scroll-behavior: auto !important;
            transition-duration: 0.01ms !important;
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
        }
    }
    </style>
    """


def get_theme_css(is_dark: bool = True) -> str:
    """Return all color tokens for the selected theme."""
    if is_dark:
        colors = {
            "bg_page": "#0b0d10",
            "sidebar_bg": "#101216",
            "surface": "#15181d",
            "surface_muted": "#1a1e24",
            "surface_hover": "#20252c",
            "input_bg": "#111419",
            "button_bg": "#171b20",
            "text_primary": "#f4f5f7",
            "text_secondary": "#a8afb9",
            "text_tertiary": "#747d89",
            "border": "#2a3038",
            "border_subtle": "#20252c",
            "border_strong": "#3a424d",
            "accent": "#4f7cff",
            "accent_hover": "#6a8fff",
            "accent_soft": "rgba(79, 124, 255, 0.12)",
            "accent_border": "rgba(79, 124, 255, 0.27)",
            "accent_strong": "#9ab3ff",
            "accent_ring": "rgba(79, 124, 255, 0.18)",
            "scroll_thumb": "#3c444f",
        }
    else:
        colors = {
            "bg_page": "#f6f7f9",
            "sidebar_bg": "#fbfbfc",
            "surface": "#ffffff",
            "surface_muted": "#f1f3f6",
            "surface_hover": "#f4f6f8",
            "input_bg": "#ffffff",
            "button_bg": "#ffffff",
            "text_primary": "#17191d",
            "text_secondary": "#5f6670",
            "text_tertiary": "#8a929d",
            "border": "#dfe3e8",
            "border_subtle": "#eaedf0",
            "border_strong": "#c5cbd3",
            "accent": "#315fd6",
            "accent_hover": "#264fb7",
            "accent_soft": "#edf3ff",
            "accent_border": "#d2e0ff",
            "accent_strong": "#264fae",
            "accent_ring": "rgba(49, 95, 214, 0.14)",
            "scroll_thumb": "#c4cad2",
        }

    variables = "\n".join(
        f"            --{name.replace('_', '-')}: {value};"
        for name, value in colors.items()
    )
    return f"""
    <style>
        :root {{
{variables}
        }}
    </style>
    """
