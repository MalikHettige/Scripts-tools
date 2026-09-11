@echo off
REM run_vdp_finder.bat
REM Double-click this to run the VDP finder script and save results to vdps.txt

cd /d "%~dp0"
python vdp_finder.py --save vdps.txt
pause
