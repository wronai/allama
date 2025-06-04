#!/usr/bin/env python3
"""
TestLLM - System do testowania i porównywania modeli LLM w kontekście generowania kodu
"""

import csv
import json
import requests
import time
import ast
import subprocess
import tempfile
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple
import logging

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CodeEvaluator:
    """Klasa do oceny wygenerowanego kodu"""

    def __init__(self):
        self.metrics = {
            'syntax_valid': 0,
            'runs_without_error': 0,
            'has_function_def': 0,
            'has_docstring': 0,
            'has_error_handling': 0,
            'imports_used': 0,
            'line_count': 0,
            'response_time': 0,
            'contains_expected_keywords': 0
        }

    def extract_python_code(self, response_text: str) -> str:
        """Wyciąga kod Python z odpowiedzi modelu"""
        # Szuka bloków kodu między ```python i ```
        if '```python' in response_text:
            start = response_text.find('```python') + 9
            end = response_text.find('```', start)
            if end != -1:
                return response_text[start:end].strip()

        # Szuka bloków kodu między ``` i ```
        if '```' in response_text:
            parts = response_text.split('```')
            for i, part in enumerate(parts):
                if i % 2 == 1:  # Nieparzysty indeks = kod
                    # Usuwa pierwszą linię jeśli zawiera nazwę języka
                    lines = part.strip().split('\n')
                    if lines and any(lang in lines[0].lower() for lang in ['python', 'py']):
                        return '\n'.join(lines[1:]).strip()
                    return part.strip()

        # Jeśli nie ma bloków kodu, zwraca całą odpowiedź
        return response_text.strip()

    def check_syntax(self, code: str) -> bool:
        """Sprawdza poprawność składni kodu Python"""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def check_execution(self, code: str) -> Tuple[bool, str]:
        """Sprawdza czy kod można wykonać bez błędów"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name

            # Wykonuje kod w subprocesie
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )

            os.unlink(temp_file)

            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr

        except subprocess.TimeoutExpired:
            return False, "Timeout - kod wykonywał się zbyt długo"
        except Exception as e:
            return False, str(e)

    def analyze_code_quality(self, code: str) -> Dict[str, Any]:
        """Analizuje jakość kodu"""
        metrics = {}

        # Podstawowe metryki
        metrics['line_count'] = len([line for line in code.split('\n') if line.strip()])
        metrics['has_function_def'] = 'def ' in code
        metrics['has_class_def'] = 'class ' in code
        metrics['has_docstring'] = '"""' in code or "'''" in code
        metrics['has_comments'] = '#' in code
        metrics['has_error_handling'] = any(keyword in code for keyword in ['try:', 'except:', 'raise', 'assert'])
        metrics['imports_used'] = code.count('import ') + code.count('from ')

        return metrics

    def evaluate_code(self, code: str, prompt: str, response_time: float) -> Dict[str, Any]:
        """Kompleksowa ocena wygenerowanego kodu"""
        results = {
            'code': code,
            'response_time': response_time,
            'syntax_valid': False,
            'runs_without_error': False,
            'execution_output': '',
            'quality_metrics': {}
        }

        # Sprawdź składnię
        results['syntax_valid'] = self.check_syntax(code)

        # Sprawdź wykonanie
        if results['syntax_valid']:
            can_run, output = self.check_execution(code)
            results['runs_without_error'] = can_run
            results['execution_output'] = output

        # Analiza jakości
        results['quality_metrics'] = self.analyze_code_quality(code)

        # Sprawdź czy kod zawiera oczekiwane słowa kluczowe z promptu
        prompt_keywords = ['function', 'class', 'password', 'hash', 'bcrypt', 'user', 'animation']
        code_lower = code.lower()
        prompt_lower = prompt.lower()

        relevant_keywords = [kw for kw in prompt_keywords if kw in prompt_lower]
        found_keywords = [kw for kw in relevant_keywords if kw in code_lower]

        results['contains_expected_keywords'] = len(found_keywords) > 0 if relevant_keywords else True
        results['keyword_match_ratio'] = len(found_keywords) / len(relevant_keywords) if relevant_keywords else 1.0

        return results


class LLMTester:
    """Główna klasa do testowania modeli LLM"""

    def __init__(self, models_file: str = 'models.csv'):
        self.models_file = models_file
        self.evaluator = CodeEvaluator()
        self.results = []
        self.test_prompts = [
            "Write a Python function that adds two numbers and returns the result",
            "Create a Python class for a User with name and email attributes",
            "Write a Python function that securely hashes passwords using bcrypt",
            "Create a simple animation in Python using time.sleep",
            "Write a Python function to read a CSV file and return data as a list of dictionaries"
        ]

    def load_models(self) -> List[Dict[str, str]]:
        """Ładuje listę modeli z pliku CSV"""
        models = []
        try:
            with open(self.models_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    models.append(row)
            logger.info(f"Załadowano {len(models)} modeli z {self.models_file}")
        except FileNotFoundError:
            logger.error(f"Plik {self.models_file} nie został znaleziony")
        except Exception as e:
            logger.error(f"Błąd podczas ładowania modeli: {e}")

        return models

    def make_request(self, model_config: Dict[str, str], prompt: str) -> Tuple[str, float, bool]:
        """Wykonuje zapytanie do modelu LLM"""
        start_time = time.time()

        try:
            headers = {'Content-Type': 'application/json'}

            # Dodaj autoryzację jeśli jest dostępna
            if model_config.get('auth_header') and model_config.get('auth_value'):
                headers[model_config['auth_header']] = model_config['auth_value']

            # Przygotuj dane do zapytania
            data = {
                "model": model_config['model_name'],
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            }

            # Dodaj specjalne parametry jeśli są dostępne
            if model_config.get('think') == 'true':
                data['think'] = True

            response = requests.post(
                model_config['url'],
                headers=headers,
                json=data,
                timeout=60
            )

            response_time = time.time() - start_time

            if response.status_code == 200:
                response_data = response.json()

                # Wyciąg odpowiedzi w zależności od formatu
                if 'message' in response_data and 'content' in response_data['message']:
                    content = response_data['message']['content']
                elif 'response' in response_data:
                    content = response_data['response']
                else:
                    content = str(response_data)

                return content, response_time, True
            else:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                return f"Error: HTTP {response.status_code}", response_time, False

        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            return "Error: Request timeout", response_time, False
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Błąd podczas zapytania: {e}")
            return f"Error: {str(e)}", response_time, False

    def test_model(self, model_config: Dict[str, str], prompt: str) -> Dict[str, Any]:
        """Testuje pojedynczy model z pojedynczym promptem"""
        logger.info(f"Testuję model {model_config['model_name']} z promptem: {prompt[:50]}...")

        # Wykonaj zapytanie
        response_text, response_time, success = self.make_request(model_config, prompt)

        if not success:
            return {
                'model_name': model_config['model_name'],
                'url': model_config['url'],
                'prompt': prompt,
                'success': False,
                'error': response_text,
                'response_time': response_time
            }

        # Wyciągnij kod z odpowiedzi
        code = self.evaluator.extract_python_code(response_text)

        # Oceń kod
        evaluation = self.evaluator.evaluate_code(code, prompt, response_time)

        return {
            'model_name': model_config['model_name'],
            'url': model_config['url'],
            'prompt': prompt,
            'success': True,
            'raw_response': response_text,
            'extracted_code': code,
            'evaluation': evaluation
        }

    def run_tests(self):
        """Uruchamia wszystkie testy"""
        models = self.load_models()

        if not models:
            logger.error("Brak modeli do testowania")
            return

        logger.info(f"Rozpoczynam testowanie {len(models)} modeli z {len(self.test_prompts)} promptami")

        for model in models:
            for prompt in self.test_prompts:
                result = self.test_model(model, prompt)
                self.results.append(result)

                # Krótka przerwa między zapytaniami
                time.sleep(1)

        logger.info(f"Zakończono testowanie. Zebrano {len(self.results)} wyników")

    def generate_html_report(self, output_file: str = 'llm_test_results.html'):
        """Generuje raport HTML z wynikami"""
        if not self.results:
            logger.error("Brak wyników do wygenerowania raportu")
            return

        html_content = self._create_html_report()

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"Raport HTML zapisany do {output_file}")
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania raportu: {e}")

    def _create_html_report(self) -> str:
        """Tworzy zawartość raportu HTML"""
        # Agreguj statystyki
        stats = self._calculate_statistics()

        html = f"""
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Raport Testowania Modeli LLM</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
        h1, h2 {{ color: #333; }}
        .summary {{ background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .model-results {{ margin: 20px 0; border: 1px solid #ddd; border-radius: 5px; }}
        .model-header {{ background: #f8f9fa; padding: 10px; border-bottom: 1px solid #ddd; }}
        .prompt-result {{ padding: 15px; border-bottom: 1px solid #eee; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 10px 0; }}
        .metric {{ background: #f8f9fa; padding: 8px; border-radius: 3px; text-align: center; }}
        .code-block {{ background: #f4f4f4; padding: 10px; border-radius: 3px; font-family: monospace; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }}
        .success {{ color: #28a745; }}
        .error {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .score {{ font-weight: bold; font-size: 1.2em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Raport Testowania Modeli LLM</h1>
        <p><strong>Data generowania:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="summary">
            <h2>📊 Podsumowanie</h2>
            <div class="metrics">
                <div class="metric">
                    <strong>Testowane modele:</strong><br>
                    {len(stats['models'])}
                </div>
                <div class="metric">
                    <strong>Liczba testów:</strong><br>
                    {len(self.results)}
                </div>
                <div class="metric">
                    <strong>Testy zakończone sukcesem:</strong><br>
                    {stats['successful_tests']} ({stats['success_rate']:.1f}%)
                </div>
                <div class="metric">
                    <strong>Średni czas odpowiedzi:</strong><br>
                    {stats['avg_response_time']:.2f}s
                </div>
            </div>
        </div>

        <h2>🏆 Ranking Modeli</h2>
        {self._generate_ranking_table(stats)}

        <h2>📋 Szczegółowe Wyniki</h2>
"""

        # Grupuj wyniki według modeli
        models_results = {}
        for result in self.results:
            model_name = result['model_name']
            if model_name not in models_results:
                models_results[model_name] = []
            models_results[model_name].append(result)

        # Generuj sekcje dla każdego modelu
        for model_name, results in models_results.items():
            html += self._generate_model_section(model_name, results)

        html += """
    </div>
</body>
</html>
"""
        return html

    def _calculate_statistics(self) -> Dict[str, Any]:
        """Oblicza statystyki z wyników"""
        successful_tests = sum(1 for r in self.results if r['success'])
        models = set(r['model_name'] for r in self.results)

        # Oblicz średni czas odpowiedzi
        response_times = [r['response_time'] for r in self.results if r['success']]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        # Oblicz wyniki dla każdego modelu
        model_scores = {}
        for model in models:
            model_results = [r for r in self.results if r['model_name'] == model and r['success']]
            if model_results:
                scores = []
                for result in model_results:
                    if 'evaluation' in result:
                        eval_data = result['evaluation']
                        score = 0
                        if eval_data.get('syntax_valid'): score += 2
                        if eval_data.get('runs_without_error'): score += 2
                        if eval_data.get('contains_expected_keywords'): score += 1
                        if eval_data.get('quality_metrics', {}).get('has_function_def'): score += 1
                        if eval_data.get('quality_metrics', {}).get('has_error_handling'): score += 1
                        if eval_data.get('quality_metrics', {}).get('has_docstring'): score += 1
                        scores.append(score)

                model_scores[model] = {
                    'avg_score': sum(scores) / len(scores) if scores else 0,
                    'success_rate': len(model_results) / len(
                        [r for r in self.results if r['model_name'] == model]) * 100,
                    'avg_response_time': sum(r['response_time'] for r in model_results) / len(model_results)
                }

        return {
            'models': models,
            'successful_tests': successful_tests,
            'success_rate': successful_tests / len(self.results) * 100 if self.results else 0,
            'avg_response_time': avg_response_time,
            'model_scores': model_scores
        }

    def _generate_ranking_table(self, stats: Dict[str, Any]) -> str:
        """Generuje tabelę rankingu modeli"""
        model_scores = stats['model_scores']
        sorted_models = sorted(model_scores.items(), key=lambda x: x[1]['avg_score'], reverse=True)

        html = """
        <table>
            <tr>
                <th>Pozycja</th>
                <th>Model</th>
                <th>Średni Wynik</th>
                <th>Wskaźnik Sukcesu</th>
                <th>Średni Czas Odpowiedzi</th>
            </tr>
"""

        for i, (model, data) in enumerate(sorted_models, 1):
            html += f"""
            <tr>
                <td>{i}</td>
                <td>{model}</td>
                <td class="score">{data['avg_score']:.1f}/8</td>
                <td>{data['success_rate']:.1f}%</td>
                <td>{data['avg_response_time']:.2f}s</td>
            </tr>
"""

        html += "</table>"
        return html

    def _generate_model_section(self, model_name: str, results: List[Dict[str, Any]]) -> str:
        """Generuje sekcję HTML dla pojedynczego modelu"""
        html = f"""
        <div class="model-results">
            <div class="model-header">
                <h3>🤖 {model_name}</h3>
                <p><strong>URL:</strong> {results[0]['url']}</p>
            </div>
"""

        for result in results:
            status_class = "success" if result['success'] else "error"
            status_text = "✅ Sukces" if result['success'] else "❌ Błąd"

            html += f"""
            <div class="prompt-result">
                <h4>{status_text} - {result['prompt'][:60]}...</h4>
                <p><strong>Czas odpowiedzi:</strong> {result['response_time']:.2f}s</p>
"""

            if result['success'] and 'evaluation' in result:
                eval_data = result['evaluation']
                html += f"""
                <div class="metrics">
                    <div class="metric">
                        <strong>Składnia poprawna:</strong><br>
                        {"✅" if eval_data.get('syntax_valid') else "❌"}
                    </div>
                    <div class="metric">
                        <strong>Wykonuje się bez błędów:</strong><br>
                        {"✅" if eval_data.get('runs_without_error') else "❌"}
                    </div>
                    <div class="metric">
                        <strong>Zawiera słowa kluczowe:</strong><br>
                        {"✅" if eval_data.get('contains_expected_keywords') else "❌"}
                    </div>
                    <div class="metric">
                        <strong>Liczba linii:</strong><br>
                        {eval_data.get('quality_metrics', {}).get('line_count', 0)}
                    </div>
                </div>

                <h5>📄 Wygenerowany kod:</h5>
                <div class="code-block">{result['extracted_code']}</div>
"""

                if eval_data.get('execution_output'):
                    html += f"""
                <h5>🖥️ Wynik wykonania:</h5>
                <div class="code-block">{eval_data['execution_output']}</div>
"""
            else:
                html += f"""<p class="error"><strong>Błąd:</strong> {result.get('error', 'Nieznany błąd')}</p>"""

            html += "</div>"

        html += "</div>"
        return html


def main():
    """Główna funkcja programu"""
    logger.info("Uruchamianie TestLLM...")

    tester = LLMTester('models.csv')
    tester.run_tests()
    tester.generate_html_report('llm_test_results.html')

    logger.info("Testowanie zakończone! Sprawdź plik llm_test_results.html")


if __name__ == "__main__":
    main()