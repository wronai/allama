#!/usr/bin/env python3
"""
Skrypt do przygotowania środowiska TestLLM
"""

import os
import subprocess
import sys


def install_requirements():
    """Instaluje wymagane pakiety"""
    print("📦 Instalowanie wymaganych pakietów...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Pakiety zainstalowane pomyślnie")
    except subprocess.CalledProcessError as e:
        print(f"❌ Błąd podczas instalacji pakietów: {e}")
        sys.exit(1)


def create_example_models_csv():
    """Tworzy przykładowy plik models.csv jeśli nie istnieje"""
    if not os.path.exists('models.csv'):
        print("📝 Tworzenie przykładowego pliku models.csv...")
        csv_content = """model_name,url,auth_header,auth_value,think,description
deepseek-coder:1.3b,http://192.168.188.108:8081/api/chat,,,false,DeepSeek Coder 1.3B na lokalnym serwerze
mistral:latest,http://192.168.188.212:11434/api/chat,,,false,Mistral Latest na Ollama
devstral:latest,http://192.168.188.212:11434/api/chat,,,false,Devstral Latest na Ollama  
deepseek-r1:8b,http://192.168.188.212:11434/api/chat,,,true,DeepSeek R1 8B z funkcją think
codellama:7b,http://192.168.188.212:11434/api/chat,,,true,CodeLlama 7B z funkcją think"""

        with open('models.csv', 'w', encoding='utf-8') as f:
            f.write(csv_content)
        print("✅ Plik models.csv utworzony")
    else:
        print("📄 Plik models.csv już istnieje")


def main():
    """Główna funkcja setupu"""
    print("🚀 Konfigurowanie środowiska TestLLM...")

    install_requirements()
    create_example_models_csv()

    print("\n✨ Konfiguracja zakończona!")
    print("\n📋 Następne kroki:")
    print("1. Sprawdź i dostosuj plik models.csv do swoich modeli")
    print("2. Uruchom testy: python main.py")
    print("3. Otwórz wygenerowany raport: llm_test_results.html")


if __name__ == "__main__":
    main()