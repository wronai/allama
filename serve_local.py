#!/usr/bin/env python3
"""
Skrypt do uruchamiania lokalnego serwera PHP dla raportów benchmarków Allama.
"""
import os
import sys
import subprocess
import webbrowser
import argparse
import shutil
from pathlib import Path

def find_php():
    """Sprawdza, czy PHP jest dostępne w systemie."""
    try:
        result = subprocess.run(["which", "php"], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        
        # Sprawdź typowe lokalizacje PHP
        common_paths = [
            "/usr/bin/php",
            "/usr/local/bin/php",
            "/opt/homebrew/bin/php"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
                
        return None
    except Exception:
        return None

def copy_server_files(source_dir, target_dir, exclude_files=None):
    """Kopiuje pliki z serwera do lokalnego katalogu, pomijając określone pliki."""
    if exclude_files is None:
        exclude_files = []
    
    # Upewnij się, że katalog docelowy istnieje
    os.makedirs(target_dir, exist_ok=True)
    
    # Kopiuj pliki PHP z serwera
    copied_files = []
    for file in os.listdir(source_dir):
        if file.endswith('.php') and file not in exclude_files:
            source_file = os.path.join(source_dir, file)
            target_file = os.path.join(target_dir, file)
            
            # Kopiuj tylko jeśli plik źródłowy jest nowszy lub plik docelowy nie istnieje
            if not os.path.exists(target_file) or os.path.getmtime(source_file) > os.path.getmtime(target_file):
                shutil.copy2(source_file, target_file)
                copied_files.append(file)
    
    return copied_files

def main():
    parser = argparse.ArgumentParser(description="Uruchamia lokalny serwer PHP dla raportów benchmarków Allama")
    parser.add_argument("--port", type=int, default=8000, help="Port na którym ma być uruchomiony serwer (domyślnie 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Nie otwieraj przeglądarki automatycznie")
    parser.add_argument("--no-sync", action="store_true", help="Nie synchronizuj plików z serwera")
    args = parser.parse_args()
    
    # Znajdź ścieżkę do PHP
    php_path = find_php()
    if not php_path:
        print("Błąd: Nie znaleziono PHP. Upewnij się, że PHP jest zainstalowane i dostępne w PATH.")
        sys.exit(1)
    
    # Ustal ścieżkę do katalogu projektu
    project_dir = Path(__file__).parent.absolute()
    server_dir = project_dir / "server"
    local_server_dir = project_dir / "local_server"
    
    # Upewnij się, że katalog local_server istnieje
    os.makedirs(local_server_dir, exist_ok=True)
    
    # Synchronizuj pliki z serwera do local_server, pomijając upload.php
    if not args.no_sync and server_dir.exists():
        print("Synchronizacja plików z serwera...")
        copied_files = copy_server_files(server_dir, local_server_dir, exclude_files=['upload.php'])
        if copied_files:
            print(f"Skopiowano pliki: {', '.join(copied_files)}")
        
        # Utwórz plik local_config.php, który wskazuje, że jest to środowisko lokalne
        with open(local_server_dir / "local_config.php", "w") as f:
            f.write("<?php\n// Konfiguracja dla lokalnego środowiska\n$IS_LOCAL_ENV = true;\n?>")
    
    # Skopiuj niezbędne pliki statyczne
    static_dir = local_server_dir / "static"
    os.makedirs(static_dir / "js", exist_ok=True)
    os.makedirs(static_dir / "css", exist_ok=True)
    os.makedirs(static_dir / "templates", exist_ok=True)
    
    # Kopiuj pliki statyczne, jeśli istnieją
    source_static = project_dir / "allama" / "static"
    if source_static.exists():
        if (source_static / "js" / "radar-chart.js").exists():
            shutil.copy2(source_static / "js" / "radar-chart.js", static_dir / "js" / "radar-chart.js")
        
        if (source_static / "css" / "allama-charts.css").exists():
            shutil.copy2(source_static / "css" / "allama-charts.css", static_dir / "css" / "allama-charts.css")
        
        if (source_static / "templates" / "stats-badges.html").exists():
            shutil.copy2(source_static / "templates" / "stats-badges.html", static_dir / "templates" / "stats-badges.html")
    
    # Uruchom serwer PHP
    port = args.port
    server_url = f"http://localhost:{port}"
    
    print(f"Uruchamianie lokalnego serwera PHP na porcie {port}...")
    print(f"Adres serwera: {server_url}")
    print("Naciśnij Ctrl+C, aby zatrzymać serwer.")
    
    # Otwórz przeglądarkę, jeśli nie wybrano opcji --no-browser
    if not args.no_browser:
        webbrowser.open(server_url)
    
    # Uruchom serwer PHP
    try:
        subprocess.run([
            php_path, 
            "-S", 
            f"localhost:{port}", 
            "-t", 
            str(local_server_dir)
        ])
    except KeyboardInterrupt:
        print("\nSerwer zatrzymany.")

if __name__ == "__main__":
    main()
