#!/usr/bin/env python3
"""
Allama - Skrypt uruchamiający benchmark modeli LLM
"""

import os
import sys
import subprocess

# Ustaw zmienną środowiskową, aby poinformować moduł o automatycznym uruchomieniu
os.environ['ALLAMA_AUTO_RUN'] = '1'

# Uruchom moduł allama.main
try:
    from allama.main import main
    
    # Uruchom benchmark i uzyskaj ścieżkę do raportu
    report_path = main()
    print(f"Benchmark zakończony. Raport dostępny w: {report_path}")
    
except ImportError:
    print("Nie można zaimportować modułu allama.main. Upewnij się, że pakiet jest zainstalowany.")
    sys.exit(1)
except Exception as e:
    print(f"Wystąpił błąd podczas uruchamiania benchmarku: {e}")
    sys.exit(1)
