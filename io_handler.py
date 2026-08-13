import os
import sys
import time
import json
import functools
from datetime import datetime
from collections import Counter

def retry_on_error(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,), logger=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            wait = delay
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if logger:
                        logger.log_warning(f"Attempt {attempts}/{max_attempts} failed: {e}. Retrying in {wait}s...")
                    if attempts >= max_attempts:
                        raise
                    time.sleep(wait)
                    wait *= backoff
            return None
        return wrapper
    return decorator

class Logger:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.infos = []
        self.debugs = []
        self.error_counts = Counter()
        self.unique_errors = []
        self.start_time = datetime.now()

    def log_error(self, message: str):
        self.errors.append((datetime.now().isoformat(), message))
        self.error_counts[message] += 1
        if self.error_counts[message] == 1:
            self.unique_errors.append(message)
        print(f"[ERROR] {message}", file=sys.stderr)

    def log_warning(self, message: str):
        self.warnings.append((datetime.now().isoformat(), message))
        print(f"[WARNING] {message}")

    def log_info(self, message: str):
        self.infos.append((datetime.now().isoformat(), message))
        print(f"[INFO] {message}")

    def log_debug(self, message: str):
        self.debugs.append((datetime.now().isoformat(), message))

    def generate_report(self, filename: str = "report.txt") -> str:
        report_path = os.path.join(os.getcwd(), filename)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"=== Organization Report ===\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Started:   {self.start_time.isoformat()}\n")
            f.write(f"Duration:  {datetime.now() - self.start_time}\n")
            f.write("\n=== Unique Errors (deduplicated) ===\n")
            if self.unique_errors:
                for err in self.unique_errors:
                    count = self.error_counts[err]
                    f.write(f"  [{count}x] {err}\n")
            else:
                f.write("  (none)\n")
            f.write("\n=== All Errors (with timestamps) ===\n")
            for ts, msg in self.errors:
                f.write(f"{ts}: {msg}\n")
            f.write("\n=== Warnings ===\n")
            for ts, msg in self.warnings:
                f.write(f"{ts}: {msg}\n")
            f.write("\n=== Info Logs ===\n")
            for ts, msg in self.infos:
                f.write(f"{ts}: {msg}\n")
            if self.debugs:
                f.write("\n=== Debug Logs ===\n")
                for ts, msg in self.debugs:
                    f.write(f"{ts}: {msg}\n")
            f.write("\n=== End of Report ===\n")
        return report_path

    def clear(self):
        self.errors.clear()
        self.warnings.clear()
        self.infos.clear()
        self.debugs.clear()
        self.error_counts.clear()
        self.unique_errors.clear()

class IOHandler:
    def __init__(self, logger: Logger):
        self.logger = logger

    def prompt_input(self, prompt: str) -> str:
        try:
            return input(prompt)
        except KeyboardInterrupt:
            self.logger.log_error("User interrupted input.")
            sys.exit(1)

    def prompt_yes_no(self, prompt: str) -> bool:
        while True:
            response = self.prompt_input(prompt).strip().lower()
            if response in ('y','yes','true','1'):
                return True
            elif response in ('n','no','false','0'):
                return False
            else:
                self.logger.log_warning("Please enter y or n.")

    def prompt_choice(self, prompt: str, options: list) -> str:
        print(prompt)
        for i, opt in enumerate(options, 1):
            print(f"  {i}. {opt}")
        while True:
            choice = self.prompt_input("Enter number: ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(options):
                    return options[idx]
            except ValueError:
                pass
            self.logger.log_warning("Invalid choice. Please try again.")