#!/usr/bin/env python3
"""
Zaawansowany runner testów dla TestLLM z dodatkowymi funkcjami
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any
import logging

from allama.main import LLMTester
from allama.config import TEST_PROMPTS, EVALUATION_WEIGHTS, TIMEOUTS

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('testllm.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class AdvancedLLMTester(LLMTester):
    """Rozszerzona wersja testera z dodatkowymi funkcjami"""

    def __init__(self, models_file: str = 'models.csv', config_file: str = None):
        super().__init__(models_file)
        self.config_file = config_file
        self.load_custom_config()

    def load_custom_config(self):
        """Ładuje niestandardową konfigurację z pliku JSON"""
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                # Zastąp domyślne prompty jeśli są w konfiguracji
                if 'test_prompts' in config:
                    self.test_prompts = [p['prompt'] for p in config['test_prompts']]
                    logger.info(f"Załadowano {len(self.test_prompts)} promptów z konfiguracji")

                # Aktualizuj inne ustawienia
                if 'timeouts' in config:
                    TIMEOUTS.update(config['timeouts'])

            except Exception as e:
                logger.error(f"Błąd podczas ładowania konfiguracji: {e}")
        else:
            # Użyj promptów z config.py
            self.test_prompts = [p['prompt'] for p in TEST_PROMPTS]

    def run_single_model_test(self, model_name: str, prompt_index: int = None):
        """Testuje pojedynczy model z opcjonalnym pojedynczym promptem"""
        models = self.load_models()
        target_model = next((m for m in models if m['model_name'] == model_name), None)

        if not target_model:
            logger.error(f"Model {model_name} nie został znaleziony w pliku konfiguracji")
            return

        prompts_to_test = [self.test_prompts[prompt_index]] if prompt_index is not None else self.test_prompts

        logger.info(f"Testowanie modelu {model_name} z {len(prompts_to_test)} promptami")

        for prompt in prompts_to_test:
            result = self.test_model(target_model, prompt)
            self.results.append(result)

    def run_benchmark_suite(self):
        """Uruchamia standardowy zestaw testów benchmarkowych"""
        logger.info("🏁 Uruchamianie zestawu testów benchmarkowych...")

        # Wyczyść poprzednie wyniki
        self.results = []

        # Uruchom testy
        self.run_tests()

        # Generuj szczegółowy raport
        self.generate_detailed_report()

        # Generuj podsumowanie CSV
        self.export_results_to_csv()

    def generate_detailed_report(self):
        """Generuje szczegółowy raport z dodatkowymi metrykami"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_file = f'llm_benchmark_report_{timestamp}.html'

        # Standardowy raport HTML
        self.generate_html_report(html_file)

        # Dodatkowy raport JSON z surowymi danymi
        json_file = f'llm_results_raw_{timestamp}.json'
        self.export_raw_results_to_json(json_file)

        logger.info(f"Szczegółowe raporty wygenerowane: {html_file}, {json_file}")

    def export_results_to_csv(self):
        """Eksportuje wyniki do pliku CSV dla łatwej analizy"""
        import csv

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_file = f'llm_results_summary_{timestamp}.csv'

        try:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Nagłówki
                headers = [
                    'model_name', 'prompt', 'success', 'response_time',
                    'syntax_valid', 'runs_without_error', 'contains_keywords',
                    'has_function_def', 'has_error_handling', 'has_docstring',
                    'line_count', 'overall_score'
                ]
                writer.writerow(headers)

                # Dane
                for result in self.results:
                    if result['success']:
                        eval_data = result.get('evaluation', {})
                        quality_metrics = eval_data.get('quality_metrics', {})

                        # Oblicz ogólny wynik
                        score = 0
                        if eval_data.get('syntax_valid'): score += 3
                        if eval_data.get('runs_without_error'): score += 2
                        if eval_data.get('contains_expected_keywords'): score += 2
                        if quality_metrics.get('has_function_def'): score += 1
                        if quality_metrics.get('has_error_handling'): score += 1
                        if quality_metrics.get('has_docstring'): score += 1

                        row = [
                            result['model_name'],
                            result['prompt'][:50] + '...' if len(result['prompt']) > 50 else result['prompt'],
                            result['success'],
                            result['response_time'],
                            eval_data.get('syntax_valid', False),
                            eval_data.get('runs_without_error', False),
                            eval_data.get('contains_expected_keywords', False),
                            quality_metrics.get('has_function_def', False),
                            quality_metrics.get('has_error_handling', False),
                            quality_metrics.get('has_docstring', False),
                            quality_metrics.get('line_count', 0),
                            score
                        ]
                    else:
                        row = [
                            result['model_name'],
                            result['prompt'][:50] + '...' if len(result['prompt']) > 50 else result['prompt'],
                            False,
                            result['response_time'],
                            False, False, False, False, False, False, 0, 0
                        ]

                    writer.writerow(row)

            logger.info(f"Wyniki wyeksportowane do CSV: {csv_file}")

        except Exception as e:
            logger.error(f"Błąd podczas eksportu do CSV: {e}")

    def export_raw_results_to_json(self, filename: str):
        """Eksportuje surowe wyniki do pliku JSON"""
        try:
            export_data = {
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'total_tests': len(self.results),
                    'models_tested': len(set(r['model_name'] for r in self.results)),
                    'prompts_used': len(set(r['prompt'] for r in self.results))
                },
                'results': self.results
            }

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Surowe wyniki wyeksportowane do JSON: {filename}")

        except Exception as e:
            logger.error(f"Błąd podczas eksportu do JSON: {e}")

    def compare_models(self, model_names: List[str], output_file: str = None):
        """Porównuje określone modele i generuje raport porównawczy"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'model_comparison_{timestamp}.html'

        # Filtruj wyniki dla określonych modeli
        filtered_results = [r for r in self.results if r['model_name'] in model_names]

        if not filtered_results:
            logger.error("Brak wyników dla określonych modeli")
            return

        # Generuj raport porównawczy
        html_content = self._generate_comparison_report(filtered_results, model_names)

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"Raport porównawczy zapisany do: {output_file}")
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania raportu porównawczego: {e}")

    def _generate_comparison_report(self, results: List[Dict], model_names: List[str]) -> str:
        """Generuje HTML dla raportu porównawczego"""
        # Oblicz statystyki dla każdego modelu
        model_stats = {}
        for model in model_names:
            model_results = [r for r in results if r['model_name'] == model]
            if model_results:
                successful = [r for r in model_results if r['success']]

                scores = []
                for result in successful:
                    if 'evaluation' in result:
                        eval_data = result['evaluation']
                        score = 0
                        if eval_data.get('syntax_valid'): score += 3
                        if eval_data.get('runs_without_error'): score += 2
                        if eval_data.get('contains_expected_keywords'): score += 2
                        if eval_data.get('quality_metrics', {}).get('has_function_def'): score += 1
                        if eval_data.get('quality_metrics', {}).get('has_error_handling'): score += 1
                        if eval_data.get('quality_metrics', {}).get('has_docstring'): score += 1
                        scores.append(score)

                model_stats[model] = {
                    'total_tests': len(model_results),
                    'successful_tests': len(successful),
                    'success_rate': len(successful) / len(model_results) * 100,
                    'avg_score': sum(scores) / len(scores) if scores else 0,
                    'avg_response_time': sum(r['response_time'] for r in successful) / len(
                        successful) if successful else 0
                }

        # Generuj HTML
        html = f"""
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>Porównanie Modeli LLM</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .comparison-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .comparison-table th, .comparison-table td {{ border: 1px solid #ddd; padding: 12px; text-align: center; }}
        .comparison-table th {{ background-color: #f2f2f2; }}
        .best {{ background-color: #d4edda; font-weight: bold; }}
        .chart {{ margin: 20px 0; }}
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
</head>
<body>
    <h1>📊 Porównanie Modeli LLM</h1>
    <p><strong>Data:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <h2>🏆 Tabela Porównawcza</h2>
    <table class="comparison-table">
        <tr>
            <th>Model</th>
            <th>Liczba Testów</th>
            <th>Testy Udane</th>
            <th>Wskaźnik Sukcesu (%)</th>
            <th>Średni Wynik</th>
            <th>Średni Czas Odpowiedzi (s)</th>
        </tr>
"""

        # Znajdź najlepsze wyniki dla podświetlenia
        best_success_rate = max(stats['success_rate'] for stats in model_stats.values())
        best_avg_score = max(stats['avg_score'] for stats in model_stats.values())
        best_response_time = min(
            stats['avg_response_time'] for stats in model_stats.values() if stats['avg_response_time'] > 0)

        for model, stats in model_stats.items():
            success_class = "best" if stats['success_rate'] == best_success_rate else ""
            score_class = "best" if stats['avg_score'] == best_avg_score else ""
            time_class = "best" if stats['avg_response_time'] == best_response_time else ""

            html += f"""
        <tr>
            <td><strong>{model}</strong></td>
            <td>{stats['total_tests']}</td>
            <td>{stats['successful_tests']}</td>
            <td class="{success_class}">{stats['success_rate']:.1f}%</td>
            <td class="{score_class}">{stats['avg_score']:.1f}/10</td>
            <td class="{time_class}">{stats['avg_response_time']:.2f}s</td>
        </tr>
"""

        html += """
    </table>

    <h2>📈 Wykres Porównawczy</h2>
    <div class="chart">
        <canvas id="comparisonChart" width="400" height="200"></canvas>
    </div>

    <script>
        const ctx = document.getElementById('comparisonChart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'radar',
            data: {
"""

        # Dane dla wykresu radarowego
        html += f"labels: ['Wskaźnik Sukcesu', 'Średni Wynik', 'Szybkość (odwrócona)'],"
        html += "datasets: ["

        colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
        for i, (model, stats) in enumerate(model_stats.items()):
            color = colors[i % len(colors)]
            # Normalizuj szybkość (mniejszy czas = lepiej, więc odwracamy)
            speed_score = 100 - min(stats['avg_response_time'] * 10, 100) if stats['avg_response_time'] > 0 else 100

            html += f"""
                {{
                    label: '{model}',
                    data: [{stats['success_rate']}, {stats['avg_score'] * 10}, {speed_score}],
                    borderColor: '{color}',
                    backgroundColor: '{color}33',
                    pointBackgroundColor: '{color}',
                }},"""

        html += """
            ]
        },
        options: {
            responsive: true,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
    </script>
</body>
</html>
"""

        return html


def main():
    """Główna funkcja z argumentami wiersza poleceń"""
    parser = argparse.ArgumentParser(description='TestLLM - Zaawansowany tester modeli LLM')
    parser.add_argument('--models', '-m', default='models.csv', help='Plik CSV z konfiguracją modeli')
    parser.add_argument('--config', '-c', help='Plik JSON z niestandardową konfiguracją')
    parser.add_argument('--single-model', help='Testuj tylko określony model')
    parser.add_argument('--prompt-index', type=int, help='Indeks pojedynczego promptu do testowania (0-based)')
    parser.add_argument('--benchmark', action='store_true', help='Uruchom pełny zestaw testów benchmarkowych')
    parser.add_argument('--compare', nargs='+', help='Porównaj określone modele')
    parser.add_argument('--output', '-o', help='Nazwa pliku wyjściowego')
    parser.add_argument('--verbose', '-v', action='store_true', help='Szczegółowe logowanie')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Inicjalizuj tester
    tester = AdvancedLLMTester(args.models, args.config)

    try:
        if args.single_model:
            # Test pojedynczego modelu
            tester.run_single_model_test(args.single_model, args.prompt_index)
            output_file = args.output or f'single_model_test_{args.single_model.replace(":", "_")}.html'
            tester.generate_html_report(output_file)

        elif args.benchmark:
            # Pełny benchmark
            tester.run_benchmark_suite()

        elif args.compare:
            # Najpierw uruchom testy jeśli nie ma wyników
            if not tester.results:
                tester.run_tests()

            # Porównaj modele
            output_file = args.output or 'model_comparison.html'
            tester.compare_models(args.compare, output_file)

        else:
            # Standardowe testy
            tester.run_tests()
            output_file = args.output or 'llm_test_results.html'
            tester.generate_html_report(output_file)

        logger.info("✅ Testowanie zakończone pomyślnie!")

    except KeyboardInterrupt:
        logger.info("⏹️  Testowanie przerwane przez użytkownika")
    except Exception as e:
        logger.error(f"❌ Błąd podczas testowania: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()