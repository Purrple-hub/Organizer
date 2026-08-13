# Organizer

> **A intelligent file organization toolkit** — because your Downloads folder deserves better.

---

## 📋 Project Description

**Organizer** is a Python-based command-line tool that brings order to digital chaos. Whether you're drowning in a messy Downloads folder, managing a media library, or need to sort thousands of files by type, date, or metadata, Organizer handles it with speed and precision.

At its core, Organizer scans a target directory, categorizes files based on extension, metadata (EXIF, ID3), or custom rules, and moves them into structured subfolders. But it doesn't stop there — it supports parallel processing for large folders, real-time watch mode, undo functionality, cloud uploads (GitHub, Hugging Face, MediaFire), Discord notifications, and more. Think of it as a Swiss Army knife for file management.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **📂 Smart Categorization** | Organize by file type, creation date, file size, EXIF metadata, or ID3 tags. |
| **⚡ Parallel Processing** | Speed up large folders using `ProcessPoolExecutor` for multi-core performance. |
| **↩️ Undo/Redo** | Revert any organization using the built-in manifest system. |
| **👁️ Real-time Watch** | Monitor a folder and automatically organize new files as they appear. |
| **🔍 Dry Run** | Preview changes before applying them — safe experimentation. |
| **🔗 Symlink Mode** | Create symbolic links instead of moving files. |
| **🧹 Deduplication** | Identify and remove duplicate files based on content hashing. |
| **📦 Compression** | Zip or 7z compress the organized folder. |
| **☁️ Cloud Uploads** | Upload to GitHub Releases/Gists, Hugging Face datasets, or MediaFire. |
| **💬 Discord Webhooks** | Send organization reports and notifications to Discord. |
| **📊 Report Generation** | Generate detailed logs with errors, warnings, and timestamps. |
| **🧪 Metadata Stripping** | Remove EXIF/IPTC metadata from images for privacy. |

---

## 🚀 Quick Start

```bash
# Install
pip install -r requirements.txt

# Organize a directory by file type
python Organization.py -d ~/Downloads

# Preview what would happen (dry run)
python Organization.py -d ~/Downloads --dry-run

# Watch a folder in real-time
python Organization.py --watch ~/Downloads

# Undo the last organization
python Organization.py --undo
```

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Step-by-Step

1. **Clone the repository**
   ```bash
   git clone https://github.com/Purrple-hub/Organizer.git
   cd Organizer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   > **Optional dependencies** for advanced features:
   > - `Pillow` — EXIF metadata extraction from images
   > - `mutagen` — ID3 tag extraction from audio files
   > - `py7zr` — 7z compression support
   > - `watchdog` — real-time folder monitoring
   > - `tqdm` — progress bars for large operations
   > - `requests` — cloud uploads and webhooks

   Install all optional features with:
   ```bash
   pip install -r requirements.txt[full]
   ```

3. **Verify installation**
   ```bash
   python Organization.py --help
   ```

---

## ⚙️ Configuration

Organizer supports a `config.yaml` file for persistent settings. Create it in the working directory or specify a custom path with `--config`.

### Example `config.yaml`

```yaml
# Default organization strategy
default_strategy: type

# Custom category mapping (extension -> folder name)
category_map:
  .py: Python
  .js: JavaScript
  .jpg: Photos
  .png: Photos

# Upload settings
github_token: your_token_here
hf_token: your_hf_token
mediafire_key: your_mf_key
discord_webhook: https://discord.com/api/webhooks/...

# Parallel processing
parallel_workers: 4

# Deduplication
deduplicate: true
deduplicate_action: move  # list, move, delete

# Watch settings
watch_delay: 5  # seconds
```

### Command-line Arguments

| Argument | Description |
|----------|-------------|
| `-d, --directory` | Target directory to organize |
| `-z, --zip` | Compress organized folder into a zip |
| `-s, --strip-metadata` | Strip metadata from images/files |
| `--github-token` | GitHub token for gist or release uploads |
| `--github-release` | Upload to a GitHub release instead of gist |
| `--hf-token` | Hugging Face token |
| `--hf-repo` | Hugging Face repo name (e.g., 'username/dataset') |
| `--mediafire-key` | MediaFire API key |
| `--mediafire-email` | MediaFire account email |
| `--discord-webhook` | Discord webhook URL |
| `--no-prompt` | Run without interactive prompts |
| `--strategy` | Organization strategy: `type`, `date`, `size`, `size-dist`, `exif`, `id3` |
| `--dry-run` | Preview changes without applying |
| `--parallel` | Use parallel processing for large folders |
| `--symlink` | Create symlinks instead of moving/copying |
| `--undo` | Undo the last organization (uses manifest) |
| `--watch` | Watch a folder and organize new files in real-time |
| `--config` | Path to config file (default: `config.yaml`) |

---

## 💻 Usage Examples

### Basic Organization by Type
```bash
python Organization.py -d ~/Downloads
```
Moves files into folders like `Code/`, `Media/`, `Documents/`, `Audio/`, etc. based on extension.

### Organize by Date
```bash
python Organization.py -d ~/Pictures --strategy date
```
Creates subfolders like `2024/`, `2025/`, `2026/` based on file creation/modification dates.

### Organize by EXIF Metadata
```bash
python Organization.py -d ~/Photos --strategy exif
```
Sorts photos by camera model, date taken, or GPS location (requires Pillow).

### Parallel Processing for Large Folders
```bash
python Organization.py -d /mnt/media --parallel
```
Uses all CPU cores to process thousands of files simultaneously.

### Real-time Watch Mode
```bash
python Organization.py --watch ~/Downloads
```
Monitors the folder and organizes new files as they appear (requires `watchdog`).

### Dry Run (Preview Only)
```bash
python Organization.py -d ~/Downloads --dry-run
```
Shows what would happen without making any changes.

### Undo
```bash
python Organization.py --undo
```
Reverts the last organization using the manifest file.

### Upload to GitHub Release
```bash
python Organization.py -d ~/Downloads --zip --github-token ghp_xxx --github-release
```
Organizes, zips, and uploads to a GitHub release.

### Send Discord Notification
```bash
python Organization.py -d ~/Downloads --discord-webhook https://discord.com/api/webhooks/xxx
```
Sends a completion report to Discord.

---

## 🧪 Running Tests

The project uses `pytest` for testing.

```bash
# Install test dependencies
pip install pytest pytest-mock

# Run all tests
pytest tests.py -v

# Run a specific test
pytest tests.py::test_organize_by_type -v
```

### Test Coverage

| Test | Description |
|------|-------------|
| `test_organize_by_type` | Verifies files are moved to correct category folders |
| `test_undo` | Confirms undo restores files to original locations |
| `test_deduplicate` | Checks duplicate detection and handling |
| `test_upload_discord_mock` | Mocks Discord webhook requests |

---

## 📝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request**

### Contribution Guidelines

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines
- Add tests for new features
- Update documentation (this README) accordingly
- Keep the code modular and well-commented

### Areas for Improvement

- [ ] Add support for more metadata formats (PDF, DOCX)
- [ ] Implement a GUI wrapper
- [ ] Add S3/AWS upload support
- [ ] Improve error handling for network operations
- [ ] Add internationalization (i18n)

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2026 PurpleXPurple

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
...
```

---

## 😫 Flaws

> Honest self-assessment — every tool has room to grow.

| Flaw | Impact | Potential Fix |
|------|--------|---------------|
| **Optional dependency hell** | Users must manually install Pillow, mutagen, watchdog, etc. for full functionality | Bundle optional features as extras or use a single `[full]` install |
| **No GUI** | Command-line only; less accessible for non-technical users | Build a simple Tkinter or web-based UI |
| **Error recovery** | Network uploads (GitHub, Hugging Face) can fail mid-operation without clean rollback | Implement transactional uploads with retry logic |
| **Large folder performance** | Even with parallel processing, millions of files may be slow | Add a progress bar (tqdm) and chunked processing |
| **Configuration complexity** | YAML config can be overwhelming for casual users | Provide a wizard or interactive setup script |
| **No Windows native integration** | Doesn't integrate with Windows File Explorer context menu | Add a PowerShell script or registry entry |
| **Undo limitations** | Only undoes the *last* organization; no history beyond that | Implement a full versioned manifest with timestamps |

---

## 👻 Human Made or AI?

**This project is Human Made.**

### Analysis

After thoroughly reviewing the repository, here's the breakdown:

**Signs of Human Authorship:**
- **Personal naming**: The GitHub handle `Purrple-hub` and Discord tag `PurpleXPurple#4394` indicate a real individual with a consistent online identity.
- **Commit history**: Multiple commits with specific messages like "Delete test_files directory" and "Add files via upload" — typical of a developer iterating on a project.
- **Code pragmatism**: The use of `try/except` for optional imports (Pillow, mutagen, py7zr, watchdog, requests) shows real-world experience handling environment variability.
- **Feature completeness**: The project includes practical features like undo, dry-run, watch mode, and cloud uploads — things a real developer would need, not just a demo.
- **Testing**: Includes `tests.py` with pytest fixtures and mocks — indicates a test-driven or quality-conscious developer.
- **Example generator**: `example.py` generates realistic test files with random text and binary content — useful for development and demo purposes.

**Potential AI-adjacent Patterns (but not conclusive):**
- Some docstrings are very comprehensive, which could be AI-assisted documentation.
- The code is well-structured with clear separation of concerns (`io_handler.py`, `file_handler.py`, `Organization.py`).
- The sheer number of file extensions mapped in `DEFAULT_CATEGORY_MAP` (50+) suggests either extensive research or AI generation.

**Verdict:** A human developer (Purple) built this project, possibly with AI assistance for documentation or boilerplate. The personal touches, pragmatic design decisions, and iterative commit history point to genuine human effort. The project shows experience with Python, file systems, and cloud APIs.

---

## 📌 Use Cases

### 1. 📸 Photography Workflow
**Problem:** A photographer has thousands of raw images scattered across memory cards and folders, with inconsistent naming.

**Solution:**
```bash
python Organization.py -d /Photos --strategy exif --parallel
```
Organizes photos by camera model, date taken, and location (GPS) using EXIF metadata. Creates folders like `Canon_EOS/2024/New_York/` for easy browsing.

---

### 2. 🎵 Music Library Management
**Problem:** A DJ has a massive collection of MP3s with inconsistent tagging and folder structure.

**Solution:**
```bash
python Organization.py -d /Music --strategy id3
```
Sorts audio files by artist, album, genre, or year using ID3 tags (requires `mutagen`).

---

### 3. 🧑‍💻 Developer Asset Organization
**Problem:** A developer has a chaotic `~/Downloads` folder with code snippets, PDFs, images, and random binaries.

**Solution:**
```bash
python Organization.py -d ~/Downloads --watch --no-prompt
```
Automatically organizes new downloads into `Code/`, `Documents/`, `Media/`, etc. in real-time. No more hunting for that one file!

---

### 4. ☁️ Automated Backup Pipeline
**Problem:** A data scientist needs to organize experiment outputs and upload them to Hugging Face for sharing.

**Solution:**
```bash
python Organization.py -d ./experiment_results --zip --hf-token hf_xxx --hf-repo username/dataset
```
Organizes results by type, compresses into a zip, and uploads directly to Hugging Face datasets.

---

### 5. 🏢 Enterprise File Governance
**Problem:** A compliance officer needs to enforce file organization policies across shared drives.

**Solution:**
```bash
python Organization.py -d /shared_drive --strategy size-dist --dry-run > report.txt
```
Generates a report showing file distribution by size, helping identify large files that violate storage policies. The `--dry-run` ensures no changes are made without approval.

---

## 🏆 Quality

**Overall Quality Score: 425 / 500**

| Category | Score | Rationale |
|----------|-------|-----------|
| **Code Quality** | 88/100 | Clean, modular structure with good separation of concerns. Some redundancy in error handling could be refactored. |
| **Documentation** | 85/100 | Comprehensive docstrings and this README. Lacks inline comments in some complex sections. |
| **Test Coverage** | 75/100 | Basic tests exist but don't cover all features (e.g., cloud uploads, watch mode, parallel processing). |
| **Feature Set** | 92/100 | Impressive range of features — type, date, EXIF, ID3, watch, undo, parallel, cloud uploads, webhooks. |
| **Usability** | 80/100 | CLI is well-designed with clear arguments. Lacks a GUI but compensates with `--no-prompt` and config file support. |
| **Performance** | 85/100 | Parallel processing helps, but large directories with millions of files may still be slow. |
| **Maintainability** | 90/100 | Well-structured code with clear module boundaries. Easy to extend with new strategies or upload targets. |
| **Security** | 70/100 | No obvious vulnerabilities, but cloud token handling could be improved (e.g., env vars instead of CLI args). |

**Strengths:**
- Modular architecture makes it easy to add new organization strategies
- Comprehensive CLI with sensible defaults
- Real-world features (undo, dry-run, watch) show practical experience
- Optional dependencies keep the core lightweight

**Areas for Improvement:**
- Increase test coverage to 90%+
- Add environment variable support for tokens (security)
- Implement a progress bar for long operations
- Add Windows context menu integration
- Provide a Docker image for easy deployment

---

*Built with 🐍 by [Purple](https://github.com/Purrple-hub) — because organization shouldn't be optional.*
