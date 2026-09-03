@echo off
chcp 65001 >nul
title ISU 185 - Mobil Saha Sunucusu
if not exist venv\Scripts\activate.bat (
 echo Once KURULUM_TEK_TIK.bat calistirin.
 pause
 exit /b 1
)
call venv\Scripts\activate.bat
set ISU_ALLOWED_HOSTS=*
echo.
echo ================================================
echo ISU 185 MOBIL SAHA SUNUCUSU
echo ================================================
echo Telefon ve bilgisayar AYNI Wi-Fi aginda olmali.
echo Asagidaki IPv4 adreslerinden bilgisayarinizinkini kullanin:
ipconfig | findstr /C:"IPv4"
echo.
echo Telefonda ornek:
echo http://BILGISAYAR_IP:8000/mobil/saha/
echo.
python manage.py runserver 0.0.0.0:8000
pause
