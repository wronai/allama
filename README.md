![allama-logo.svg](allama-logo.svg)

# TestLLM - System Testowania Modeli LLM 🧪

Kompleksowy system do testowania i porównywania modeli Large Language Models (LLM) w kontekście generowania kodu Python. Projekt umożliwia automatyczną ocenę jakości wygenerowanego kodu poprzez różne metryki i generuje szczegółowe raporty HTML.

## ✨ Funkcjonalności

- **Automatyczne testowanie** multiple modeli LLM z konfigurowalnymi promptami
- **Ocena jakości kodu** - sprawdzanie składni, wykonalności, stylu i funkcjonalności
- **Szczegółowe raporty HTML** z metrykami, wykresami i porównaniami
- **Eksport wyników** do CSV i JSON dla dalszej analizy
- **Konfigurowalność** - łatwe dodawanie nowych modeli i testów
- **Wsparcie dla różnych API** - Ollama, lokalnych serwerów, usług w chmurze
- **Ranking modeli** na podstawie wydajności i jakości

## 🚀 Szybki Start

### 1. Instalacja

```bash
# Sklonuj projekt
git clone https://github.com/wronai/allama.git
cd testllm

# Zainstaluj zależności
pip install -r requirements.txt

# Lub użyj skryptu setup
python setup.py
```

### 2. Konfiguracja modeli

Edytuj plik `models.csv` aby skonfigurować swoje modele:

```csv
model_name,url,auth_header,auth_value,think,description
deepseek-coder:1.3b,http://192.168.188.108:8081/api/chat,,,false,DeepSeek Coder na lokalnym serwerze
mistral:latest,http://192.168.188.212:11434/api/chat,,,false,Mistral Latest na Ollama
gpt-4,https://api.openai.com/v1/chat/completions,Authorization,Bearer sk-...,false,OpenAI GPT-4
```

**Kolumny w CSV:**
- `model_name` - nazwa modelu
- `url` - endpoint API
- `auth_header` - nagłówek autoryzacji (opcjonalny)
- `auth_value` - wartość autoryzacji (opcjonalny)
- `think` - czy model obsługuje parametr "think" (true/false)
- `description` - opis modelu

### 3. Uruchomienie testów

```bash
# Podstawowe testy wszystkich modeli
python main.py

# Zaawansowane opcje
python test_runner.py --benchmark

# Test pojedynczego modelu
python test_runner.py --single-model "deepseek-coder:1.3b"

# Porównanie określonych modeli
python test_runner.py --compare "mistral:latest" "deepseek-coder:1.3b"
```

## 📊 Metryki Oceny

System ocenia wygenerowany kod według następujących kryteriów:

### Podstawowe metryki (automatyczne)
- ✅ **Składnia poprawna** - czy kod kompiluje się bez błędów
- ✅ **Wykonalność** - czy kod uruchamia się bez błędów runtime
- ✅ **Słowa kluczowe** - czy kod zawiera oczekiwane elementy z promptu

### Metryki jakości kodu
- 📝 **Definicje funkcji/klas** - poprawna struktura kodu
- 🛡️ **Obsługa błędów** - try/catch, walidacja inputów
- 📚 **Dokumentacja** - docstringi, komentarze
- 📦 **Importy** - właściwe użycie bibliotek
- 📏 **Długość kodu** - rozsądna ilość linii

### System punktowy
- Składnia poprawna: **3 punkty**
- Wykonuje się bez błędów: **2 punkty**  
- Zawiera oczekiwane elementy: **2 punkty**
- Ma definicje funkcji/klas: **1 punkt**
- Ma obsługę błędów: **1 punkt**
- Ma dokumentację: **1 punkt**
- **Maksymalnie: 10 punktów**

## 🔧 Konfiguracja

### Dostosowanie promptów

Edytuj plik `config.py` aby zmienić prompty testowe:

```python
TEST_PROMPTS = [
    {
        "name": "Custom Function",
        "prompt": "Write a Python function that...",
        "expected_keywords": ["def", "function_name"],
        "expected_behavior": "function_definition"
    }
]
```

### Własna konfiguracja JSON

# Test wszystkich modeli Ollama na lokalnym serwerze
python test_runner.py --models ollama_models.csv

# Porównanie tylko modeli kodujących
python test_runner.py --compare "deepseek-coder:1.3b" "codellama:7b" --output coding_models_comparison.html

# Szybki test pojedynczego modelu z jednym promptem
python test_runner.py --single-model "mistral:latest" --prompt-index 0 --output quick_test.html
```

## 🔌 Integracja z Różnymi API

### Ollama (lokalny)
```csv
llama3.2:3b,http://localhost:11434/api/chat,,,false,Llama 3.2
```

### OpenAI API
```csv
gpt-4,https://api.openai.com/v1/chat/completions,Authorization,Bearer sk-your-key,false,OpenAI GPT-4
```

### Anthropic Claude
```csv
claude-3,https://api.anthropic.com/v1/messages,x-api-key,your-key,false,Claude 3
```

### Lokalny serwer
```csv
local-model,http://192.168.1.100:8080/generate,,,false,Lokalny model
```

## 📁 Struktura Projek