"""
file_handler.py – Core engine for file organization.
Supports: rich category mapping, parallel processing, undo/redo, EXIF/ID3 metadata,
compression, deduplication, batch rename, report generation, and uploads to
GitHub, Hugging Face, MediaFire, and Discord webhooks.
"""

import os
import shutil
import zipfile
import hashlib
import re
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Callable, Union
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

# Optional imports
try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import py7zr
    SEVENZ_AVAILABLE = True
except ImportError:
    SEVENZ_AVAILABLE = False

try:
    import mutagen
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class FileHandler:
    """
    Main class for file operations.
    """

    # Default category mapping (extension -> folder name)
    DEFAULT_CATEGORY_MAP = {
        # Code
        '.py': 'Code', '.java': 'Code', '.lua': 'Code', '.luau': 'Code',
        '.c': 'Code', '.cpp': 'Code', '.h': 'Code', '.cs': 'Code',
        '.go': 'Code', '.rs': 'Code', '.rb': 'Code', '.pl': 'Code',
        '.sh': 'Code', '.bat': 'Code', '.ps1': 'Code', '.r': 'Code',
        '.swift': 'Code', '.kt': 'Code', '.scala': 'Code', '.clj': 'Code',
        '.exs': 'Code', '.elm': 'Code', '.hs': 'Code', '.erl': 'Code',
        '.cr': 'Code', '.nim': 'Code', '.zig': 'Code',

        # Web (HTML + JS + CSS + TS + PHP etc.)
        '.html': 'Web', '.htm': 'Web', '.js': 'Web', '.css': 'Web',
        '.php': 'Web', '.asp': 'Web', '.aspx': 'Web', '.jsp': 'Web',
        '.ts': 'Web', '.jsx': 'Web', '.tsx': 'Web', '.vue': 'Web',
        '.svelte': 'Web',

        # Data
        '.csv': 'Data', '.parquet': 'Data', '.sql': 'Data',
        '.json': 'Data', '.xml': 'Data', '.yaml': 'Data', '.yml': 'Data',
        '.xls': 'Data', '.xlsx': 'Data', '.tsv': 'Data',
        '.feather': 'Data', '.orc': 'Data', '.avro': 'Data',

        # Logs
        '.log': 'Logs',

        # Text (non‑code)
        '.txt': 'Text', '.md': 'Text', '.rst': 'Text',

        # Documents
        '.pdf': 'Documents', '.doc': 'Documents', '.docx': 'Documents',
        '.ppt': 'Documents', '.pptx': 'Documents', '.odt': 'Documents',
        '.ods': 'Documents', '.odp': 'Documents', '.rtf': 'Documents',
        '.tex': 'Documents',

        # Media - Images
        '.png': 'Media', '.jpg': 'Media', '.jpeg': 'Media', '.gif': 'Media',
        '.bmp': 'Media', '.tiff': 'Media', '.svg': 'Media', '.ico': 'Media',
        '.cur': 'Media',

        # Media - Videos
        '.mp4': 'Media', '.avi': 'Media', '.mov': 'Media', '.mkv': 'Media',
        '.webm': 'Media', '.flv': 'Media', '.wmv': 'Media', '.m4v': 'Media',

        # Audio
        '.mp3': 'Audio', '.wav': 'Audio', '.flac': 'Audio', '.aac': 'Audio',
        '.ogg': 'Audio', '.wma': 'Audio', '.m4a': 'Audio',

        # Archives
        '.zip': 'Archives', '.rar': 'Archives', '.7z': 'Archives',
        '.tar': 'Archives', '.gz': 'Archives', '.bz2': 'Archives',
        '.xz': 'Archives', '.zst': 'Archives',

        # Executables
        '.exe': 'Executables', '.msi': 'Executables', '.app': 'Executables',
        '.dll': 'Executables', '.so': 'Executables', '.dylib': 'Executables',
        '.bin': 'Executables',

        # Libraries
        '.lib': 'Libraries', '.a': 'Libraries', '.o': 'Libraries',

        # Disk Images
        '.iso': 'DiskImages', '.img': 'DiskImages', '.dmg': 'DiskImages',

        # Fonts
        '.ttf': 'Fonts', '.otf': 'Fonts',

        # Security
        '.key': 'Security', '.pem': 'Security', '.crt': 'Security',
        '.cer': 'Security', '.pfx': 'Security',

        # Databases
        '.db': 'Databases', '.sqlite': 'Databases', '.sqlite3': 'Databases',
        '.mdb': 'Databases', '.accdb': 'Databases',

        # Config
        '.cfg': 'Config', '.conf': 'Config', '.ini': 'Config', '.env': 'Config',

        # Temporary
        '.tmp': 'Temporary', '.temp': 'Temporary', '.cache': 'Temporary',
    }

    def __init__(self, logger=None, config=None):
        self.logger = logger
        self.stats = {'processed': 0, 'errors': 0, 'skipped': 0}
        self.config = config or {}
        self.manifest_path = os.path.join(os.getcwd(), 'organization_manifest.json')
        self._load_manifest()

    # ------------------------------------------------------------------
    # MANIFEST / UNDO
    # ------------------------------------------------------------------
    def _load_manifest(self):
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path, 'r') as f:
                self.manifest = json.load(f)
        else:
            self.manifest = {'moves': [], 'timestamp': None}

    def _save_manifest(self):
        with open(self.manifest_path, 'w') as f:
            json.dump(self.manifest, f, indent=2)

    def _record_move(self, src, dst):
        self.manifest['moves'].append({'src': src, 'dst': dst, 'time': datetime.now().isoformat()})
        self.manifest['timestamp'] = datetime.now().isoformat()
        self._save_manifest()

    def undo_organization(self) -> bool:
        """Revert the last organization (move files back)."""
        if not self.manifest['moves']:
            return False
        for move in reversed(self.manifest['moves']):
            src = move['src']
            dst = move['dst']
            if os.path.exists(dst):
                os.makedirs(os.path.dirname(src), exist_ok=True)
                shutil.move(dst, src)
                self._log(f"Undo: moved {dst} -> {src}")
        self.manifest['moves'] = []
        self._save_manifest()
        return True

    # ------------------------------------------------------------------
    # CATEGORY MAP
    # ------------------------------------------------------------------
    def _get_category_map(self):
        return self.config.get('category_map', self.DEFAULT_CATEGORY_MAP)

    # ------------------------------------------------------------------
    # CORE ORGANIZE
    # ------------------------------------------------------------------
    def organize_files(self,
                       source_dir: str,
                       dest_root: Optional[str] = None,
                       strategy: str = 'type',
                       move: bool = True,
                       recursive: bool = True,
                       dry_run: bool = False,
                       prefix_with_date: bool = False,
                       parallel: bool = False) -> Dict[str, List[str]]:
        """
        Organize files into subfolders based on extension (or other strategy).
        Returns dict of {target_folder: [list_of_files]}.
        """
        if dest_root is None:
            dest_root = os.path.join(source_dir, f"organized_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        if not dry_run:
            os.makedirs(dest_root, exist_ok=True)

        # Collect files (skip dest_root)
        items = []
        if recursive:
            for root, _, files in os.walk(source_dir):
                if root.startswith(dest_root):
                    continue
                for f in files:
                    items.append(os.path.join(root, f))
        else:
            items = [os.path.join(source_dir, f) for f in os.listdir(source_dir)
                     if os.path.isfile(os.path.join(source_dir, f)) and
                     not os.path.join(source_dir, f).startswith(dest_root)]

        # Decide parallel or sequential
        if parallel and len(items) > 100:
            return self._organize_parallel(items, dest_root, strategy, move, dry_run, prefix_with_date)
        else:
            return self._organize_sequential(items, dest_root, strategy, move, dry_run, prefix_with_date)

    def _organize_sequential(self, items, dest_root, strategy, move, dry_run, prefix_with_date):
        result = {}
        for file_path in items:
            try:
                dest_path, target_folder = self._get_dest_path(file_path, dest_root, strategy, prefix_with_date)
                if not dry_run:
                    os.makedirs(target_folder, exist_ok=True)
                    # Handle collisions
                    base = os.path.basename(dest_path)
                    counter = 1
                    while os.path.exists(dest_path):
                        name, ext2 = os.path.splitext(base)
                        dest_path = os.path.join(target_folder, f"{name}_{counter}{ext2}")
                        counter += 1
                    if move:
                        shutil.move(file_path, dest_path)
                    else:
                        shutil.copy2(file_path, dest_path)
                    self._record_move(file_path, dest_path)
                    self._log(f"Moved {file_path} -> {dest_path}")
                result.setdefault(target_folder, []).append(file_path)
                self.stats['processed'] += 1
            except Exception as e:
                self._log(f"Error processing {file_path}: {e}", level='error')
                self.stats['errors'] += 1
        return result

    def _organize_parallel(self, items, dest_root, strategy, move, dry_run, prefix_with_date):
        result = {}
        with ProcessPoolExecutor() as executor:
            futures = []
            for file_path in items:
                future = executor.submit(
                    self._process_single_file,
                    file_path, dest_root, strategy, prefix_with_date, move, dry_run
                )
                futures.append(future)
            for future in as_completed(futures):
                try:
                    dest_path, target_folder, src = future.result()
                    if dest_path:
                        result.setdefault(target_folder, []).append(src)
                        self.stats['processed'] += 1
                        # Record move in main process (cannot do in child)
                        if not dry_run and os.path.exists(dest_path):
                            self._record_move(src, dest_path)
                except Exception as e:
                    self._log(f"Parallel processing error: {e}", level='error')
                    self.stats['errors'] += 1
        return result

    def _process_single_file(self, file_path, dest_root, strategy, prefix_with_date, move, dry_run):
        """Helper for parallel processing – returns (dest_path, target_folder, src)."""
        try:
            dest_path, target_folder = self._get_dest_path(file_path, dest_root, strategy, prefix_with_date)
            if not dry_run:
                os.makedirs(target_folder, exist_ok=True)
                base = os.path.basename(dest_path)
                counter = 1
                while os.path.exists(dest_path):
                    name, ext2 = os.path.splitext(base)
                    dest_path = os.path.join(target_folder, f"{name}_{counter}{ext2}")
                    counter += 1
                if move:
                    shutil.move(file_path, dest_path)
                else:
                    shutil.copy2(file_path, dest_path)
            return dest_path, target_folder, file_path
        except Exception as e:
            return None, None, None

    def _get_dest_path(self, file_path, dest_root, strategy, prefix_with_date):
        """Determine destination path and target folder based on strategy."""
        ext = os.path.splitext(file_path)[1].lower()
        category = self._get_category_map().get(ext, 'Other')

        # Override based on strategy
        if strategy == 'date':
            mtime = os.path.getmtime(file_path)
            category = datetime.fromtimestamp(mtime).strftime('%Y-%m')
        elif strategy == 'size':
            size = os.path.getsize(file_path)
            if size < 1024*1024:
                category = 'small_<1MB'
            elif size < 100*1024*1024:
                category = 'medium_1-100MB'
            else:
                category = 'large_>100MB'
        elif strategy == 'size-dist':
            size = os.path.getsize(file_path)
            if size < 1024:
                category = '<1KB'
            elif size < 1024*1024:
                category = '1KB-1MB'
            elif size < 10*1024*1024:
                category = '1-10MB'
            elif size < 100*1024*1024:
                category = '10-100MB'
            elif size < 1000*1024*1024:
                category = '100MB-1GB'
            else:
                category = '>1GB'
        elif strategy == 'exif' and PIL_AVAILABLE:
            try:
                img = Image.open(file_path)
                exif = img._getexif()
                if exif:
                    for tag, value in exif.items():
                        if TAGS.get(tag) == 'DateTimeOriginal':
                            date_str = value.replace(':', '-').split(' ')[0]
                            category = date_str
                            break
            except:
                pass
        elif strategy == 'id3' and MUTAGEN_AVAILABLE:
            try:
                audio = mutagen.File(file_path)
                if audio:
                    if 'TPE1' in audio:
                        category = str(audio['TPE1'])
                    elif 'TIT2' in audio:
                        category = str(audio['TIT2'])
            except:
                pass

        if prefix_with_date:
            today = datetime.now().strftime('%Y%m%d')
            target_folder = os.path.join(dest_root, f"{today}_{category}")
        else:
            target_folder = os.path.join(dest_root, category)

        dest_path = os.path.join(target_folder, os.path.basename(file_path))
        return dest_path, target_folder

    # ------------------------------------------------------------------
    # COMPRESS
    # ------------------------------------------------------------------
    def compress(self,
                 source_dir: str,
                 output_path: Optional[str] = None,
                 format: str = 'zip',
                 password: Optional[str] = None,
                 split_size: Optional[int] = None,
                 exclude_patterns: List[str] = None,
                 compression_level: int = 6,
                 recursive: bool = True) -> str:
        """Compress a folder into a zip, 7z, or tar archive."""
        if output_path is None:
            base = os.path.basename(source_dir)
            output_path = os.path.join(os.path.dirname(source_dir), f"{base}.{format}")
        if format == 'zip':
            with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED,
                                 compresslevel=compression_level) as zf:
                for root, _, files in os.walk(source_dir):
                    if not recursive and root != source_dir:
                        continue
                    for f in files:
                        full = os.path.join(root, f)
                        if exclude_patterns and any(re.search(p, full) for p in exclude_patterns):
                            continue
                        arcname = os.path.relpath(full, start=os.path.dirname(source_dir))
                        zf.write(full, arcname)
        elif format == '7z' and SEVENZ_AVAILABLE:
            import py7zr
            with py7zr.SevenZipFile(output_path, 'w', password=password,
                                     compression_level=compression_level) as archive:
                archive.writeall(source_dir, arcname=os.path.basename(source_dir))
        else:
            raise NotImplementedError(f"Format {format} not supported or missing library.")
        self._log(f"Compressed {source_dir} -> {output_path}")
        return output_path

    # ------------------------------------------------------------------
    # METADATA STRIP
    # ------------------------------------------------------------------
    def strip_metadata(self,
                       target_path: str,
                       recursive: bool = True,
                       image_only: bool = False,
                       sanitize_filenames: bool = False,
                       remove_hidden_attributes: bool = False) -> int:
        """Strip EXIF from images, optionally sanitize filenames, remove hidden flags."""
        count = 0
        items = []
        if os.path.isfile(target_path):
            items = [target_path]
        elif recursive:
            for root, _, files in os.walk(target_path):
                for f in files:
                    items.append(os.path.join(root, f))
        else:
            items = [os.path.join(target_path, f) for f in os.listdir(target_path) if os.path.isfile(os.path.join(target_path, f))]

        for path in items:
            try:
                if not image_only or path.lower().endswith(('.jpg','.jpeg','.png','.tiff','.bmp')):
                    if PIL_AVAILABLE and path.lower().endswith(('.jpg','.jpeg','.tiff','.png')):
                        img = Image.open(path)
                        data = list(img.getdata())
                        new_img = Image.new(img.mode, img.size)
                        new_img.putdata(data)
                        new_img.save(path)
                        self._log(f"Stripped EXIF from {path}")
                        count += 1
                    elif os.name == 'nt' and remove_hidden_attributes:
                        import ctypes
                        FILE_ATTRIBUTE_HIDDEN = 0x2
                        FILE_ATTRIBUTE_SYSTEM = 0x4
                        attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
                        if attrs & (FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM):
                            attrs &= ~(FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)
                            ctypes.windll.kernel32.SetFileAttributesW(path, attrs)
                if sanitize_filenames:
                    dirname = os.path.dirname(path)
                    basename = os.path.basename(path)
                    newname = re.sub(r'[^a-zA-Z0-9._-]', '_', basename)
                    if newname != basename:
                        newpath = os.path.join(dirname, newname)
                        os.rename(path, newpath)
                        self._log(f"Sanitized filename: {path} -> {newpath}")
            except Exception as e:
                self._log(f"Metadata strip failed for {path}: {e}", level='error')
        return count

    # ------------------------------------------------------------------
    # DEDUPLICATE
    # ------------------------------------------------------------------
    def deduplicate(self,
                    source_dir: str,
                    action: str = 'move',
                    dest_dir: Optional[str] = None,
                    method: str = 'md5',
                    dry_run: bool = False,
                    recursive: bool = True,
                    keep_newest: bool = True) -> Dict[str, List[str]]:
        """Find duplicate files and perform action (move, copy, delete, list)."""
        hashes = {}
        duplicates = {}
        items = []
        if recursive:
            for root, _, files in os.walk(source_dir):
                for f in files:
                    items.append(os.path.join(root, f))
        else:
            items = [os.path.join(source_dir, f) for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]

        for path in items:
            try:
                size = os.path.getsize(path)
                if method == 'size_only':
                    key = str(size)
                else:
                    with open(path, 'rb') as f:
                        digest = hashlib.new(method, f.read()).hexdigest()
                    key = f"{size}_{digest}"
                hashes.setdefault(key, []).append(path)
            except Exception as e:
                self._log(f"Error hashing {path}: {e}", level='error')

        for h, paths in hashes.items():
            if len(paths) > 1:
                duplicates[h] = paths
                if action != 'list' and not dry_run:
                    if keep_newest:
                        paths.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                    else:
                        paths.sort(key=lambda p: os.path.getmtime(p))
                    keeper = paths[0]
                    for dup in paths[1:]:
                        if action == 'delete':
                            os.remove(dup)
                            self._log(f"Deleted duplicate {dup}")
                        elif action == 'move' and dest_dir:
                            os.makedirs(dest_dir, exist_ok=True)
                            shutil.move(dup, os.path.join(dest_dir, os.path.basename(dup)))
                            self._log(f"Moved duplicate {dup} -> {dest_dir}")
                        elif action == 'copy' and dest_dir:
                            os.makedirs(dest_dir, exist_ok=True)
                            shutil.copy2(dup, os.path.join(dest_dir, os.path.basename(dup)))
                            self._log(f"Copied duplicate {dup} -> {dest_dir}")
        return duplicates

    # ------------------------------------------------------------------
    # BATCH RENAME
    # ------------------------------------------------------------------
    def batch_rename(self,
                     target_dir: str,
                     pattern: str,
                     replacement: str = '',
                     use_regex: bool = False,
                     dry_run: bool = False,
                     recursive: bool = True,
                     include_ext: bool = False) -> Dict[str, str]:
        """Rename files using pattern replacement (string or regex)."""
        changes = {}
        items = []
        if recursive:
            for root, _, files in os.walk(target_dir):
                for f in files:
                    items.append(os.path.join(root, f))
        else:
            items = [os.path.join(target_dir, f) for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))]

        for path in items:
            dirname = os.path.dirname(path)
            basename = os.path.basename(path)
            name, ext = os.path.splitext(basename)
            if not include_ext:
                new_name = re.sub(pattern, replacement, name) if use_regex else name.replace(pattern, replacement)
                new_basename = new_name + ext
            else:
                new_basename = re.sub(pattern, replacement, basename) if use_regex else basename.replace(pattern, replacement)
            if new_basename != basename:
                new_path = os.path.join(dirname, new_basename)
                if not dry_run:
                    os.rename(path, new_path)
                changes[path] = new_path
                self._log(f"Renamed {path} -> {new_path}")
        return changes

    # ------------------------------------------------------------------
    # GENERATE REPORT (without writing to file, just dict)
    # ------------------------------------------------------------------
    def generate_report(self,
                        target_dir: str,
                        recursive: bool = True,
                        include_duplicates: bool = True,
                        include_metadata: bool = False,
                        output_file: Optional[str] = None) -> Dict:
        """Generate a report dictionary (and optionally write to file)."""
        stats = {'total_files': 0, 'total_size': 0, 'extensions': {}, 'size_buckets': {}}
        hashes = {}
        items = []
        if recursive:
            for root, _, files in os.walk(target_dir):
                for f in files:
                    items.append(os.path.join(root, f))
        else:
            items = [os.path.join(target_dir, f) for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))]

        for path in items:
            size = os.path.getsize(path)
            stats['total_files'] += 1
            stats['total_size'] += size
            ext = os.path.splitext(path)[1].lower()
            stats['extensions'][ext] = stats['extensions'].get(ext, 0) + 1
            if size < 1024:
                bucket = '<1KB'
            elif size < 1024*1024:
                bucket = '1KB-1MB'
            elif size < 10*1024*1024:
                bucket = '1-10MB'
            elif size < 100*1024*1024:
                bucket = '10-100MB'
            else:
                bucket = '>100MB'
            stats['size_buckets'][bucket] = stats['size_buckets'].get(bucket, 0) + 1
            if include_duplicates:
                with open(path, 'rb') as f:
                    digest = hashlib.md5(f.read()).hexdigest()
                hashes.setdefault(digest, []).append(path)

        if include_duplicates:
            stats['duplicates'] = {h: paths for h, paths in hashes.items() if len(paths) > 1}
            stats['duplicate_count'] = sum(len(v) - 1 for v in stats['duplicates'].values())

        if output_file:
            with open(output_file, 'w') as f:
                json.dump(stats, f, indent=2, default=str)
            self._log(f"Report saved to {output_file}")
        return stats

    # ------------------------------------------------------------------
    # CLEAN TEMP FILES
    # ------------------------------------------------------------------
    def clean_temp(self,
                   target_dir: str,
                   older_than_days: int = 30,
                   pattern: str = r'.*\.tmp$|.*~$|^~.*',
                   dry_run: bool = False,
                   recursive: bool = True,
                   also_empty_dirs: bool = True) -> int:
        """Delete temporary files older than N days."""
        deleted = 0
        now = time.time()
        threshold = now - older_than_days * 86400
        items = []
        if recursive:
            for root, _, files in os.walk(target_dir):
                for f in files:
                    items.append(os.path.join(root, f))
        else:
            items = [os.path.join(target_dir, f) for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))]

        for path in items:
            if re.search(pattern, os.path.basename(path), re.IGNORECASE):
                if os.path.getmtime(path) < threshold:
                    if not dry_run:
                        os.remove(path)
                        self._log(f"Deleted temp file {path}")
                    deleted += 1
        if also_empty_dirs and not dry_run:
            for root, dirs, files in os.walk(target_dir, topdown=False):
                if root != target_dir and not os.listdir(root):
                    os.rmdir(root)
                    self._log(f"Removed empty dir {root}")
        return deleted

    # ------------------------------------------------------------------
    # UPLOAD METHODS
    # ------------------------------------------------------------------
    def upload_to_github(self, token: str, target_dir: str, zip_path: str = None, release: bool = False):
        """Upload report (or zip) to a GitHub gist or release."""
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests module required")
        report_path = os.path.join(os.getcwd(), "report.txt")
        if not os.path.exists(report_path):
            report_path = self.generate_report(target_dir, output_file=report_path)
        with open(report_path, 'r') as f:
            report_content = f.read()
        if release:
            # Upload to a release (requires repo, tag, etc.) – simplified example
            # Actually we'd need more info; we'll implement a gist for simplicity.
            self._log("GitHub release upload not fully implemented; falling back to gist.", level='warning')
        url = "https://api.github.com/gists"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        payload = {
            "description": "Organization Report",
            "public": False,
            "files": {"report.txt": {"content": report_content}}
        }
        if zip_path and os.path.exists(zip_path):
            import base64
            with open(zip_path, 'rb') as f:
                zip_data = base64.b64encode(f.read()).decode('utf-8')
            payload["files"]["organized.zip"] = {"content": zip_data}
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 201:
            self._log(f"Uploaded to GitHub gist: {response.json().get('html_url')}")
        else:
            raise Exception(f"GitHub upload failed: {response.text}")

    def upload_to_huggingface(self, token: str, repo: str, target_dir: str, zip_path: str = None):
        """Upload report or zip to a Hugging Face dataset."""
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests module required")
        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://huggingface.co/api/datasets/{repo}/upload"
        files = []
        if zip_path and os.path.exists(zip_path):
            files.append(('files', (os.path.basename(zip_path), open(zip_path, 'rb'))))
        else:
            report_path = os.path.join(os.getcwd(), "report.txt")
            if os.path.exists(report_path):
                files.append(('files', ('report.txt', open(report_path, 'rb'))))
        response = requests.post(url, headers=headers, files=files)
        if response.status_code == 201:
            self._log("Uploaded to Hugging Face successfully.")
        else:
            raise Exception(f"Hugging Face upload failed: {response.text}")

    def upload_to_mediafire(self, api_key: str, email: str, target_dir: str, zip_path: str = None):
        """Upload report or zip to MediaFire."""
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests module required")
        files = []
        if zip_path and os.path.exists(zip_path):
            files.append(('file', open(zip_path, 'rb')))
        else:
            report_path = os.path.join(os.getcwd(), "report.txt")
            if os.path.exists(report_path):
                files.append(('file', open(report_path, 'rb')))
        data = {'api_key': api_key, 'email': email}
        response = requests.post('https://www.mediafire.com/api/upload/upload.php', data=data, files=files)
        if response.status_code == 200:
            self._log("Uploaded to MediaFire successfully.")
        else:
            raise Exception(f"MediaFire upload failed: {response.text}")

    def send_discord_webhook(self, webhook_url: str, target_dir: str, zip_path: str = None):
        """Send a Discord webhook with report/zip as attachment."""
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests module required")
        content = f"Organization completed for `{target_dir}`"
        files = []
        if zip_path and os.path.exists(zip_path):
            files.append(('file', (os.path.basename(zip_path), open(zip_path, 'rb'))))
        else:
            report_path = os.path.join(os.getcwd(), "report.txt")
            if os.path.exists(report_path):
                files.append(('file', ('report.txt', open(report_path, 'rb'))))
        data = {'content': content}
        response = requests.post(webhook_url, data=data, files=files)
        if response.status_code == 204:
            self._log("Discord webhook sent.")
        else:
            raise Exception(f"Discord webhook failed: {response.text}")

    # ------------------------------------------------------------------
    # LOGGING HELPER
    # ------------------------------------------------------------------
    def _log(self, msg, level='info'):
        if self.logger:
            if level == 'error':
                self.logger.log_error(msg)
            else:
                self.logger.log_info(msg)
        else:
            print(f"[{level.upper()}] {msg}")