"""Guided on-screen tour: a spotlight on real elements (marked with data-tour="...") plus a popover per step."""

import json

from nicegui import run, ui

from db.connection import get_connection, set_tour_done

ENGINE = """
<style>
.tour-block { position: fixed; inset: 0; z-index: 9000; }
.tour-spot { position: fixed; z-index: 9001; border-radius: 12px; pointer-events: none;
  box-shadow: 0 0 0 9999px rgba(10, 10, 8, .58); transition: all .28s cubic-bezier(.2,.8,.2,1); }
.tour-spot.center { width: 0 !important; height: 0 !important; top: 50% !important; left: 50% !important; }
.tour-spot::after { content: ''; position: absolute; inset: -3px; border-radius: 14px; border: 2px solid var(--accent); }
.tour-spot.center::after { display: none; }
.tour-pop { position: fixed; z-index: 9002; width: 340px; max-width: calc(100vw - 32px); box-sizing: border-box;
  background: var(--panel); color: var(--text); border-radius: 16px; padding: 20px; direction: rtl;
  box-shadow: 0 20px 60px rgba(0,0,0,.3); font-family: 'Heebo', system-ui, sans-serif;
  transition: top .28s cubic-bezier(.2,.8,.2,1), left .28s cubic-bezier(.2,.8,.2,1); }
.tour-pop:focus { outline: none; }
.tour-step { font-size: 12.5px; color: var(--muted); font-weight: 500; }
.tour-title { font-family: 'Rubik', sans-serif; font-weight: 600; font-size: 18px; margin: 6px 0 6px; }
.tour-text { font-size: 14.5px; line-height: 1.6; color: var(--text); margin: 0 0 16px; }
.tour-dots { display: flex; gap: 5px; }
.tour-dots span { width: 6px; height: 6px; border-radius: 3px; background: var(--border); transition: all .2s; }
.tour-dots span.on { width: 18px; background: var(--accent); }
.tour-actions { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.tour-actions .btns { display: flex; gap: 8px; }
.tour-btn { height: 38px; padding: 0 16px; border-radius: 9px; font: 600 14px 'Heebo', sans-serif; cursor: pointer;
  border: 1px solid var(--border); background: var(--panel); color: var(--text); }
.tour-btn.primary { background: var(--accent); color: var(--on-accent); border-color: var(--accent); }
.tour-skip { background: none; border: none; color: var(--muted); font: 500 13px 'Heebo', sans-serif; cursor: pointer;
  padding: 4px 0; margin-top: 12px; text-decoration: underline; }
@keyframes tourIn { from { opacity: 0; transform: translateY(6px) } to { opacity: 1; transform: none } }
.tour-pop.enter { animation: tourIn .25s ease-out; }
</style>
<script>
window.AppTour = (() => {
  let steps = [], index = 0, nodes = null, current = null;

  function visible(el) {
    if (!el) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden';
  }
  function findTarget(step) {
    for (const key of step.targets || []) {
      const el = [...document.querySelectorAll(`[data-tour="${key}"]`)].find(visible);
      if (el) return el;
    }
    return null;
  }
  function build() {
    const block = document.createElement('div'); block.className = 'tour-block';
    const spot = document.createElement('div'); spot.className = 'tour-spot center';
    const pop = document.createElement('div'); pop.className = 'tour-pop';
    pop.setAttribute('role', 'dialog'); pop.setAttribute('aria-modal', 'true'); pop.tabIndex = -1;
    document.body.append(block, spot, pop);
    return { block, spot, pop };
  }
  function place() {
    if (!nodes) return;
    const { spot, pop } = nodes;
    const vw = window.innerWidth, vh = window.innerHeight, pad = 8, gap = 14;
    const pw = pop.offsetWidth, ph = pop.offsetHeight;
    if (!current) {
      spot.classList.add('center');
      pop.style.left = Math.max(16, (vw - pw) / 2) + 'px';
      pop.style.top = Math.max(16, (vh - ph) / 2) + 'px';
      return;
    }
    const r = current.getBoundingClientRect();
    spot.classList.remove('center');
    spot.style.top = (r.top - pad) + 'px'; spot.style.left = (r.left - pad) + 'px';
    spot.style.width = (r.width + pad * 2) + 'px'; spot.style.height = (r.height + pad * 2) + 'px';
    let top;
    if (r.bottom + gap + ph < vh) top = r.bottom + pad + gap;
    else if (r.top - gap - ph > 0) top = r.top - pad - gap - ph;
    else top = Math.min(vh - ph - 16, Math.max(16, r.top));
    let left;
    if (top === Math.min(vh - ph - 16, Math.max(16, r.top)) && r.width < vw / 2) {
      // no room above or below: sit beside the target
      left = r.left - pw - gap > 16 ? r.left - pw - gap : r.right + gap;
    } else {
      left = r.left + r.width / 2 - pw / 2;
    }
    pop.style.left = Math.min(vw - pw - 16, Math.max(16, left)) + 'px';
    pop.style.top = top + 'px';
  }
  function render() {
    const step = steps[index];
    current = findTarget(step);
    const last = index === steps.length - 1;
    const { pop } = nodes;
    pop.classList.remove('enter'); void pop.offsetWidth; pop.classList.add('enter');
    pop.setAttribute('aria-label', step.title);
    pop.innerHTML = '';
    const head = document.createElement('div');
    head.style.cssText = 'display:flex;justify-content:space-between;align-items:center';
    const count = document.createElement('span'); count.className = 'tour-step';
    count.textContent = `${index + 1} מתוך ${steps.length}`;
    const dots = document.createElement('div'); dots.className = 'tour-dots';
    steps.forEach((_, i) => { const d = document.createElement('span'); if (i === index) d.className = 'on'; dots.append(d); });
    head.append(count, dots);
    const title = document.createElement('div'); title.className = 'tour-title'; title.textContent = step.title;
    const text = document.createElement('p'); text.className = 'tour-text'; text.textContent = step.text;
    const actions = document.createElement('div'); actions.className = 'tour-actions';
    const btns = document.createElement('div'); btns.className = 'btns';
    const next = document.createElement('button'); next.type = 'button'; next.className = 'tour-btn primary';
    next.textContent = last ? (step.done_label || 'סיום') : 'הבא';
    next.onclick = () => last ? finish(step) : go(index + 1);
    btns.append(next);
    if (index > 0) {
      const back = document.createElement('button'); back.type = 'button'; back.className = 'tour-btn';
      back.textContent = 'הקודם'; back.onclick = () => go(index - 1); btns.append(back);
    }
    actions.append(btns);
    pop.append(head, title, text, actions);
    if (!last || step.navigate) {
      const skip = document.createElement('button'); skip.type = 'button'; skip.className = 'tour-skip';
      skip.textContent = 'דלג על הסיור'; skip.onclick = () => end(true); pop.append(skip);
    }
    if (current) current.scrollIntoView({ block: 'center', behavior: 'smooth' });
    place(); setTimeout(place, 380);
    next.focus({ preventScroll: true });
  }
  function go(i) { index = i; render(); }
  function finish(step) {
    if (step.navigate) { cleanup(); window.location.href = step.navigate; }
    else end(true);
  }
  function cleanup() {
    if (nodes) { nodes.block.remove(); nodes.spot.remove(); nodes.pop.remove(); nodes = null; }
    window.removeEventListener('resize', place); window.removeEventListener('scroll', place, true);
    document.removeEventListener('keydown', onKey, true);
  }
  function end(markDone) { cleanup(); if (markDone) emitEvent('tour_done'); }
  function onKey(e) {
    if (!nodes) return;
    if (e.key === 'Escape') { e.preventDefault(); end(true); }
  }
  function start(allSteps) {
    cleanup();
    steps = allSteps.filter(s => !s.targets || s.targets.length === 0 || findTarget(s));
    if (!steps.length) return;
    index = 0; nodes = build();
    window.addEventListener('resize', place); window.addEventListener('scroll', place, true);
    document.addEventListener('keydown', onKey, true);
    render();
  }
  return { start };
})();
</script>
"""

HELP_TEXT = "כפתור ה־? בתפריט מפעיל את הסיור מחדש בכל רגע."

STEPS = {
    "dashboard": [
        {"title": "ברוך הבא למערכת שיבוץ המשמרות",
         "text": "סיור קצר של כדקה יראה לך איך בונים סידור עבודה מאפס: צוות, משמרות ושיבוץ. "
                 "אפשר לדלג בכל רגע. " + HELP_TEXT},
        {"targets": ["nav-team", "bottom-team"], "title": "הכל מתחיל בצוות",
         "text": "במסך הצוות מגדירים תפקידים, אנשי צוות, עמדות ואילוצים – הבסיס שהשיבוץ נשען עליו."},
        {"targets": ["nav-board", "bottom-board"], "title": "לוח השיבוץ",
         "text": "כאן בונים את משמרות השבוע ומשבצים אנשים – בגרירה, בלחיצה או אוטומטית."},
        {"targets": ["stats", "empty"], "title": "תמונת מצב",
         "text": "כמה משמרות יש השבוע, כמה כבר משובצות וכמה עוד פתוחות. "
                 "לחיצה על 'לא משובצות' לוקחת ישר ללוח."},
        {"targets": ["todo"], "title": "דורש טיפול",
         "text": "כל משמרת פתוחה, עם הסבר למה אי אפשר לשבץ אותה – למשל כולם הגיעו למכסה, "
                 "או שמי שמתאים נמצא במילואים."},
        {"targets": ["generate"], "title": "צור סידור עבודה",
         "text": "שיבוץ אוטומטי: המערכת ממלאת את המשמרות הפתוחות, שומרת על 8 שעות מנוחה, "
                 "אילוצים ומכסות שבועיות, ומאזנת את השעות בין אנשי הצוות."},
        {"targets": ["help", "help-mobile"], "title": "תמיד אפשר לחזור לכאן",
         "text": "כפתור ה־? מפעיל את הסיור מחדש. עכשיו נעבור למסך הצוות.",
         "done_label": "המשך לצוות", "navigate": "/team?tour=1"},
    ],
    "team": [
        {"targets": ["team-tabs"], "title": "ארבעה סוגי נתונים",
         "text": "הסדר המומלץ: קודם תפקידים (למשל מאבטח, ובהם אפשר להגביל משמרות בשבוע), "
                 "אחר כך אנשי צוות, עמדות (למשל שער ראשי, עם התפקיד הנדרש) ואילוצים (חופשה, מילואים)."},
        {"targets": ["team-add"], "title": "הוספה",
         "text": "הכפתור משתנה לפי הלשונית שבחרת: איש צוות, תפקיד, עמדה או אילוץ. "
                 "הטופס נפתח מהצד."},
        {"targets": ["team-card"], "title": "כרטיס",
         "text": "עיפרון לעריכה ופח למחיקה. בכרטיס של איש צוות רואים גם כמה שעות עבד השבוע ואם יש לו אילוץ קרוב."},
        {"targets": ["team-search"], "title": "חיפוש",
         "text": "מסנן את אנשי הצוות לפי שם או תפקיד."},
        {"targets": ["nav-board", "bottom-board"], "title": "עכשיו – השיבוץ",
         "text": "כשיש תפקידים, אנשי צוות ועמדות, עוברים ללוח השיבוץ.",
         "done_label": "המשך ללוח", "navigate": "/board?tour=1"},
    ],
    "board": [
        {"targets": ["week-nav"], "title": "בחירת שבוע",
         "text": "החצים עוברים בין שבועות. כל שבוע נבנה בנפרד."},
        {"targets": ["week-builder"], "title": "משמרות לשבוע",
         "text": "כאן מגדירים אילו משמרות יש בכל עמדה בכל יום. "
                 "יש מילוי מהיר ל־06–14, 14–22 ו־22–06 לכל העמדות בבת אחת."},
        {"targets": ["board-empty"], "title": "הצעד הבא שלך",
         "text": "עדיין אין משמרות בשבוע הזה. אחרי שתיצור אותן, יופיע כאן לוח שבועי לפי עמדות וימים."},
        {"targets": ["people-panel"], "title": "גרירה",
         "text": "גרור איש צוות אל משמרת. בזמן הגרירה המשבצות שאפשר לשבץ בהן יידלקו בכחול, "
                 "והחסומות יתעמעמו – מעבר עם העכבר מסביר למה."},
        {"targets": ["day-pills"], "title": "בוחרים יום",
         "text": "בטלפון בוחרים יום למעלה, ולוחצים על משמרת כדי לבחור מי ישובץ."},
        {"targets": ["shift-card", "m-shift"], "title": "לחיצה על משמרת",
         "text": "פותחת רשימה של מי שמתאים לתפקיד, מסודרת לפי זמינות ושעות. "
                 "משם גם מסירים שיבוץ או מוחקים משמרת."},
        {"targets": ["auto-schedule"], "title": "שבץ אוטומטית",
         "text": "ממלא בבת אחת את כל המשמרות הפתוחות לפי הכללים. אחר כך אפשר לתקן ידנית בגרירה."},
        {"title": "זהו, אתה מוכן",
         "text": "הסדר בקצרה: מסך הצוות ← משמרות לשבוע ← שבץ אוטומטית ← תיקונים בגרירה. " + HELP_TEXT,
         "done_label": "סיום"},
    ],
}


def install():
    ui.add_body_html(ENGINE, shared=True)


def attach(page_key, user_id, start):
    """Registers the 'tour done' handler for this page and starts the tour when asked."""

    async def mark_done():
        def save():
            conn = get_connection()
            try:
                set_tour_done(conn, user_id, True)
            finally:
                conn.close()

        try:
            await run.io_bound(save)
        except Exception:
            pass  # showing the tour again next time is harmless

    ui.on("tour_done", mark_done)
    if start:
        # after this render reaches the browser, so every target exists
        ui.timer(0.4, lambda: ui.run_javascript(f"window.AppTour.start({json.dumps(STEPS[page_key])})"), once=True)
