@echo off
chcp 65001 > nul
echo ========================================================
echo  העלאת השינויים ל-GitHub (ענף main)
echo ========================================================
echo.

"C:\Program Files\Git\cmd\git.exe" push origin main

echo.
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] השינויים עלו בהצלחה ל-GitHub!
) else (
    echo [ERROR] אירעה שגיאה בהעלאה. בדוק את ההודעה למעלה.
)
echo.
pause
