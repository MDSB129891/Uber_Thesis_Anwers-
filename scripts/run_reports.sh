#!/usr/bin/env bash
set -e
python3 scripts/run_uber_update.py
python3 scripts/build_investment_report.py
open outputs/decision_report_UBER.html
open export/UBER_Investment_Report.docx
open export/UBER_Investment_Report.xlsx
