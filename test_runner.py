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
from allama.config_loader import get_config
from allama.open_report import open_report_in_browser
from allama.report_generator import ReportGenerator
from allama.publisher import ResultPublisher

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

    def __init__(self, models_file: str = 'models.csv', config_path: str = None):
        super().__init__(models_file, config_path)

    def load_prompts(self):
        """Ładuje prompty z pliku JSON"""
        try:
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                prompts = json.load(f)
                logger.info(f"Załadowano {len(prompts)} promptów z {self.prompts_file}")
                return prompts
        except FileNotFoundError:
            logger.error(f"Plik z promptami nie został znaleziony: {self.prompts_file}")
            return []
        except Exception as e:
            logger.error(f"Błąd podczas ładowania promptów: {e}")
            return []

    def load_custom_config(self):
        """Ładuje niestandardową konfigurację z pliku JSON"""
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                # Zastąp domyślne prompty jeśli są w konfiguracji
                if 'test_prompts' in config:
                    self.test_prompts = config['test_prompts']
                    logger.info(f"Załadowano {len(self.test_prompts)} promptów z pliku konfiguracyjnego {self.config_file}")

                # Aktualizuj inne ustawienia
                if 'timeouts' in config:
                    TIMEOUTS.update(config['timeouts'])

            except Exception as e:
                logger.error(f"Błąd podczas ładowania konfiguracji: {e}")
        else:
            # Użyj promptów z pliku JSON
            pass

    def run_single_model_test(self, model_name: str, prompt_index: int = None):
        """Testuje pojedynczy model z opcjonalnym pojedynczym promptem"""
        models = self.load_models()
        target_model = next((m for m in models if m['model_name'] == model_name), None)

        if not target_model:
            logger.error(f"Model {model_name} nie został znaleziony w pliku konfiguracji")
            return

        prompts_to_test = [self.test_prompts[prompt_index]] if prompt_index is not None and self.test_prompts else self.test_prompts

        logger.info(f"Testowanie modelu {model_name} z {len(prompts_to_test)} promptami")

        for prompt in prompts_to_test:
            result = self.test_model(target_model, prompt)
            self.results.append(result)

    def run_benchmark_suite(self):
        """Uruchamia standardowy zestaw testów benchmarkowych"""
        logger.info(" Uruchamianie zestawu testów benchmarkowych...")

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

    def compare_models(self, model_names: List[str], output_file: str = None, json_output: str = None):
        """Porównuje określone modele i generuje raport porównawczy"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'model_comparison_{timestamp}.html'
            
        if not json_output:
            json_output = output_file.replace('.html', '.json')

        # Filtruj wyniki dla określonych modeli
        filtered_results = [r for r in self.results if r['model_name'] in model_names]

        if not filtered_results:
            logger.error("Brak wyników dla określonych modeli")
            return

        # Zapisz wyniki do pliku JSON
        try:
            with open(json_output, 'w', encoding='utf-8') as f:
                json.dump(filtered_results, f, indent=2)
            logger.info(f"Wyniki porównania zapisane do JSON: {json_output}")
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania wyników do JSON: {e}")

        # Generuj raport porównawczy HTML używając ReportGenerator
        report_generator = ReportGenerator(self.config)
        report_generator.generate_html_report(filtered_results, output_file=output_file, json_file=json_output)
        logger.info(f"Raport porównawczy zapisany do: {output_file}")


def main():
    """Główna funkcja z argumentami wiersza poleceń"""
    parser = argparse.ArgumentParser(description='TestLLM - Zaawansowany tester modeli LLM')
    parser.add_argument('--models', '-m', default='models.csv', help='Plik CSV z konfiguracją modeli')
    parser.add_argument('--config', '-c', help='Plik JSON z niestandardową konfiguracją (JSON lub YAML)')
    parser.add_argument('--single-model', help='Testuj tylko określony model')
    parser.add_argument('--prompt-index', type=int, help='Indeks pojedynczego promptu do testowania (0-based)')
    parser.add_argument('--benchmark', action='store_true', help='Uruchom pełny zestaw testów benchmarkowych')
    parser.add_argument('--compare', nargs='+', help='Porównaj określone modele')
    parser.add_argument('--output', '-o', help='Nazwa pliku wyjściowego HTML')
    parser.add_argument('--json-output', help='Nazwa pliku wyjściowego JSON')
    parser.add_argument('--verbose', '-v', action='store_true', help='Szczegółowe logowanie')
    parser.add_argument('--no-browser', action='store_true', help='Nie otwieraj automatycznie raportu w przeglądarce')
    parser.add_argument('--publish', action='store_true', help='Publikuj wyniki na serwerze')
    parser.add_argument('--server-url', default='https://allama.sapletta.com/upload.php', 
                      help='URL serwera do publikowania wyników')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Inicjalizuj tester
    tester = AdvancedLLMTester(args.models, args.config)

    try:
        output_file = None
        json_output = None
        
        if args.single_model:
            # Test pojedynczego modelu
            tester.run_single_model_test(args.single_model, args.prompt_index)
            output_file = args.output or f'allama.html'
            json_output = args.json_output or 'allama.json'
            tester.generate_html_report(output_file, json_output)

        elif args.benchmark:
            # Pełny benchmark
            tester.run_benchmark_suite()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = args.output or 'allama.html'
            json_output = args.json_output or 'allama.json'
            tester.generate_html_report(output_file, json_output)

        elif args.compare:
            # Najpierw uruchom testy jeśli nie ma wyników
            if not tester.results:
                tester.run_tests()

            # Porównaj modele
            output_file = args.output or 'allama.html'
            json_output = args.json_output or 'allama.json'
            tester.compare_models(args.compare, output_file, json_output)

        else:
            # Standardowe testy
            tester.run_tests()
            output_file = args.output or 'allama.html'
            json_output = args.json_output or 'allama.json'
            tester.generate_html_report(output_file, json_output)

        logger.info(" Testowanie zakończone pomyślnie!")
        
        # Automatycznie otwórz raport w przeglądarce, jeśli został wygenerowany i opcja nie jest wyłączona
        if output_file and not args.no_browser:
            open_report_in_browser(output_file)
            
        # Publikuj wyniki na serwerze, jeśli opcja jest włączona
        if args.publish and json_output:
            publisher = ResultPublisher(server_url=args.server_url)
            result = publisher.publish_results(json_output)
            
            if result.get('success'):
                logger.info(f"Wyniki zostały pomyślnie opublikowane na serwerze")
                if 'data' in result and 'url' in result['data']:
                    logger.info(f"URL wyników: {result['data']['url']}")
            else:
                logger.error(f"Błąd podczas publikowania wyników: {result.get('error', 'Nieznany błąd')}")

    except KeyboardInterrupt:
        logger.info("  Testowanie przerwane przez użytkownika")
    except Exception as e:
        logger.error(f"Błąd podczas testowania: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()