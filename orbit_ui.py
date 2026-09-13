THEMES = {
    "VOID": {"bg":"#0b0b0d","surface":"#141416","surface2":"#1c1c20","border":"#2a2a30","text":"#f5f5f7","muted":"#8e8e98","accent":"#8b7cff"},
    "ICE": {"bg":"#081014","surface":"#101a20","surface2":"#16242c","border":"#263943","text":"#f2fbff","muted":"#91a9b5","accent":"#57c9ff"},
    "BLUE": {"bg":"#090d14","surface":"#111927","surface2":"#19263a","border":"#273b59","text":"#f4f7ff","muted":"#91a3bc","accent":"#5b92ff"},
    "PURPLE": {"bg":"#0e0a13","surface":"#17101e","surface2":"#23172f","border":"#473154","text":"#fff7ff","muted":"#b39fb8","accent":"#c66cff"},
    "EMERALD": {"bg":"#08100b","surface":"#101a15","surface2":"#17251e","border":"#2b4537","text":"#f2fff8","muted":"#96aa9e","accent":"#46d99a"},
    "RED": {"bg":"#120a0b","surface":"#1c1113","surface2":"#29171a","border":"#4b2b30","text":"#fff6f7","muted":"#c19ca1","accent":"#ff667a"},
}


def stylesheet(theme_name):
    t = THEMES.get(theme_name, THEMES["VOID"])
    return f"""
    QWidget {{
        background: {t['bg']};
        color: {t['text']};
        font-family: 'Segoe UI';
        font-size: 13px;
    }}
    QMainWindow {{ background: {t['bg']}; }}
    QFrame#toolbar {{
        background: transparent;
        border: none;
    }}
    QLineEdit#address {{
        background: {t['surface']};
        border: 1px solid transparent;
        border-radius: 20px;
        padding: 10px 17px;
        color: {t['text']};
        font-size: 14px;
        min-height: 23px;
    }}
    QLineEdit#address:focus {{
        border-color: {t['border']};
        background: {t['surface2']};
    }}
    QPushButton {{
        background: transparent;
        color: {t['text']};
        border: 1px solid transparent;
        border-radius: 11px;
        padding: 8px 11px;
    }}
    QPushButton:hover {{
        background: {t['surface2']};
        border-color: {t['border']};
    }}
    QPushButton[accent="true"] {{
        background: {t['accent']};
        color: white;
        border-color: {t['accent']};
        font-weight: 700;
    }}
    QPushButton#homeShortcut {{
        background: transparent;
        border: none;
        color: {t['muted']};
        padding: 8px 14px;
        border-radius: 10px;
    }}
    QPushButton#homeShortcut:hover {{
        color: {t['text']};
        background: {t['surface2']};
    }}
    QTabWidget::pane {{ border: none; background: transparent; }}
    QTabBar::tab {{
        background: transparent;
        color: {t['muted']};
        border: none;
        padding: 8px 16px;
        margin: 1px 2px;
        border-radius: 10px;
        min-width: 90px;
    }}
    QTabBar::tab:hover {{ background: {t['surface2']}; color: {t['text']}; }}
    QTabBar::tab:selected {{
        background: {t['surface']};
        color: {t['text']};
        border: 1px solid {t['border']};
    }}
    QLabel#orbitLogo {{
        font-size: 52px;
        font-weight: 800;
        letter-spacing: 8px;
    }}
    QLabel#homeWelcome {{
        font-size: 18px;
        color: {t['muted']};
    }}
    QLabel#pageTitle {{
        font-size: 28px;
        font-weight: 800;
    }}
    QLabel#sectionTitle {{
        font-size: 15px;
        font-weight: 700;
    }}
    QLabel#muted {{ color: {t['muted']}; }}
    QFrame#profileCard, QFrame#settingsCard, QFrame#contentCard {{
        background: {t['surface']};
        border: 1px solid {t['border']};
        border-radius: 22px;
    }}
    QLabel#badge {{
        background: {t['accent']};
        color: white;
        border-radius: 8px;
        padding: 5px 9px;
        font-weight: 700;
    }}
    QListWidget {{
        background: {t['surface']};
        border: 1px solid {t['border']};
        border-radius: 16px;
        padding: 6px;
    }}
    QListWidget::item {{
        padding: 10px 12px;
        border-radius: 10px;
    }}
    QListWidget::item:hover {{ background: {t['surface2']}; }}
    QComboBox {{
        background: {t['surface']};
        border: 1px solid {t['border']};
        border-radius: 10px;
        padding: 8px 10px;
        color: {t['text']};
    }}
    QComboBox QAbstractItemView {{
        background: {t['surface']};
        color: {t['text']};
        selection-background-color: {t['accent']};
    }}
    QCheckBox {{ spacing: 8px; }}
    QProgressBar {{
        background: {t['surface2']};
        border: none;
        border-radius: 7px;
        min-height: 12px;
        max-height: 12px;
    }}
    QProgressBar::chunk {{
        background: {t['accent']};
        border-radius: 7px;
    }}
    QMenu {{
        background: {t['surface']};
        color: {t['text']};
        border: 1px solid {t['border']};
        border-radius: 12px;
        padding: 5px;
    }}
    QMenu::item {{ padding: 8px 22px 8px 12px; border-radius: 8px; }}
    QMenu::item:selected {{ background: {t['surface2']}; }}
    """


def site_theme_css(theme_name):
    t = THEMES.get(theme_name, THEMES["VOID"])
    return f"""
    html.orbit-theme-enabled {{ background:{t['bg']} !important; color-scheme:dark !important; }}
    html.orbit-theme-enabled body {{ background:{t['bg']} !important; color:{t['text']} !important; }}
    html.orbit-theme-enabled a {{ color:{t['accent']} !important; }}
    html.orbit-theme-enabled input,
    html.orbit-theme-enabled textarea,
    html.orbit-theme-enabled select,
    html.orbit-theme-enabled button {{ background:{t['surface']} !important; color:{t['text']} !important; border-color:{t['border']} !important; }}
    html.orbit-theme-enabled header,
    html.orbit-theme-enabled nav,
    html.orbit-theme-enabled aside,
    html.orbit-theme-enabled footer,
    html.orbit-theme-enabled [role='dialog'],
    html.orbit-theme-enabled [role='menu'] {{ background-color:{t['surface']} !important; color:{t['text']} !important; }}
    """
