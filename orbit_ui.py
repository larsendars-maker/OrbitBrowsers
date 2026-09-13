THEMES = {
    "VOID": {"bg": "#0b0d12", "surface": "#11151e", "surface2": "#171d29", "border": "#283247", "text": "#f4f7ff", "muted": "#8f9aaf", "accent": "#7657ff"},
    "ICE": {"bg": "#081118", "surface": "#0e1d29", "surface2": "#152a3c", "border": "#2c4d64", "text": "#effaff", "muted": "#8eafc4", "accent": "#42c8ff"},
    "BLUE": {"bg": "#080d16", "surface": "#0e1726", "surface2": "#14243d", "border": "#2c466b", "text": "#f2f7ff", "muted": "#91a7c3", "accent": "#4d8dff"},
    "PURPLE": {"bg": "#0e0815", "surface": "#181023", "surface2": "#251633", "border": "#52336b", "text": "#fff5ff", "muted": "#b49bbf", "accent": "#c35cff"},
    "EMERALD": {"bg": "#07100c", "surface": "#0d1914", "surface2": "#13261d", "border": "#2b4d3d", "text": "#effff6", "muted": "#8fad9f", "accent": "#2bd58a"},
    "RED": {"bg": "#12090a", "surface": "#211112", "surface2": "#32191a", "border": "#603033", "text": "#fff5f5", "muted": "#c39b9e", "accent": "#ff516b"},
}


def stylesheet(theme_name):
    t = THEMES.get(theme_name, THEMES["VOID"])
    return f"""
    QWidget {{ background: {t['bg']}; color: {t['text']}; font-family: 'Segoe UI'; }}
    QMainWindow {{ background: {t['bg']}; }}
    QLineEdit {{ background: {t['surface']}; color: {t['text']}; border: 1px solid {t['border']}; border-radius: 14px; padding: 10px 14px; }}
    QLineEdit:focus {{ border-color: {t['accent']}; }}
    QPushButton {{ background: {t['surface']}; color: {t['text']}; border: 1px solid {t['border']}; border-radius: 11px; padding: 8px 12px; }}
    QPushButton:hover {{ background: {t['surface2']}; border-color: {t['accent']}; }}
    QComboBox {{ background: {t['surface']}; color: {t['text']}; border: 1px solid {t['border']}; border-radius: 10px; padding: 8px; }}
    QTabWidget::pane {{ border: none; background: {t['bg']}; }}
    QTabBar::tab {{ background: {t['surface']}; color: {t['muted']}; padding: 8px 15px; margin-right: 3px; border-radius: 9px; }}
    QTabBar::tab:selected {{ color: {t['text']}; background: {t['surface2']}; border: 1px solid {t['border']}; }}
    QFrame#toolbar {{ background: {t['surface']}; border: 1px solid {t['border']}; border-radius: 15px; }}
    QLabel#logo {{ color: {t['accent']}; font-size: 23px; font-weight: 900; letter-spacing: 2px; }}
    QLabel#title {{ font-size: 28px; font-weight: 800; }}
    QLabel#muted {{ color: {t['muted']}; }}
    """
