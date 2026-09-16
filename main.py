from nicegui import app, ui

from config import APP_PORT, AUTO_INIT_DB, SEED_INITIAL_DATA
from pages import (
    constraints_page,
    personnel_page,
    positions_page,
    roles_page,
    schedule_page,
    shifts_page,
)
from scripts.init_db import ensure_schema, seed_sample_data

ui.add_head_html(
    """
    <link rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Rubik:wght@500;700;800&family=Heebo:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap">
    <style>
    :root {
        --rc-bg: oklch(0.97 0.005 60);
        --rc-panel: oklch(0.995 0.002 60);
        --rc-surface: oklch(0.94 0.007 60);
        --rc-border: oklch(0.85 0.009 60);
        --rc-border-soft: oklch(0.90 0.007 60);
        --rc-text: oklch(0.20 0.01 60);
        --rc-text-dim: oklch(0.26 0.01 60);
        --rc-text-muted: oklch(0.46 0.012 60);
        --rc-text-faint: oklch(0.54 0.01 60);
        --rc-amber: oklch(0.64 0.17 55);
        --rc-teal: oklch(0.48 0.11 195);
        --rc-danger: oklch(0.52 0.17 25);
        --rc-danger-bg: oklch(0.52 0.17 25 / 0.08);
    }

    body {
        direction: rtl;
        background: var(--rc-bg) !important;
        color: var(--rc-text);
        font-family: 'Heebo', system-ui, 'Segoe UI', Arial, sans-serif;
    }

    .rc-title {
        font-family: 'Rubik', sans-serif;
        font-weight: 800;
        letter-spacing: -0.01em;
        color: oklch(0.15 0.012 60);
    }

    .rc-heading {
        font-family: 'Rubik', sans-serif;
        font-weight: 700;
        color: var(--rc-text-dim);
    }

    .rc-mono {
        font-family: 'IBM Plex Mono', ui-monospace, monospace;
        direction: ltr;
        unicode-bidi: isolate;
    }

    .q-tabs { border-bottom: 1px solid var(--rc-border); }
    .q-tab { font-family: 'Heebo', sans-serif; color: var(--rc-text-faint) !important; }
    .q-tab--active { color: var(--rc-amber) !important; font-weight: 600; }
    .q-tab__indicator { background: var(--rc-amber) !important; height: 2.5px !important; }

    .q-table { background: var(--rc-panel) !important; border: 1px solid var(--rc-border); border-radius: 10px; overflow: hidden; }
    .q-table th, .q-table td { text-align: right; border-color: var(--rc-border-soft) !important; }
    .q-table thead th { background: var(--rc-surface) !important; color: var(--rc-text-faint) !important; font-weight: 600; font-size: 12.5px; }
    .q-table tbody td { color: var(--rc-text-dim) !important; font-size: 14px; }

    .q-card { background: var(--rc-panel) !important; }
    .q-field__native, .q-field__label, .q-item__label { font-family: 'Heebo', sans-serif; }

    .rc-pill {
        display: inline-flex;
        align-items: center;
        padding: 3px 12px;
        border-radius: 999px;
        font-size: 12.5px;
        font-weight: 500;
        border: 1px solid oklch(0.48 0.11 195 / 0.35);
        color: var(--rc-teal);
        background: oklch(0.48 0.11 195 / 0.10);
    }

    .rc-cell-empty { color: var(--rc-danger) !important; background: var(--rc-danger-bg); }
    </style>
    """,
    shared=True,
)


@ui.page("/")
def index():
    ui.colors(
        primary="oklch(0.64 0.17 55)",
        secondary="oklch(0.48 0.11 195)",
        accent="oklch(0.48 0.11 195)",
        negative="oklch(0.52 0.17 25)",
        positive="oklch(0.48 0.11 195)",
        warning="oklch(0.64 0.17 55)",
        info="oklch(0.48 0.11 195)",
    )
    ui.label("מערכת שיבוץ משמרות אבטחה").classes("rc-title text-2xl q-mb-md")

    with ui.tabs().classes("w-full") as tabs:
        personnel_tab = ui.tab("אנשי צוות")
        roles_tab = ui.tab("תפקידים")
        positions_tab = ui.tab("עמדות")
        shifts_tab = ui.tab("משמרות")
        constraints_tab = ui.tab("אילוצים")
        schedule_tab = ui.tab("שיבוץ")

    with ui.tab_panels(tabs, value=personnel_tab).classes("w-full").style("background: transparent"):
        with ui.tab_panel(personnel_tab):
            personnel_page.build()
        with ui.tab_panel(roles_tab):
            roles_page.build()
        with ui.tab_panel(positions_tab):
            positions_page.build()
        with ui.tab_panel(shifts_tab):
            shifts_page.build()
        with ui.tab_panel(constraints_tab):
            constraints_page.build()
        with ui.tab_panel(schedule_tab):
            schedule_page.build()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_startup
def on_startup():
    if AUTO_INIT_DB:
        try:
            ensure_schema()
            if SEED_INITIAL_DATA:
                seed_sample_data()
        except Exception as exc:
            print(f"[WARN] Startup database verification: {exc}")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="שיבוץ משמרות אבטחה",
        host="0.0.0.0",
        port=APP_PORT,
        reload=False,
        show=False,
        forwarded_allow_ips="*",
    )
