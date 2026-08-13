#!/usr/bin/env python3
import os
import sys
import random
import string
import argparse
import uuid
import time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

DEFAULT_EXTENSIONS = [
    '.py', '.java', '.lua', '.luau', '.c', '.cpp', '.h', '.cs',
    '.go', '.rs', '.rb', '.pl', '.sh', '.bat', '.ps1', '.r',
    '.swift', '.kt', '.scala', '.clj', '.exs', '.elm', '.hs',
    '.erl', '.cr', '.nim', '.zig',
    '.html', '.htm', '.js', '.css', '.php', '.asp', '.aspx', '.jsp',
    '.ts', '.jsx', '.tsx', '.vue', '.svelte',
    '.csv', '.parquet', '.sql', '.json', '.xml', '.yaml', '.yml',
    '.xls', '.xlsx', '.tsv', '.feather', '.orc', '.avro',
    '.log',
    '.txt', '.md', '.rst',
    '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.odt', '.ods', '.odp',
    '.rtf', '.tex',
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.svg', '.ico',
    '.cur', '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv',
    '.m4v',
    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a',
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.zst',
    '.exe', '.msi', '.app', '.dll', '.so', '.dylib', '.bin',
    '.lib', '.a', '.o',
    '.iso', '.img', '.dmg',
    '.ttf', '.otf',
    '.key', '.pem', '.crt', '.cer', '.pfx',
    '.db', '.sqlite', '.sqlite3', '.mdb', '.accdb',
    '.cfg', '.conf', '.ini', '.env',
    '.tmp', '.temp', '.cache',
]

LOREM_IPSUM = [
    "lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit",
    "sed", "do", "eiusmod", "tempor", "incididunt", "ut", "labore", "et", "dolore",
    "magna", "aliqua", "ut", "enim", "ad", "minim", "veniam", "quis", "nostrud",
    "exercitation", "ullamco", "laboris", "nisi", "ut", "aliquip", "ex", "ea",
    "commodo", "consequat", "duis", "aute", "irure", "dolor", "in", "reprehenderit"
]

def random_text(min_words=5, max_words=50):
    words = random.choices(LOREM_IPSUM, k=random.randint(min_words, max_words))
    return (' '.join(words) + '\n').encode('utf-8')

def random_binary(size_min=100, size_max=10*1024):
    size = random.randint(size_min, size_max)
    return os.urandom(size)

def generate_file(file_path, ext, content_type='mixed'):
    if content_type == 'mixed':
        content_type = random.choice(['text', 'binary'])
    text_extensions = {'.txt', '.md', '.rst', '.log', '.py', '.java', '.c', '.cpp',
                       '.h', '.cs', '.go', '.rs', '.rb', '.pl', '.sh', '.bat',
                       '.ps1', '.r', '.swift', '.kt', '.scala', '.clj', '.exs',
                       '.elm', '.hs', '.erl', '.cr', '.nim', '.zig', '.html',
                       '.htm', '.js', '.css', '.php', '.asp', '.aspx', '.jsp',
                       '.ts', '.jsx', '.tsx', '.vue', '.svelte', '.json', '.xml',
                       '.yaml', '.yml', '.csv', '.sql', '.cfg', '.conf', '.ini',
                       '.env', '.tsv', '.sqlite', '.sqlite3', '.db', '.tex', '.rtf'}
    if ext in text_extensions:
        content_type = 'text'
    else:
        content_type = 'binary'
    if content_type == 'text':
        content = random_text()
    else:
        content = random_binary()
    with open(file_path, 'wb') as f:
        f.write(content)

def generate_files_worker(args):
    output_dir, index, ext, content_type, seed = args
    if seed is not None:
        random.seed(seed + index)
    ts = datetime.now().strftime('%H%M%S%f')[:-3]
    rand_hex = uuid.uuid4().hex[:6]
    name_base = f"file_{ts}_{rand_hex}_{index}"
    if random.random() < 0.05:
        name_base += " " + random.choice(["!@#$%^&*()", "test with spaces", "üñîçødè"])
    file_name = name_base + ext
    file_path = os.path.join(output_dir, file_name)
    try:
        generate_file(file_path, ext, content_type)
        return (file_path, os.path.getsize(file_path))
    except Exception as e:
        return (None, str(e))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--num-files", type=int, default=3000)
    parser.add_argument("-o", "--output-dir", default="./test_files")
    parser.add_argument("-e", "--extensions", nargs="+")
    parser.add_argument("--extensions-file")
    parser.add_argument("--content-type", choices=['text', 'binary', 'mixed'], default='mixed')
    parser.add_argument("--seed", type=int)
    parser.add_argument("--no-parallel", action="store_true")
    parser.add_argument("--duplicates", type=int, default=0)
    parser.add_argument("--subdirs", type=int, default=0)
    parser.add_argument("--subdir-depth", type=int, default=2)
    parser.add_argument("--no-progress", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    extensions = []
    if args.extensions_file:
        with open(args.extensions_file, 'r') as f:
            extensions = [line.strip() for line in f if line.strip()]
    elif args.extensions:
        extensions = args.extensions
    else:
        extensions = DEFAULT_EXTENSIONS
    if not extensions:
        print("No extensions specified.")
        sys.exit(1)

    output_dir = Path(args.output_dir)
    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        print(f"[DRY RUN] Would create directory: {output_dir}")

    if args.seed is not None:
        random.seed(args.seed)

    total_files = args.num_files
    if total_files <= 0:
        print("Number of files must be positive.")
        sys.exit(1)

    file_specs = [(random.choice(extensions), args.content_type) for _ in range(total_files)]

    if args.duplicates > 0:
        for _ in range(args.duplicates):
            ext = random.choice(extensions)
            file_specs.append((ext, args.content_type))
            file_specs.append((ext, args.content_type))

    subdir_list = []
    if args.subdirs > 0:
        base_names = [f"sub_{i}" for i in range(args.subdirs)]
        for _ in range(min(args.subdirs, 100)):
            path = ""
            depth = random.randint(0, args.subdir_depth)
            for _ in range(depth):
                if base_names:
                    path = os.path.join(path, random.choice(base_names))
                else:
                    path = os.path.join(path, f"sub_{random.randint(0,9)}")
            subdir_list.append(path)
    file_paths = [random.choice(subdir_list) if subdir_list else "" for _ in range(total_files + args.duplicates*2)]

    tasks = []
    for i, (ext, content_type) in enumerate(file_specs):
        rel_path = file_paths[i] if args.subdirs > 0 else ""
        target_dir = output_dir / rel_path if rel_path else output_dir
        tasks.append((str(target_dir), i, ext, content_type, args.seed))

    use_parallel = not args.no_parallel and len(tasks) > 500

    if args.dry_run:
        print(f"[DRY RUN] Would generate {len(tasks)} files in {output_dir}")
        ext_counts = {}
        for _, _, ext, _, _ in tasks:
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
        print("Extension distribution:")
        for ext, count in sorted(ext_counts.items(), key=lambda x: -x[1])[:10]:
            print(f"  {ext}: {count}")
        sys.exit(0)

    print(f"Generating {len(tasks)} files in {output_dir}...")
    start_time = time.time()
    total_size = 0
    success_count = 0
    error_count = 0

    if use_parallel:
        print(f"Using parallel processing with {os.cpu_count()} workers.")
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(generate_files_worker, task) for task in tasks]
            if HAS_TQDM and not args.no_progress:
                pbar = tqdm(total=len(futures), desc="Generating files", unit="file")
            else:
                pbar = None
            for future in as_completed(futures):
                result = future.result()
                if result[0] is not None:
                    success_count += 1
                    total_size += result[1]
                else:
                    error_count += 1
                    print(f"Error: {result[1]}")
                if pbar:
                    pbar.update(1)
            if pbar:
                pbar.close()
    else:
        if HAS_TQDM and not args.no_progress:
            iterator = tqdm(tasks, desc="Generating files", unit="file")
        else:
            iterator = tasks
        for task in iterator:
            result = generate_files_worker(task)
            if result[0] is not None:
                success_count += 1
                total_size += result[1]
            else:
                error_count += 1
                print(f"Error: {result[1]}")

    elapsed = time.time() - start_time
    print("\n=== Generation Summary ===")
    print(f"Files generated: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Total size: {total_size / (1024*1024):.2f} MB")
    print(f"Time elapsed: {elapsed:.2f} seconds")
    if success_count > 0:
        print(f"Average speed: {success_count / elapsed:.2f} files/sec")
    print(f"Output directory: {output_dir.absolute()}")

    manifest_path = output_dir / "generation_manifest.json"
    manifest = {
        "timestamp": datetime.now().isoformat(),
        "num_files": success_count,
        "total_size": total_size,
        "extensions_used": list(set(ext for _, _, ext, _, _ in tasks)),
        "duplicates_requested": args.duplicates,
        "subdirs": args.subdirs,
        "seed": args.seed,
    }
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest saved to {manifest_path}")

if __name__ == "__main__":
    main()