@echo off
cd /d "C:\Banknifty App"
echo ==== %date% %time% ==== >> "data\logs\daily_paper_trading.log"
".venv\Scripts\python.exe" -m core.paper.run_daily >> "data\logs\daily_paper_trading.log" 2>&1
