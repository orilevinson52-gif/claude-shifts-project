# מדריך פריסה מלא ל-Render (Deployment Guide) 🚀

מדריך זה מסביר שלב-אחר-שלב כיצד לפרוס את מערכת שיבוץ המשמרות בענן דרך **Render** וליהנות מכתובת אינטרנט ציבורית ומאובטחת (`https://<app-name>.onrender.com`).

---

## 🏗️ מבנה המערכת בענן

1. **אפליקציית Web ב-Render:**
   - רצה כשירות Web Service מבוסס Python 3.11 / Docker (תוכנית Free).
   - מריצה שרת FastAPI + Uvicorn + NiceGUI עם תמיכה מלאה ב-WebSockets ו-RTL.
2. **מסד נתונים MySQL בענן:**
   - מאחר ש-Render אינו מציע MySQL מובנה בתוכנית החינמית (הוא מציע רק PostgreSQL חינמי שתקף ל-30 יום), אנו מחברים מסד נתונים מנוהל בחינם לכל החיים (Free Forever) דרך **TiDB Cloud Serverless** או **Aiven**.

---

## שלב 1: פתיחת מסד נתונים MySQL חינמי בענן (2 דקות)

האפשרות המומלצת ביותר היא **TiDB Cloud Serverless** (תואם 100% ל-MySQL, חינמי לתמיד ללא כרטיס אשראי):

1. היכנס ל-[tidbcloud.com](https://tidbcloud.com) והירשם (ניתן להתחבר בלחיצה עם Google / GitHub).
2. בחר ב-**Serverless** (חינמי).
3. לחץ על **Create Cluster**.
4. לאחר כמה שניות, לחץ על **Connect**:
   - בחר ב-**Language: General** או **Python**.
   - יוצגו לך הפרטים:
     - **Host:** לדוגמה `gateway01.us-east-1.prod.aws.tidbcloud.com`
     - **Port:** `4000` (או `3306`)
     - **User:** לדוגמה `xxxxxx.root`
     - **Password:** הסיסמה שהופקה (שמור אותה בצד!)
     - **Database:** `test` (או צור מסד בשם `shift_scheduler`)

> 💡 **טיפ:** האפליקציה כוללת סקריפט אתחול אוטומטי (`AUTO_INIT_DB=true`). ברגע שהאפליקציה תתחבר לראשונה למסד הנתונים בענן, היא תיצור את כל הטבלאות הנדרשות (`Roles`, `Personnel`, `Positions`, `Shifts_Roster`, `Personnel_Unavailability`) ואת התפקידים הראשוניים בעצמה!

---

## שלב 2: העלאת השינויים ל-GitHub

ודא שכל הקבצים מעודכנים ונדחפו למאגר שלך ב-GitHub:

```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

---

## שלב 3: הקמת האפליקציה ב-Render

יש שתי דרכים פשוטות להקים את האפליקציה ב-Render:

### אפשרות א': דרך ה-Blueprint של Render (הכי מהיר ומומלץ!)

הפרויקט כולל קובץ [render.yaml](render.yaml) מוגדר מראש:

1. היכנס לחשבון שלך ב-[dashboard.render.com](https://dashboard.render.com).
2. לחץ על **New +** > **Blueprint**.
3. בחר את ה-Repository שלך (`claude-shifts-project`).
4. Render יזהה אוטומטית את קובץ ה-`render.yaml` ויציג את שירות ה-Web עם כל המאפיינים.
5. במסך שיופיע, הזן את פרטי החיבור למסד הנתונים שהעתקת משלב 1:
   - `DB_HOST`
   - `DB_PORT` (למשל `4000`)
   - `DB_USER`
   - `DB_PASSWORD`
   - `DB_NAME` (למשל `test` או `shift_scheduler`)
   *(או לחלופין מלא את `DATABASE_URL` אם יש לך מחרוזת חיבור מלאה)*
6. לחץ על **Apply**.

---

### אפשרות ב': הקמה ידנית של Web Service

אם ברצונך להקים ללא Blueprint:

1. ב-Render Dashboard לחץ על **New +** > **Web Service**.
2. חבר את ה-Repository שלך מ-GitHub.
3. מלא את השדות הבאים:
   - **Name:** `shift-scheduler`
   - **Region:** Frankfurt (EU Central) או Ohio (US East)
   - **Runtime:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Instance Type:** `Free`
4. גלול למטה ל-**Environment Variables** והוסף את המשתנים:
   - `PYTHON_VERSION` = `3.11.9`
   - `AUTO_INIT_DB` = `true`
   - `DB_HOST` = (ה-Host מספק הענן)
   - `DB_PORT` = (הפורט, למשל `4000` או `3306`)
   - `DB_USER` = (שם המשתמש)
   - `DB_PASSWORD` = (הסיסמה)
   - `DB_NAME` = (שם מסד הנתונים)
   - `DB_SSL_VERIFY_CERT` = `true`
5. לחץ על **Deploy Web Service**.

---

## שלב 4: אימות הפריסה

1. בלשונית **Logs** ב-Render תראה:
   ```text
   ==> Building service...
   ==> Installing dependencies...
   ==> Running 'python main.py'
   Table 'Roles' checked/created successfully.
   Table 'Personnel' checked/created successfully.
   Table 'Positions' checked/created successfully.
   Table 'Shifts_Roster' checked/created successfully.
   Table 'Personnel_Unavailability' checked/created successfully.
   Default roles created: ['לוחם', 'מאבטח', 'סמבצית', 'סייר']
   Database schema is ready.
   Uvicorn running on http://0.0.0.0:10000
   ```
2. Render יסמן את השירות כ-**Live** בירוק.
3. לחץ על הקישור הראשי בראש הדף (לדוגמה: `https://shift-scheduler-xxxx.onrender.com`).
4. המערכת תעלה במלואה בעברית עם כל הטאבים!

---

## 🔍 פתרון תקלות ודגשים חשובים (FAQ)

### 1. זמן תגובה בפנייה ראשונה (Free Tier Spin-down)
בתוכנית החינמית של Render, כאשר אין תנועה במשך 15 דקות, השירות נכנס למצב "שינה" (Spin down). בפנייה הבאה ייתכן עיכוב של 30–50 שניות עד שהשרת מתעורר. זהו התנהגות רגילה של התוכנית החינמית.

### 2. בדיקת בריאות (Health Check)
האפליקציה כוללת נתיב בדיקה ייעודי ב-`/health`. Render בודק נתיב זה באופן תקופתי כדי לוודא שהשירות חי ומגיב.

### 3. שימוש ב-Docker במקום Python Runtime
אם תעדיף לפרוס כ-Container, הפרויקט מכיל קובץ [Dockerfile](Dockerfile) מוכן. ב-Render שנה את ה-Runtime ל-`Docker`, והבנייה תתבצע אוטומטית מתוך ה-Container.
