@echo off
echo Running monthly_profit table fix...
python direct_fix_monthly_profit.py > fix_output.txt 2>&1
echo Fix completed. Check fix_output.txt for details.
type fix_output.txt
