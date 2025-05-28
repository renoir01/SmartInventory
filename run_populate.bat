@echo off
echo Running monthly profit population script...
python populate_monthly_profits.py > populate_output.txt 2>&1
echo Script completed. Check populate_output.txt for details.
type populate_output.txt
