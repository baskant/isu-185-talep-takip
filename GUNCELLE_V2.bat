@echo off
chcp 65001 >nul
title ISU 185 - V2 Guncelleme

if not exist manage.py (
  echo HATA: Bu dosya manage.py bulunan proje klasorunde calistirilmali.
  pause
  exit /b 1
)

if not exist venv\Scripts\activate.bat (
  echo Sanal ortam bulunamadi. Once KURULUM_TEK_TIK.bat calistirin.
  pause
  exit /b 1
)

call venv\Scripts\activate.bat

echo [1/3] Veritabani semasi kontrol ediliyor...
python manage.py migrate
if errorlevel 1 goto error

echo [2/3] Genisletilmis ISU is turleri ve temel veriler guncelleniyor...
python manage.py seed_isu
if errorlevel 1 goto error

echo [3/3] Sistem kontrolu...
python manage.py check
if errorlevel 1 goto error

echo.
echo ==========================================
echo V2 GUNCELLEMESI BASARILI
echo ==========================================
echo Mevcut db.sqlite3 ve kullanici hesaplari korunmustur.
echo BASLAT.bat ile sistemi yeniden baslatin.
pause
exit /b 0

:error
echo.
echo GUNCELLEME DURDU. Yukaridaki hata satirini ChatGPT'ye gonderin.
pause
exit /b 1
