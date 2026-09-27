"""Shared look for every screen: theme tokens, icons, the app shell and small building blocks."""

from contextlib import contextmanager
from datetime import date

from nicegui import app, ui

DAY_NAMES = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]
DAY_LETTERS = ["א׳", "ב׳", "ג׳", "ד׳", "ה׳", "ו׳", "ש׳"]
ROLE_PALETTE_SIZE = 6

CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rubik:wght@500;600;700&family=Heebo:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap">
<style>
:root {
  --bg: #f6f6f3; --panel: #ffffff; --sunken: #f1f1ed; --border: #e4e3de;
  --text: #1a1a17; --muted: #5f5e58;
  --accent: #2b59c3; --on-accent: #ffffff; --accent-soft: #e8eefb; --accent-text: #1f4296;
  --warn: #b4470c; --warn-soft: #fdf1e8; --warn-border: #f5d3bb; --ok: #1f7a55;
  --rc0-bg: #e8eefb; --rc0-fg: #1f4296; --rc0-bar: #4a74d4;
  --rc1-bg: #e3f3eb; --rc1-fg: #1c6b4b; --rc1-bar: #2f9468;
  --rc2-bg: #fbf2d5; --rc2-fg: #7a5a00; --rc2-bar: #c9a227;
  --rc3-bg: #f1e8fa; --rc3-fg: #6a2c91; --rc3-bar: #9557c2;
  --rc4-bg: #dff1f3; --rc4-fg: #0f5f66; --rc4-bar: #2a8f99;
  --rc5-bg: #fbe7ee; --rc5-fg: #8f2350; --rc5-bar: #c24b7c;
}
body.body--dark {
  --bg: #131416; --panel: #1b1c1f; --sunken: #232428; --border: #2e3035;
  --text: #ededea; --muted: #a3a29c;
  --accent: #7ea2f2; --on-accent: #0f1a33; --accent-soft: #1f2c47; --accent-text: #b7cbf7;
  --warn: #f29a5c; --warn-soft: #2d1f15; --warn-border: #5a3a22; --ok: #5cc99a;
  --rc0-bg: #1f2c47; --rc0-fg: #b7cbf7; --rc0-bar: #7ea2f2;
  --rc1-bg: #173327; --rc1-fg: #8fdcb8; --rc1-bar: #5cc99a;
  --rc2-bg: #332a10; --rc2-fg: #e9c96b; --rc2-bar: #d9b54a;
  --rc3-bg: #2e2140; --rc3-fg: #d6b8f0; --rc3-bar: #b98be0;
  --rc4-bg: #12302f; --rc4-fg: #86d6d2; --rc4-bar: #4fb8b3;
  --rc5-bg: #3a1a26; --rc5-fg: #f0a9c4; --rc5-bar: #e07aa3;
}
.rc0 { --rc-bg: var(--rc0-bg); --rc-fg: var(--rc0-fg); --rc-bar: var(--rc0-bar); }
.rc1 { --rc-bg: var(--rc1-bg); --rc-fg: var(--rc1-fg); --rc-bar: var(--rc1-bar); }
.rc2 { --rc-bg: var(--rc2-bg); --rc-fg: var(--rc2-fg); --rc-bar: var(--rc2-bar); }
.rc3 { --rc-bg: var(--rc3-bg); --rc-fg: var(--rc3-fg); --rc-bar: var(--rc3-bar); }
.rc4 { --rc-bg: var(--rc4-bg); --rc-fg: var(--rc4-fg); --rc-bar: var(--rc4-bar); }
.rc5 { --rc-bg: var(--rc5-bg); --rc-fg: var(--rc5-fg); --rc-bar: var(--rc5-bar); }

html, body { direction: rtl; }
body { background: var(--bg) !important; color: var(--text); font-family: 'Heebo', system-ui, sans-serif; }
.nicegui-content { padding: 0 !important; gap: 0 !important; }
.q-field__native, .q-field__label, .q-item__label, .q-btn, .q-menu, .q-dialog { font-family: 'Heebo', system-ui, sans-serif; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

.font-display { font-family: 'Rubik', sans-serif; }
.mono { font-family: 'IBM Plex Mono', ui-monospace, monospace; direction: ltr; unicode-bidi: isolate; }
.muted { color: var(--muted); }
.warn-text { color: var(--warn); }
.ok-text { color: var(--ok); }
.page-title { font-family: 'Rubik', sans-serif; font-weight: 700; font-size: 30px; letter-spacing: -0.01em; margin: 0; line-height: 1.2; }
.section-title { font-family: 'Rubik', sans-serif; font-weight: 600; font-size: 18px; margin: 0; }

/* shell */
.app-shell { display: flex; min-height: 100vh; width: 100%; }
.rail { width: 76px; flex-shrink: 0; background: #1a1a17; display: flex; flex-direction: column; align-items: center;
  padding: 18px 0; gap: 6px; position: sticky; top: 0; height: 100vh; box-sizing: border-box; }
.rail-logo { width: 40px; height: 40px; border-radius: 10px; background: #2b59c3; display: flex; align-items: center;
  justify-content: center; margin-bottom: 18px; color: #fff; }
.rail-link { width: 60px; padding: 10px 0 8px; border-radius: 10px; display: flex; flex-direction: column; align-items: center;
  gap: 4px; text-decoration: none; color: #c9c8c1; font-size: 11px; font-weight: 500; transition: background .15s, color .15s; }
.rail-link:hover { background: #2e2e2a; color: #fff; }
.rail-link.active { background: #2e2e2a; color: #fff; }
.rail-btn { width: 44px; height: 44px; border: none; border-radius: 10px; background: transparent; color: #c9c8c1;
  display: flex; align-items: center; justify-content: center; cursor: pointer; transition: background .15s; }
.rail-btn:hover { background: #2e2e2a; color: #fff; }
.rail-avatar { width: 36px; height: 36px; border-radius: 50%; background: #3a3a35; color: #fff; display: flex; align-items: center;
  justify-content: center; font-size: 13px; font-weight: 600; margin-top: 6px; }
.app-main { flex-grow: 1; min-width: 0; padding: 32px 40px; display: flex; flex-direction: column; gap: 24px; box-sizing: border-box; }
.bottom-nav { display: none; }

/* building blocks */
.card { background: var(--panel); border: 1px solid var(--border); border-radius: 14px; }
.lift { transition: transform .18s ease, box-shadow .18s ease; }
.lift:hover { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(20,20,15,.08); }
.stat-value { font-family: 'Rubik', sans-serif; font-size: 36px; font-weight: 600; line-height: 1; }
.progress { height: 6px; border-radius: 3px; background: var(--sunken); overflow: hidden; }
.progress > div { height: 100%; border-radius: 3px; background: var(--ok); transition: width .5s cubic-bezier(.2,.8,.2,1); }
.bar-track { height: 10px; border-radius: 5px; background: var(--sunken); overflow: hidden; }
.bar-track > div { height: 100%; border-radius: 5px; background: var(--rc-bar, var(--accent)); transition: width .5s cubic-bezier(.2,.8,.2,1); }
.pill { display: inline-flex; align-items: center; font-size: 12px; font-weight: 500; padding: 1px 8px; border-radius: 999px;
  background: var(--rc-bg); color: var(--rc-fg); white-space: nowrap; }
.avatar { border-radius: 50%; background: var(--rc-bg); color: var(--rc-fg); display: flex; align-items: center;
  justify-content: center; font-weight: 600; flex-shrink: 0; }
.warn-card { background: var(--warn-soft); border: 1px solid var(--warn-border); border-radius: 14px; }
.todo-row { display: flex; align-items: center; gap: 12px; padding: 11px 14px; border-radius: 10px; background: var(--sunken);
  text-decoration: none; color: var(--text); }
.dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

.btn { height: 44px; padding: 0 18px; border-radius: 10px; font-size: 15px; font-weight: 600; display: inline-flex;
  align-items: center; justify-content: center; gap: 8px; cursor: pointer; border: 1px solid transparent; text-decoration: none;
  font-family: 'Heebo', system-ui, sans-serif; transition: filter .15s, background .15s; white-space: nowrap; }
.btn:hover { filter: brightness(1.06); }
.btn-primary { background: var(--accent); color: var(--on-accent); }
.btn-secondary { background: var(--panel); color: var(--text); border-color: var(--border); font-weight: 500; }
.btn-secondary:hover { background: var(--sunken); filter: none; }
.btn-danger { background: transparent; color: var(--warn); border-color: var(--border); }
.btn-ghost { background: transparent; color: var(--muted); border: none; padding: 0 10px; }
.btn-ghost:hover { background: var(--sunken); filter: none; }
.icon-btn { width: 34px; height: 34px; border: none; border-radius: 8px; background: transparent; color: var(--muted);
  display: inline-flex; align-items: center; justify-content: center; cursor: pointer; padding: 0; }
.icon-btn:hover { background: var(--sunken); color: var(--text); }
.btn:disabled, .btn[disabled] { opacity: .5; cursor: not-allowed; }

.segmented { display: flex; gap: 4px; background: var(--sunken); border-radius: 11px; padding: 4px; }
.segmented button { height: 38px; padding: 0 16px; border: none; border-radius: 8px; font-size: 14.5px; font-weight: 600;
  background: transparent; color: var(--muted); cursor: pointer; display: flex; align-items: center; gap: 8px; font-family: inherit; }
.segmented button.on { background: var(--panel); color: var(--text); box-shadow: 0 1px 3px rgba(20,20,15,.12); }

.field-input { height: 44px; border-radius: 10px; border: 1px solid var(--border); background: var(--panel); color: var(--text);
  padding: 0 14px; font-size: 15px; font-family: inherit; box-sizing: border-box; width: 100%; }
.field-input:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 22%, transparent); }

/* board */
.board-grid { display: grid; grid-template-columns: 116px repeat(7, minmax(0, 1fr)); gap: 8px; }
.shift-card { box-sizing: border-box; border-radius: 9px; border: 1.5px solid transparent; padding: 6px 8px; min-height: 56px;
  display: flex; flex-direction: column; justify-content: space-between; gap: 3px; cursor: pointer;
  transition: background .15s, border-color .15s, opacity .15s, transform .15s; background: var(--rc-bg); color: var(--rc-fg); }
.shift-card:hover { transform: translateY(-1px); }
.shift-card.is-open { background: var(--panel); border: 1.5px dashed var(--warn); color: var(--warn); }
.shift-card.is-ok { background: var(--accent-soft); border: 1.5px dashed var(--accent); color: var(--accent-text); opacity: 1; }
.shift-card.is-blocked { opacity: .35; }
.shift-card.is-self { border-color: var(--accent); }
.shift-name { font-size: 12.5px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.chip { display: flex; align-items: center; gap: 10px; padding: 8px 10px; border-radius: 10px; border: 1px solid var(--border);
  background: var(--panel); cursor: grab; transition: background .15s, transform .15s, box-shadow .15s; user-select: none; }
.chip:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(20,20,15,.08); }
.chip.dragging { background: var(--accent-soft); border-color: var(--accent); }
.drag-banner { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 9px; background: var(--accent-soft);
  color: var(--accent-text); font-size: 13.5px; font-weight: 500; }
.day-head { display: flex; flex-direction: column; align-items: center; gap: 1px; padding: 4px 0; border-radius: 8px; }
.day-head.today { background: var(--accent-soft); color: var(--accent-text); }
@keyframes pop { 0% { transform: scale(.96) } 60% { transform: scale(1.03) } 100% { transform: scale(1) } }
.pop { animation: pop .28s ease-out; }
.day-pill { height: 58px; border-radius: 12px; border: 1px solid var(--border); background: var(--panel); color: var(--text);
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; padding: 0; position: relative;
  cursor: pointer; font-family: inherit; }
.day-pill.on { background: var(--accent); border-color: var(--accent); color: var(--on-accent); }
.m-shift { min-height: 56px; border-radius: 12px; display: flex; align-items: center; gap: 12px; padding: 0 14px; cursor: pointer;
  background: var(--rc-bg); color: var(--rc-fg); border: 1.5px solid transparent; }
.m-shift.is-open { background: var(--panel); border: 1.5px dashed var(--warn); color: var(--warn); }

/* dialogs & toasts */
.sheet-card { background: var(--panel) !important; color: var(--text); border-radius: 18px !important; padding: 22px !important;
  width: 440px; max-width: 94vw; box-shadow: 0 20px 60px rgba(0,0,0,.25) !important; }
.candidate { display: flex; align-items: center; gap: 12px; padding: 8px 12px; border-radius: 12px; border: 1px solid var(--border);
  background: var(--panel); color: var(--text); min-height: 56px; cursor: pointer; text-align: right; font-family: inherit; width: 100%; }
.candidate:hover { background: var(--sunken); }
.candidate.current { background: var(--accent-soft); border-color: var(--accent); }
.candidate.blocked { opacity: .5; cursor: not-allowed; }
.candidate.blocked:hover { background: var(--panel); }
.app-toast { background: #1a1a17 !important; color: #fff !important; border-radius: 12px !important; font-family: 'Heebo', sans-serif;
  font-weight: 500; box-shadow: 0 10px 30px rgba(0,0,0,.25) !important; }
.q-table { background: var(--panel) !important; color: var(--text) !important; border: 1px solid var(--border); border-radius: 14px; }
.q-table th, .q-table td { text-align: right; border-color: var(--border) !important; }
.q-table thead th { background: var(--sunken) !important; color: var(--muted) !important; font-weight: 600; }

/* auth */
.auth-wrap { display: flex; min-height: 100vh; width: 100%; }
.auth-form { width: 620px; flex-shrink: 0; display: flex; flex-direction: column; justify-content: center; padding: 40px 110px;
  box-sizing: border-box; gap: 24px; }
.auth-art { flex-grow: 1; margin: 20px; border-radius: 24px; background: #1d2a4d; position: relative; overflow: hidden;
  display: flex; flex-direction: column; justify-content: flex-end; padding: 56px; box-sizing: border-box; min-height: 560px; }
@keyframes floaty { 0%, 100% { transform: translateY(0) } 50% { transform: translateY(-6px) } }
.float-a { animation: floaty 6s ease-in-out infinite; }
.float-b { animation: floaty 7s ease-in-out infinite .8s; }

.sm-only { display: none !important; }

@media (max-width: 1100px) {
  .auth-form { width: 100%; padding: 40px 24px; }
  .auth-art { display: none; }
}
@media (max-width: 767px) {
  .rail { display: none; }
  .app-main { padding: 20px 16px 96px; gap: 18px; }
  .page-title { font-size: 24px; }
  .bottom-nav { display: grid; grid-template-columns: repeat(var(--nav-count, 3), minmax(0, 1fr)); position: fixed; bottom: 0;
    left: 0; right: 0; height: 68px; background: var(--panel); border-top: 1px solid var(--border); z-index: 50;
    padding-bottom: env(safe-area-inset-bottom); }
  .bottom-link { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px;
    text-decoration: none; color: var(--muted); font-size: 12px; font-weight: 500; }
  .bottom-link.active { color: var(--accent-text); font-weight: 600; }
  .lg-only { display: none !important; }
  .sm-only { display: flex !important; }
  .stats-grid { grid-template-columns: repeat(2, minmax(0, 1fr)) !important; }
  .two-col { grid-template-columns: minmax(0, 1fr) !important; }
  .cards-grid { grid-template-columns: minmax(0, 1fr) !important; }
  .header-row { flex-direction: column; align-items: stretch !important; }
  .sheet-card { width: 100vw; max-width: 100vw; border-radius: 22px 22px 0 0 !important; }
}
</style>
"""

ICONS = {
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
    "dashboard": '<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/>'
                 '<rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>'
             '<path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
    "admin": '<circle cx="12" cy="8" r="4"/><path d="M4 21v-1a6 6 0 0 1 9-5.2"/><path d="m17 15 1.5 3 3 .5-2.2 2 .6 3-2.9-1.5-2.9 1.5.6-3-2.2-2 3-.5z"/>',
    "moon": '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2'
           'M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>',
    "logout": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
    "sparkle": '<path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3'
               'L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4M12 17h.01"/>',
    "check_circle": '<circle cx="12" cy="12" r="10"/><path d="m8 12 3 3 5-6"/>',
    "chev_right": '<path d="m9 18 6-6-6-6"/>',
    "chev_left": '<path d="m15 18-6-6 6-6"/>',
    "plus": '<path d="M5 12h14M12 5v14"/>',
    "x": '<path d="M18 6 6 18M6 6l12 12"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "trash": '<path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    "edit": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    "arrow": '<path d="M19 12H5M12 19l-7-7 7-7"/>',
    "home": '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M9 22V12h6v10"/>',
    "list_plus": '<path d="M11 12H3M16 6H3M16 18H3M18 9v6M21 12h-6"/>',
    "help": '<circle cx="12" cy="12" r="10"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
    "eraser": '<path d="m7 21-4.3-4.3a1 1 0 0 1 0-1.4l10-10a1 1 0 0 1 1.4 0l5.6 5.6a1 1 0 0 1 0 1.4L13 19"/><path d="M22 21H7M5 11l9 9"/>',
}


def icon_svg(name, size=20, stroke_width=1.75):
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        f"{ICONS[name]}</svg>"
    )


def icon(name, size=20, stroke_width=1.75):
    # Our own static SVG markup, so there is nothing to sanitize
    return ui.html(icon_svg(name, size, stroke_width), sanitize=False, tag="span").classes("inline-flex")


def install_theme():
    ui.add_head_html(CSS, shared=True)


def role_class(role, role_names):
    """Stable color slot per role: its position among the user's roles."""
    try:
        index = sorted(role_names).index(role)
    except ValueError:
        index = sum(map(ord, role or ""))
    return f"rc{index % ROLE_PALETTE_SIZE}"


def initials(name):
    return "".join(word[0] for word in (name or "").split()[:2])


def ltr(text):
    return f"⁦{text}⁩"


def fmt_date(value):
    return f"{value.day}.{value.month}"


def fmt_time(value):
    return value.strftime("%H:%M")


def pill(text, rclass):
    return ui.label(text).classes(f"pill {rclass}")


def toast(message, kind="ok"):
    ui.notify(message, position="bottom", timeout=2600, classes="app-toast",
              icon="check_circle" if kind == "ok" else "error_outline")


def db_error(error):
    ui.notify(f"שגיאת תקשורת עם מסד הנתונים: {error}", type="negative", position="bottom")


def button(text, on_click=None, kind="primary", icon_name=None, href=None):
    """A styled native button (or link when href is given)."""
    tag = "a" if href else "button"
    btn = ui.element(tag).classes(f"btn btn-{kind}")
    if href:
        btn.props(f'href="{href}"')
    else:
        btn.props('type="button"')
    with btn:
        if icon_name:
            icon(icon_name, 18)
        ui.label(text)
    if on_click:
        btn.on("click", on_click)
    return btn


def icon_button(icon_name, label, on_click, size=18):
    btn = ui.element("button").classes("icon-btn").props(f'type="button" aria-label="{label}" title="{label}"')
    with btn:
        icon(icon_name, size)
    btn.on("click", on_click)
    return btn


def is_dark():
    return bool(app.storage.user.get("dark", False))


def apply_color_scheme():
    ui.colors(primary="#2b59c3", secondary="#1f7a55", accent="#2b59c3", negative="#b4470c",
              positive="#1f7a55", warning="#b4470c", info="#2b59c3")
    return ui.dark_mode(is_dark())


NAV = [
    ("dashboard", "/", "דשבורד", "dashboard"),
    ("board", "/board", "לוח שיבוץ", "calendar"),
    ("team", "/team", "צוות", "users"),
]


@contextmanager
def app_shell(active, username, show_admin=False, on_logout=None):
    """Side rail on desktop, bottom bar on phones; yields the main content column."""
    dark_mode = apply_color_scheme()
    nav = NAV + ([("admin", "/admin", "משתמשים", "admin")] if show_admin else [])

    def toggle_dark():
        app.storage.user["dark"] = not is_dark()
        dark_mode.value = is_dark()
        theme_icon.refresh()

    @ui.refreshable
    def theme_icon():
        icon("sun" if is_dark() else "moon", 20)

    with ui.element("div").classes("app-shell"):
        with ui.element("nav").classes("rail").props('aria-label="ניווט ראשי"'):
            with ui.element("div").classes("rail-logo"):
                icon("shield", 22, 2)
            for key, href, label, icon_name in nav:
                link = ui.element("a").classes("rail-link" + (" active" if key == active else "")).props(
                    f'href="{href}" data-tour="nav-{key}"'
                )
                if key == active:
                    link.props('aria-current="page"')
                with link:
                    icon(icon_name, 20)
                    ui.label(label)
            ui.element("div").classes("flex-grow")
            with ui.element("a").classes("rail-btn").props(
                'href="/?tour=1" aria-label="סיור מודרך" title="סיור מודרך" data-tour="help"'
            ):
                icon("help", 20)
            theme_btn = ui.element("button").classes("rail-btn").props('type="button" aria-label="החלפת מצב תצוגה"')
            with theme_btn:
                theme_icon()
            theme_btn.on("click", toggle_dark)
            out = ui.element("button").classes("rail-btn").props(
                f'type="button" aria-label="התנתקות" title="{username} · התנתקות"'
            )
            with out:
                icon("logout", 19)
            if on_logout:
                out.on("click", on_logout)
            ui.label(initials(username).upper() or "?").classes("rail-avatar").props(f'title="{username}"')

        with ui.element("main").classes("app-main") as main:
            with ui.element("div").classes("sm-only items-center justify-between"):
                with ui.element("div").classes("flex items-center gap-2"):
                    with ui.element("div").classes("rail-logo").style("margin: 0; width: 34px; height: 34px"):
                        icon("shield", 19, 2)
                    ui.label(username).classes("text-sm muted")
                with ui.element("div").classes("flex items-center gap-1"):
                    with ui.element("a").classes("icon-btn").style("width: 44px; height: 44px").props(
                        'href="/?tour=1" aria-label="סיור מודרך" data-tour="help-mobile"'
                    ):
                        icon("help", 20)
                    mobile_theme = ui.element("button").classes("icon-btn").props(
                        'type="button" aria-label="החלפת מצב תצוגה"'
                    ).style("width: 44px; height: 44px")
                    with mobile_theme:
                        theme_icon()
                    mobile_theme.on("click", toggle_dark)
                    if on_logout:
                        icon_button("logout", "התנתקות", on_logout, 19).style("width: 44px; height: 44px")
            yield main

    with ui.element("nav").classes("bottom-nav").style(f"--nav-count: {len(nav)}").props('aria-label="ניווט ראשי"'):
        for key, href, label, icon_name in nav:
            with ui.element("a").classes("bottom-link" + (" active" if key == active else "")).props(
                f'href="{href}" data-tour="bottom-{key}"'
            ):
                icon(icon_name, 22)
                ui.label(label)


def week_label(week_start, week_end):
    week_number = week_start.isocalendar()[1]
    return f"שבוע {week_number} · {fmt_date(week_start)} – {fmt_date(week_end)}.{week_end.year}"


def today():
    return date.today()
