#!/usr/bin/env python3
"""
Универсальный анализатор сервера для оптимизации производительности
Определяет оптимальные лимиты задач на основе характеристик системы
Только консольная работа, без создания файлов
"""

import asyncio
import time
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime

class ServerAnalyzer:
    """Анализатор сервера для TaskManager"""
    
    def __init__(self):
        self.results = {
            'system_info': {},
            'performance_tests': [],
            'recommendations': {},
            'analysis_time': datetime.now().isoformat()
        }
        
        # Цвета для вывода
        self.colors = {
            'header': '\033[95m',
            'success': '\033[92m',
            'warning': '\033[93m',
            'error': '\033[91m',
            'info': '\033[94m',
            'end': '\033[0m'
        }
    
    def print_header(self, text: str):
        """Печатает заголовок"""
        print(f"\n{self.colors['header']}{'='*60}")
        print(f"{text:^60}")
        print(f"{'='*60}{self.colors['end']}")
    
    def print_success(self, text: str):
        """Печатает успешное сообщение"""
        print(f"{self.colors['success']}✅ {text}{self.colors['end']}")
    
    def print_warning(self, text: str):
        """Печатает предупреждение"""
        print(f"{self.colors['warning']}⚠️ {text}{self.colors['end']}")
    
    def print_error(self, text: str):
        """Печатает ошибку"""
        print(f"{self.colors['error']}❌ {text}{self.colors['end']}")
    
    def print_info(self, text: str):
        """Печатает информацию"""
        print(f"{self.colors['info']}ℹ️ {text}{self.colors['end']}")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Получает детальную информацию о системе"""
        print(f"\n{self.colors['info']}🔍 Анализируем систему...{self.colors['end']}")
        
        # CPU информация
        cpu_info = {
            'cores_physical': psutil.cpu_count(logical=False),
            'cores_logical': psutil.cpu_count(logical=True),
            'max_frequency': psutil.cpu_freq().max if psutil.cpu_freq() else 0,
            'current_frequency': psutil.cpu_freq().current if psutil.cpu_freq() else 0,
            'usage_percent': psutil.cpu_percent(interval=1)
        }
        
        # Память
        memory = psutil.virtual_memory()
        memory_info = {
            'total_gb': memory.total / (1024**3),
            'available_gb': memory.available / (1024**3),
            'used_gb': memory.used / (1024**3),
            'percent': memory.percent,
            'free_gb': memory.free / (1024**3)
        }
        
        # Диск
        disk = psutil.disk_usage('/')
        disk_info = {
            'total_gb': disk.total / (1024**3),
            'free_gb': disk.free / (1024**3),
            'used_gb': disk.used / (1024**3),
            'percent': (disk.used / disk.total) * 100
        }
        
        # Сеть
        network_info = {
            'connections': len(psutil.net_connections()),
            'interfaces': len(psutil.net_if_addrs())
        }
        
        system_info = {
            'cpu': cpu_info,
            'memory': memory_info,
            'disk': disk_info,
            'network': network_info,
            'platform': {
                'system': psutil.UNIX if hasattr(psutil, 'UNIX') else 'Windows',
                'python_version': f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}"
            }
        }
        
        self.results['system_info'] = system_info
        return system_info
    
    def display_system_info(self, system_info: Dict[str, Any]):
        """Отображает информацию о системе"""
        self.print_header("ИНФОРМАЦИЯ О СИСТЕМЕ")
        
        cpu = system_info['cpu']
        memory = system_info['memory']
        disk = system_info['disk']
        
        print(f"\n🖥️ ПРОЦЕССОР:")
        print(f"   Физические ядра: {cpu['cores_physical']}")
        print(f"   Логические ядра: {cpu['cores_logical']}")
        print(f"   Максимальная частота: {cpu['max_frequency']:.0f} MHz")
        print(f"   Текущая частота: {cpu['current_frequency']:.0f} MHz")
        print(f"   Текущая нагрузка: {cpu['usage_percent']:.1f}%")
        
        print(f"\n💾 ПАМЯТЬ:")
        print(f"   Общий объем: {memory['total_gb']:.1f} GB")
        print(f"   Доступно: {memory['available_gb']:.1f} GB")
        print(f"   Используется: {memory['used_gb']:.1f} GB ({memory['percent']:.1f}%)")
        print(f"   Свободно: {memory['free_gb']:.1f} GB")
        
        print(f"\n💿 ДИСК:")
        print(f"   Общий объем: {disk['total_gb']:.1f} GB")
        print(f"   Свободно: {disk['free_gb']:.1f} GB")
        print(f"   Используется: {disk['used_gb']:.1f} GB ({disk['percent']:.1f}%)")
        
        print(f"\n🌐 СЕТЬ:")
        print(f"   Активных соединений: {system_info['network']['connections']}")
        print(f"   Сетевых интерфейсов: {system_info['network']['interfaces']}")
    
    async def run_performance_test(self, test_name: str, max_concurrent: int, 
                                 task_count: int, test_duration: float = 2.0) -> Dict[str, Any]:
        """Запускает тест производительности"""
        print(f"\n🧪 Тест: {test_name} (лимит: {max_concurrent}, задач: {task_count})")
        
        # Измеряем нагрузку до теста
        cpu_before = psutil.cpu_percent()
        memory_before = psutil.virtual_memory().percent
        
        start_time = time.time()
        
        # Создаем семафор для ограничения
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def test_task(task_id: int):
            async with semaphore:
                import random
                
                # Реалистичные типы задач на основе тестирования
                task_type = task_id % 5
                
                if task_type == 0:
                    # Critical задача - быстрая, но важная (API, аутентификация)
                    await asyncio.sleep(0.01)  # Минимальная задержка сети
                    data = [random.randint(1, 100) for _ in range(100)]
                    result = sum(data)
                    if result > 5000:
                        processed = [x for x in data if x > 50]
                    else:
                        processed = data
                    
                elif task_type == 1:
                    # High задача - пользовательские действия
                    await asyncio.sleep(0.05)  # Умеренная задержка I/O
                    user_data = [random.randint(1, 1000) for _ in range(500)]
                    processed = [x * 2 for x in user_data if x % 2 == 0]
                    processed.sort()
                    filtered = [x for x in processed if x > 100]
                    
                elif task_type == 2:
                    # Medium задача - обработка данных
                    await asyncio.sleep(0.1)  # Задержка для обработки данных
                    data = [random.random() for _ in range(2000)]
                    data.sort()
                    mean = sum(data) / len(data)
                    variance = sum((x - mean) ** 2 for x in data) / len(data)
                    groups = {}
                    for i, value in enumerate(data):
                        group = int(value * 10)
                        if group not in groups:
                            groups[group] = []
                        groups[group].append(i)
                    
                elif task_type == 3:
                    # Low задача - логирование, статистика
                    await asyncio.sleep(0.2)  # Длительная задержка (логирование в файл)
                    logs = [f"Log entry {i}: {random.randint(1, 1000)}" for i in range(1000)]
                    stats = {}
                    for log in logs:
                        key = log.split(':')[0]
                        if key not in stats:
                            stats[key] = 0
                        stats[key] += 1
                    report = {k: v for k, v in stats.items() if v > 10}
                    
                else:
                    # Heavy задача - ML, анализ, обработка файлов
                    await asyncio.sleep(0.02)  # Минимальная задержка - основная работа CPU/Memory
                    matrix_a = [[random.random() for _ in range(100)] for _ in range(100)]
                    matrix_b = [[random.random() for _ in range(100)] for _ in range(100)]
                    result_matrix = [[0 for _ in range(100)] for _ in range(100)]
                    for i in range(100):
                        for j in range(100):
                            for k in range(100):
                                result_matrix[i][j] += matrix_a[i][k] * matrix_b[k][j]
                    eigenvalues = []
                    for row in result_matrix:
                        eigenvalues.append(sum(row))
                    eigenvalues.sort()
                    filtered_eigenvalues = [x for x in eigenvalues if x > 50]
        
        # Запускаем задачи
        tasks = [test_task(i) for i in range(task_count)]
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Измеряем нагрузку после теста
        cpu_after = psutil.cpu_percent()
        memory_after = psutil.virtual_memory().percent
        
        result = {
            'test_name': test_name,
            'max_concurrent': max_concurrent,
            'task_count': task_count,
            'duration': duration,
            'tasks_per_second': task_count / duration,
            'cpu_before': cpu_before,
            'cpu_after': cpu_after,
            'cpu_delta': cpu_after - cpu_before,
            'memory_before': memory_before,
            'memory_after': memory_after,
            'memory_delta': memory_after - memory_before,
            'efficiency_score': (task_count / duration) / max_concurrent
        }
        
        self.results['performance_tests'].append(result)
        
        print(f"   ⏱️ Время выполнения: {duration:.2f}с")
        print(f"   📊 Задач в секунду: {result['tasks_per_second']:.1f}")
        print(f"   🔥 CPU: {cpu_before:.1f}% → {cpu_after:.1f}% (Δ{cpu_after-cpu_before:+.1f}%)")
        print(f"   💾 RAM: {memory_before:.1f}% → {memory_after:.1f}% (Δ{memory_after-memory_before:+.1f}%)")
        print(f"   📈 Эффективность: {result['efficiency_score']:.2f}")
        
        return result
    
    async def run_basic_performance_tests(self):
        """Запускает базовые тесты для генерации рекомендаций"""
        # Простые тесты для анализа системы
        test_scenarios = [
            ("Critical Queue", 5, 10),
            ("High Priority Queue", 8, 16),
            ("Medium Priority Queue", 12, 24),
            ("Low Priority Queue", 6, 12),
            ("Heavy Tasks", 3, 6),
        ]
        
        for test_name, limit, task_count in test_scenarios:
            await self.run_performance_test(test_name, limit, task_count, 1.0)
            await asyncio.sleep(0.2)  # Пауза между тестами
    
    def calculate_recommendations(self) -> Dict[str, Any]:
        """Вычисляет рекомендации на основе тестов"""
        system_info = self.results['system_info']
        tests = self.results['performance_tests']
        
        cpu_cores = system_info['cpu']['cores_physical']
        memory_gb = system_info['memory']['total_gb']
        
        # Анализируем результаты тестов для корректировки рекомендаций
        best_performances = {}
        cpu_load_analysis = []
        
        for test in tests:
            queue_type = test['test_name'].split()[0].lower()
            if queue_type not in best_performances:
                best_performances[queue_type] = test
            elif test['efficiency_score'] > best_performances[queue_type]['efficiency_score']:
                best_performances[queue_type] = test
            
            # Собираем данные о нагрузке для анализа
            cpu_load_analysis.append({
                'limit': test['max_concurrent'],
                'cpu_delta': test['cpu_delta'],
                'memory_delta': test['memory_delta'],
                'queue_type': queue_type
            })
        
        # Корректируем рекомендации на основе реальной нагрузки
        avg_cpu_delta = sum(t['cpu_delta'] for t in cpu_load_analysis) / len(cpu_load_analysis)
        avg_memory_delta = sum(t['memory_delta'] for t in cpu_load_analysis) / len(cpu_load_analysis)
        
        # КАРДИНАЛЬНО агрессивные коэффициенты для достижения реальных пределов
        if avg_cpu_delta < 5:  # Очень низкая нагрузка - можно сильно увеличить
            conservative_factor = 3.0   # Консервативный - в 3 раза больше
            optimal_factor = 6.0        # Оптимальный - в 6 раз больше
            aggressive_factor = 12.0    # Агрессивный - в 12 раз больше!
        elif avg_cpu_delta < 10:  # Низкая нагрузка
            conservative_factor = 2.5
            optimal_factor = 5.0
            aggressive_factor = 10.0
        elif avg_cpu_delta > 30:  # Очень высокая нагрузка
            conservative_factor = 1.5
            optimal_factor = 3.0
            aggressive_factor = 6.0
        elif avg_cpu_delta > 20:  # Высокая нагрузка
            conservative_factor = 2.0
            optimal_factor = 4.0
            aggressive_factor = 8.0
        else:  # Нормальная нагрузка
            conservative_factor = 2.5
            optimal_factor = 5.0
            aggressive_factor = 10.0
        
        # КАРДИНАЛЬНО агрессивные рекомендации для достижения реальных пределов
        recommendations = {
            'global_limit': {
                'conservative': int(cpu_cores * 15 * conservative_factor),   # 6 * 15 * 3.0 = 270
                'optimal': int(cpu_cores * 30 * optimal_factor),             # 6 * 30 * 6.0 = 1080
                'aggressive': int(cpu_cores * 50 * aggressive_factor),       # 6 * 50 * 12.0 = 3600!
                'max_memory_based': int(memory_gb * 50 * optimal_factor)     # 16 * 50 * 6.0 = 4800
            },
            'queues': {
                'critical': {
                    'conservative': int(cpu_cores * 5 * conservative_factor),    # 6 * 5 * 3.0 = 90
                    'optimal': int(cpu_cores * 10 * optimal_factor),              # 6 * 10 * 6.0 = 360
                    'aggressive': int(cpu_cores * 20 * aggressive_factor)        # 6 * 20 * 12.0 = 1440!
                },
                'high': {
                    'conservative': int(cpu_cores * 6 * conservative_factor),     # 6 * 6 * 3.0 = 108
                    'optimal': int(cpu_cores * 12 * optimal_factor),              # 6 * 12 * 6.0 = 432
                    'aggressive': int(cpu_cores * 25 * aggressive_factor)         # 6 * 25 * 12.0 = 1800!
                },
                'medium': {
                    'conservative': int(cpu_cores * 8 * conservative_factor),     # 6 * 8 * 3.0 = 144
                    'optimal': int(cpu_cores * 15 * optimal_factor),              # 6 * 15 * 6.0 = 540
                    'aggressive': int(cpu_cores * 30 * aggressive_factor)        # 6 * 30 * 12.0 = 2160!
                },
                'low': {
                    'conservative': int(cpu_cores * 5 * conservative_factor),     # 6 * 5 * 3.0 = 90
                    'optimal': int(cpu_cores * 10 * optimal_factor),              # 6 * 10 * 6.0 = 360
                    'aggressive': int(cpu_cores * 20 * aggressive_factor)        # 6 * 20 * 12.0 = 1440!
                },
                'heavy': {
                    'conservative': int(cpu_cores * 3 * conservative_factor),     # 6 * 3 * 3.0 = 54
                    'optimal': int(cpu_cores * 6 * optimal_factor),              # 6 * 6 * 6.0 = 216
                    'aggressive': int(cpu_cores * 12 * aggressive_factor)        # 6 * 12 * 12.0 = 864!
                }
            },
            'monitoring': {
                'enabled': True,
                'load_limits': {
                    'level_1': {'threshold': 70.0, 'total_limit': None},
                    'level_2': {'threshold': 85.0, 'total_limit': None},
                    'level_3': {'threshold': 95.0, 'total_limit': None}
                }
            }
        }
        
        # Вычисляем лимиты мониторинга
        optimal_global = recommendations['global_limit']['optimal']
        recommendations['monitoring']['load_limits']['level_1']['total_limit'] = int(optimal_global * 0.7)
        recommendations['monitoring']['load_limits']['level_2']['total_limit'] = int(optimal_global * 0.5)
        recommendations['monitoring']['load_limits']['level_3']['total_limit'] = int(optimal_global * 0.3)
        
        # Добавляем информацию об анализе нагрузки
        recommendations['load_analysis'] = {
            'avg_cpu_delta': avg_cpu_delta,
            'avg_memory_delta': avg_memory_delta,
            'conservative_factor': conservative_factor,
            'optimal_factor': optimal_factor,
            'aggressive_factor': aggressive_factor,
            'recommendation_note': f"Коэффициенты: консервативный {conservative_factor:.1f}, оптимальный {optimal_factor:.1f}, агрессивный {aggressive_factor:.1f} (средний прирост CPU: {avg_cpu_delta:+.1f}%)"
        }
        
        self.results['recommendations'] = recommendations
        return recommendations
    
    def display_recommendations(self, recommendations: Dict[str, Any]):
        """Отображает рекомендации"""
        self.print_header("РЕКОМЕНДАЦИИ ПО КОНФИГУРАЦИИ")
        
        global_limit = recommendations['global_limit']
        queues = recommendations['queues']
        load_analysis = recommendations.get('load_analysis', {})
        
        # Показываем анализ нагрузки
        if load_analysis:
            print(f"\n📊 АНАЛИЗ НАГРУЗКИ:")
            print(f"   {load_analysis.get('recommendation_note', '')}")
            print(f"   Средний прирост RAM: {load_analysis.get('avg_memory_delta', 0):+.1f}%")
        
        print(f"\n🌐 ГЛОБАЛЬНЫЙ ЛИМИТ СИСТЕМЫ:")
        print(f"   Консервативный: {global_limit['conservative']}")
        print(f"   Оптимальный: {global_limit['optimal']}")
        print(f"   Агрессивный: {global_limit['aggressive']}")
        print(f"   По памяти: {global_limit['max_memory_based']}")
        
        print(f"\n📋 ЛИМИТЫ ОЧЕРЕДЕЙ:")
        for queue_name, limits in queues.items():
            print(f"\n   {queue_name.upper()}:")
            print(f"     Консервативный: {limits['conservative']}")
            print(f"     Оптимальный: {limits['optimal']}")
            print(f"     Агрессивный: {limits['aggressive']}")
        
        print(f"\n📊 МОНИТОРИНГ НАГРУЗКИ:")
        monitoring = recommendations['monitoring']
        print(f"   Включен: {'Да' if monitoring['enabled'] else 'Нет'}")
        for level, config in monitoring['load_limits'].items():
            print(f"   {level}: порог {config['threshold']}%, лимит {config['total_limit']}")
    
    
    def display_settings_summary(self, recommendations: Dict[str, Any], profile: str = 'optimal'):
        """Отображает краткую сводку настроек"""
        global_limit = recommendations['global_limit'][profile]
        queues = recommendations['queues']
        monitoring = recommendations['monitoring']
        
        self.print_header(f"СВОДКА НАСТРОЕК ({profile.upper()})")
        
        print(f"\n🌐 ГЛОБАЛЬНЫЕ НАСТРОЙКИ:")
        print(f"   Общий лимит задач: {global_limit}")
        print(f"   Мониторинг включен: {'Да' if monitoring['enabled'] else 'Нет'}")
        
        print(f"\n📊 ЛИМИТЫ МОНИТОРИНГА:")
        for level, config in monitoring['load_limits'].items():
            print(f"   {level}: порог {config['threshold']}%, лимит {config['total_limit']}")
        
        print(f"\n📋 ЛИМИТЫ ОЧЕРЕДЕЙ:")
        for queue_name, limits in queues.items():
            print(f"   {queue_name}: {limits[profile]}")
        
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        print(f"   • Скопируйте эти значения в вашу конфигурацию")
        print(f"   • Начните с консервативных значений")
        print(f"   • Мониторьте производительность после внедрения")
        print(f"   • При необходимости корректируйте лимиты")
    
    async def test_real_task_manager(self, recommendations: Dict[str, Any], profile: str = 'optimal'):
        """Тестирует реальный TaskManager с рекомендованными настройками"""
        self.print_header(f"ТЕСТ РЕАЛЬНОГО TASKMANAGER ({profile.upper()})")
        
        global_limit = recommendations['global_limit'][profile]
        queues = recommendations['queues']
        
        print(f"\n🎯 Тестируем настройки:")
        print(f"   Глобальный лимит: {global_limit}")
        for queue_name, limits in queues.items():
            print(f"   {queue_name}: {limits[profile]}")
        
        print(f"\n⚠️ ВНИМАНИЕ: Этот тест требует реального TaskManager")
        print(f"   • Подмена конфигурации")
        print(f"   • Загрузка задач во все очереди одновременно")
        print(f"   • Измерение реальной производительности")
        
        print(f"\n🚧 Функция в разработке...")
        print(f"   • Интеграция с реальным TaskManager")
        print(f"   • Подмена config.yaml")
        print(f"   • Тестирование полной нагрузки")
        
        # Реализуем интеграцию с реальным TaskManager
        await self._test_real_task_manager_integration(global_limit, queues, profile)
    
    async def _test_real_task_manager_integration(self, global_limit: int, queues: Dict[str, Any], profile: str):
        """Интеграция с реальным TaskManager из DI-контейнера"""
        try:
            # Инициализируем DI-контейнер как в database_manager.py
            print(f"\n🔧 Инициализация DI-контейнера...")
            
            # Настройка путей и окружения
            import os
            import sys
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            sys.path.insert(0, project_root)
            os.chdir(project_root)
            
            # Загружаем переменные окружения
            try:
                from dotenv import load_dotenv
                load_dotenv()
            except ImportError:
                print("⚠️ python-dotenv не установлен")
            
            # Импорты для работы с DI-контейнером
            from app.di_container import DIContainer
            from plugins.utilities.foundation.logger.logger import Logger
            from plugins.utilities.foundation.plugins_manager.plugins_manager import PluginsManager
            from plugins.utilities.foundation.settings_manager.settings_manager import SettingsManager
            
            # Инициализация DI-контейнера
            logger = Logger()
            plugins_manager = PluginsManager(logger=logger)
            settings_manager = SettingsManager(logger=logger, plugins_manager=plugins_manager)
            di_container = DIContainer(logger=logger, plugins_manager=plugins_manager, settings_manager=settings_manager)
            
            # Инициализация всех плагинов
            di_container.initialize_all_plugins()
            
            # Получение TaskManager из контейнера по требованию
            print(f"🔍 Поиск TaskManager в DI-контейнере...")
            task_manager = di_container.get_utility_on_demand("task_manager")
            if not task_manager:
                print("❌ Ошибка: не удалось получить task_manager из DI-контейнера")
                return
            
            print(f"✅ TaskManager получен из DI-контейнера")
            print(f"   Текущий глобальный лимит: {task_manager.current_total_limit}")
            print(f"   Мониторинг включен: {task_manager.monitoring_enabled}")
            
            # Подменяем настройки в работающем TaskManager
            await self._override_task_manager_settings(task_manager, global_limit, queues, profile)
            
            # Запускаем тест полной нагрузки
            await self._run_full_load_test(task_manager, queues, profile)
            
            # Получаем статистику
            stats = task_manager.get_stats()
            self._analyze_task_manager_results(stats, profile)
            
            # Корректно завершаем DI-контейнер
            di_container.shutdown()
            
        except Exception as e:
            print(f"❌ Ошибка тестирования: {e}")
            import traceback
            traceback.print_exc()
    
    async def _override_task_manager_settings(self, task_manager, global_limit: int, queues: Dict[str, Any], profile: str):
        """Подменяет настройки в работающем TaskManager"""
        print(f"\n🔧 Подмена настроек TaskManager...")
        
        # Сохраняем оригинальные настройки для восстановления
        original_settings = {
            'default_total_limit': task_manager.default_total_limit,
            'current_total_limit': task_manager.current_total_limit,
            'monitoring_enabled': task_manager.monitoring_enabled
        }
        
        # Подменяем системные лимиты
        task_manager.default_total_limit = global_limit
        task_manager.current_total_limit = global_limit
        
        # Отключаем мониторинг для чистого теста
        task_manager.monitoring_enabled = False
        
        print(f"   ✅ Глобальный лимит: {global_limit}")
        print(f"   ✅ Мониторинг отключен")
        
        # Подменяем настройки очередей через queue_manager
        if hasattr(task_manager, 'queue_manager'):
            queue_manager = task_manager.queue_manager
            
            # Обновляем лимиты очередей
            for queue_name, limits in queues.items():
                if hasattr(queue_manager, 'queue_configs') and queue_name in queue_manager.queue_configs:
                    config = queue_manager.queue_configs[queue_name]
                    new_limit = limits[profile]
                    
                    # Обновляем лимит в конфигурации
                    config.max_concurrent = new_limit
                    
                    # Обновляем семафор для этой очереди
                    if hasattr(queue_manager, 'semaphores') and queue_name in queue_manager.semaphores:
                        old_semaphore = queue_manager.semaphores[queue_name]
                        new_semaphore = asyncio.Semaphore(new_limit)
                        queue_manager.semaphores[queue_name] = new_semaphore
                        
                        print(f"   ✅ {queue_name}: {new_limit} (было: {old_semaphore._value})")
        
        # Сохраняем оригинальные настройки для восстановления
        task_manager._original_settings = original_settings
        
        print(f"   ✅ Настройки подменены успешно")
    
    
    async def _run_full_load_test(self, task_manager, queues: Dict[str, Any], profile: str):
        """Запускает полный тест загрузки всех очередей"""
        print(f"\n🚀 Запуск полного теста загрузки...")
        
        # Определяем количество задач для каждой очереди - СВЕРХ лимитов!
        queue_tasks = {}
        
        for queue_name, limits in queues.items():
            queue_limit = limits[profile]
            # Загружаем в 5-10 раз больше задач чем лимит очереди для полной нагрузки!
            if profile == 'conservative':
                multiplier = 5  # Консервативный - в 5 раз больше
            elif profile == 'optimal':
                multiplier = 8  # Оптимальный - в 8 раз больше
            else:  # aggressive
                multiplier = 10  # Агрессивный - в 10 раз больше!
            
            queue_tasks[queue_name] = queue_limit * multiplier
        
        print(f"📊 План загрузки:")
        for queue_name, task_count in queue_tasks.items():
            queue_limit = queues[queue_name][profile]
            print(f"   {queue_name}: {task_count} задач (лимит: {queue_limit})")
        
        # Создаем задачи для всех очередей
        start_time = time.time()
        start_cpu = psutil.cpu_percent()
        start_memory = psutil.virtual_memory().percent
        
        submitted_tasks = 0
        
        # Загружаем задачи во все очереди параллельно
        for queue_name, task_count in queue_tasks.items():
            for i in range(task_count):
                task_id = f"{queue_name}_{i}"
                coro = lambda: asyncio.create_task(self._create_task_simulator(queue_name, i))
                
                success = await task_manager.submit_task(
                    task_id=task_id,
                    coro=coro,
                    queue_name=queue_name
                )
                
                if success:
                    submitted_tasks += 1
                
                # Небольшая задержка между отправкой задач
                await asyncio.sleep(0.001)
        
        print(f"✅ Отправлено {submitted_tasks} задач")
        
        # Ждем завершения всех задач
        print(f"⏳ Ожидание завершения задач...")
        await asyncio.sleep(5)  # Даем время на выполнение
        
        # Получаем финальную статистику
        end_time = time.time()
        end_cpu = psutil.cpu_percent()
        end_memory = psutil.virtual_memory().percent
        
        duration = end_time - start_time
        cpu_delta = end_cpu - start_cpu
        memory_delta = end_memory - start_memory
        
        print(f"\n📊 РЕЗУЛЬТАТЫ ТЕСТА:")
        print(f"   Время выполнения: {duration:.2f}с")
        print(f"   Прирост CPU: {cpu_delta:+.1f}%")
        print(f"   Прирост RAM: {memory_delta:+.1f}%")
        print(f"   Отправлено задач: {submitted_tasks}")
        
        # Сохраняем результаты для анализа
        self.test_results = {
            'profile': profile,
            'global_limit': task_manager.current_total_limit,
            'queue_limits': {k: queues[k][profile] for k in queues.keys()},
            'submitted_tasks': submitted_tasks,
            'duration': duration,
            'cpu_delta': cpu_delta,
            'memory_delta': memory_delta,
            'tasks_per_second': submitted_tasks / duration if duration > 0 else 0
        }
    
    async def _create_task_simulator(self, queue_name: str, task_id: int):
        """Создает симулятор задачи для указанной очереди"""
        import random
        
        if queue_name == 'critical':
            # Быстрые критические задачи
            await asyncio.sleep(random.uniform(0.01, 0.05))
            data = [random.randint(1, 100) for _ in range(50)]
            result = sum(data)
        elif queue_name == 'high':
            # Пользовательские действия
            await asyncio.sleep(random.uniform(0.05, 0.1))
            user_data = [random.randint(1, 1000) for _ in range(200)]
            processed = [x * 2 for x in user_data if x % 2 == 0]
        elif queue_name == 'medium':
            # Обработка данных
            await asyncio.sleep(random.uniform(0.1, 0.2))
            data = [random.random() for _ in range(1000)]
            data.sort()
            mean = sum(data) / len(data)
        elif queue_name == 'low':
            # Логирование и статистика
            await asyncio.sleep(random.uniform(0.2, 0.4))
            logs = [f"Log entry {i}: {random.randint(1, 1000)}" for i in range(500)]
            stats = {}
            for log in logs:
                key = log.split(':')[0]
                stats[key] = stats.get(key, 0) + 1
        else:  # heavy
            # Тяжелые задачи
            await asyncio.sleep(random.uniform(0.02, 0.1))
            matrix_a = [[random.random() for _ in range(50)] for _ in range(50)]
            matrix_b = [[random.random() for _ in range(50)] for _ in range(50)]
            result_matrix = [[0 for _ in range(50)] for _ in range(50)]
            for i in range(50):
                for j in range(50):
                    for k in range(50):
                        result_matrix[i][j] += matrix_a[i][k] * matrix_b[k][j]
    
    def _analyze_task_manager_results(self, stats: Dict[str, Any], profile: str):
        """Анализирует результаты работы TaskManager"""
        print(f"\n📈 АНАЛИЗ РАБОТЫ TASKMANAGER:")
        
        # Активные задачи
        active_tasks = stats.get('active_tasks', {})
        total_active = sum(active_tasks.values())
        print(f"   Активные задачи: {total_active}")
        for queue_name, count in active_tasks.items():
            print(f"     {queue_name}: {count}")
        
        # Размеры очередей
        queue_sizes = stats.get('queue_sizes', {})
        total_queued = sum(queue_sizes.values())
        print(f"   Задач в очередях: {total_queued}")
        for queue_name, size in queue_sizes.items():
            print(f"     {queue_name}: {size}")
        
        # Системные лимиты
        system_limit = stats.get('system_limit', 0)
        print(f"   Системный лимит: {system_limit}")
        
        # Анализ эффективности
        if hasattr(self, 'test_results'):
            results = self.test_results
            efficiency = results['tasks_per_second']
            cpu_load = results['cpu_delta']
            
            print(f"\n🎯 ОЦЕНКА ЭФФЕКТИВНОСТИ:")
            print(f"   Скорость обработки: {efficiency:.1f} задач/сек")
            print(f"   CPU нагрузка: {cpu_load:+.1f}%")
            
            if cpu_load < 5:
                print("   ✅ Нагрузка оптимальна - можно увеличить лимиты")
            elif cpu_load < 15:
                print("   ⚠️ Нагрузка умеренная - лимиты подходят")
            else:
                print("   ❌ Нагрузка высокая - рекомендуется уменьшить лимиты")

async def interactive_menu():
    """Интерактивное меню"""
    analyzer = ServerAnalyzer()
    
    while True:
        print(f"\n{analyzer.colors['header']}🔧 АНАЛИЗАТОР ПРОИЗВОДИТЕЛЬНОСТИ СЕРВЕРА{analyzer.colors['end']}")
        print("1. 📊 Полный анализ системы")
        print("2. 🖥️ Информация о системе")
        print("3. 💡 Рекомендации")
        print("4. 🎯 Тест реального TaskManager")
        print("5. ❌ Выход")
        
        choice = input(f"\n{analyzer.colors['info']}Выберите опцию (1-5): {analyzer.colors['end']}").strip()
        
        if choice == '1':
            # Полный анализ
            analyzer.print_header("ПОЛНЫЙ АНАЛИЗ СИСТЕМЫ")
            system_info = analyzer.get_system_info()
            analyzer.display_system_info(system_info)
            
            # Базовые тесты для генерации рекомендаций
            analyzer.print_header("БАЗОВЫЕ ТЕСТЫ ПРОИЗВОДИТЕЛЬНОСТИ")
            await analyzer.run_basic_performance_tests()
            
            recommendations = analyzer.calculate_recommendations()
            analyzer.display_recommendations(recommendations)
            
        elif choice == '2':
            # Информация о системе
            system_info = analyzer.get_system_info()
            analyzer.display_system_info(system_info)
            
        elif choice == '3':
            # Рекомендации
            if not analyzer.results.get('recommendations'):
                analyzer.print_warning("Сначала запустите полный анализ системы")
                continue
            analyzer.display_recommendations(analyzer.results['recommendations'])
            
        elif choice == '4':
            # Тест реального TaskManager
            if not analyzer.results.get('recommendations'):
                analyzer.print_warning("Сначала получите рекомендации")
                continue
            
            print(f"\n{analyzer.colors['info']}Выберите профиль для тестирования:{analyzer.colors['end']}")
            print("1. Консервативный (безопасный)")
            print("2. Оптимальный (рекомендуемый)")
            print("3. Агрессивный (максимальная производительность)")
            
            profile_choice = input("Профиль (1-3): ").strip()
            profile_map = {'1': 'conservative', '2': 'optimal', '3': 'aggressive'}
            profile = profile_map.get(profile_choice, 'optimal')
            
            await analyzer.test_real_task_manager(analyzer.results['recommendations'], profile)
            
        elif choice == '5':
            # Выход
            analyzer.print_success("До свидания!")
            break
            
        else:
            analyzer.print_error("Неверный выбор. Попробуйте снова.")

async def main():
    """Основная функция"""
    try:
        await interactive_menu()
    except KeyboardInterrupt:
        print(f"\n{ServerAnalyzer().colors['warning']}Прервано пользователем{ServerAnalyzer().colors['end']}")
    except Exception as e:
        print(f"\n{ServerAnalyzer().colors['error']}Ошибка: {e}{ServerAnalyzer().colors['end']}")

if __name__ == "__main__":
    asyncio.run(main())
