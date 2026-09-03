@echo off
chcp 65001 >nul
title ISU 185 - V54 Baslat
if not exist venv\Scripts\activate.bat (
 echo Once KURULUM_TEK_TIK.bat calistirin.
 pause
 exit /b 1
)
call venv\Scripts\activate.bat
echo [1/6] Veritabani guncellemeleri kontrol ediliyor...
python manage.py migrate --noinput
if errorlevel 1 goto error
echo [2/6] Devir ve Ambar hesaplari kontrol ediliyor...
python manage.py v50_guncelle
if errorlevel 1 goto error
echo [3/6] Merkez Ambar hesabi kontrol ediliyor...
python manage.py v52_guncelle
if errorlevel 1 goto error
echo [4/6] Abonelik devir verileri kontrol ediliyor...
python manage.py v53_guncelle
if errorlevel 1 goto error
echo [5/6] V54 Sicil / Sozlesme / Ambar yetkileri kontrol ediliyor...
python manage.py v54_guncelle
if errorlevel 1 goto error
echo [6/6] Sistem kontrolu...
python manage.py check
if errorlevel 1 goto error
python manage.py runserver
pause
exit /b 0
:error
echo.
echo BASLATMA DURDU. Yukaridaki hata satirini ChatGPT'ye gonderin.
pause
exit /b 1
