#!/usr/bin/env python3
"""
Konfiguracja dla TestLLM
"""

# Prompty do testowania modeli - zaprojektowane tak, aby generowały przewidywalny kod
TEST_PROMPTS = [
    {
        "name": "Simple Addition Function",
        "prompt": "Write a Python function called 'add_numbers' that takes two parameters (a, b) and returns their sum. Include a docstring and a simple test call.",
        "expected_keywords": ["def", "add_numbers", "return", "a", "b"],
        "expected_behavior": "function_definition"
    },
    {
        "name": "User Class",
        "prompt": "Create a Python class called 'User' with __init__ method that accepts name and email parameters. Add a method called 'get_info' that returns a formatted string with user information.",
        "expected_keywords": ["class", "User", "__init__", "name", "email", "get_info"],
        "expected_behavior": "class_definition"
    },
    {
        "name": "Password Hashing",
        "prompt": "Write a Python function called 'hash_password' that takes a password string and returns a hashed version. Use hashlib library with sha256. Include error handling for empty passwords.",
        "expected_keywords": ["def", "hash_password", "hashlib", "sha256", "encode"],
        "expected_behavior": "function_with_imports"
    },
    {
        "name": "CSV Reader",
        "prompt": "Write a Python function called 'read_csv_file' that takes a filename parameter and returns a list of dictionaries. Use the csv module and include basic error handling for file not found.",
        "expected_keywords": ["def", "read_csv_file", "csv", "DictReader", "try", "except"],
        "expected_behavior": "function_with_error_handling"
    },
    {
        "name": "Simple Calculator",
        "prompt": "Create a Python class called 'Calculator' with methods: add, subtract, multiply, divide. Each method should take two numbers and return the result. Include division by zero protection.",
        "expected_keywords": ["class", "Calculator", "add", "subtract", "multiply", "divide"],
        "expected_behavior": "class_with_methods"
    }
]

# Konfiguracja oceny kodu
EVALUATION_WEIGHTS = {
    "syntax_valid": 3.0,           # Najważniejsze - kod musi się kompilować
    "runs_without_error": 2.5,     # Kod musi się wykonywać
    "contains_expected_keywords": 2.0,  # Kod zawiera oczekiwane elementy
    "has_function_def": 1.5,       # Definicja funkcji/klasy
    "has_error_handling": 1.0,     # Obsługa błędów
    "has_docstring": 1.0,          # Dokumentacja
    "has_imports": 0.5,            # Właściwe importy
    "code_length_reasonable": 0.5   # Rozsądna długość kodu
}

# Limity czasowe
TIMEOUTS = {
    "request_timeout": 60,    # Timeout dla zapytania HTTP (sekundy)
    "execution_timeout": 10,  # Timeout dla wykonania kodu (sekundy)
    "delay_between_requests": 1  # Opóźnienie między zapytaniami (sekundy)
}

# Konfiguracja raportu HTML
REPORT_CONFIG = {
    "title": "Raport Testowania Modeli LLM - Generowanie Kodu",
    "include_raw_responses": True,
    "include_execution_output": True,
    "max_code_display_lines": 50,
    "show_detailed_metrics": True
}

# Kolory dla raportu HTML
COLORS = {
    "success": "#28a745",
    "error": "#dc3545",
    "warning": "#ffc107",
    "info": "#17a2b8",
    "primary": "#007bff",
    "light": "#f8f9fa",
    "dark": "#343a40"
}