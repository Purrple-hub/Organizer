import argparse
import sys
import os
import time
import yaml
from io_handler import Logger, IOHandler, retry_on_error
from file_handler import FileHandler
from concurrent.futures import ProcessPoolExecutor

def load_config(config_path="config.yaml"):
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def main():
    parser = argparse.ArgumentParser(description="Organize files with advanced features.")
    parser.add_argument("-d", "--directory", help="Target directory to organize")
    parser.add_argument("-z", "--zip", action="store_true", help="Compress organized folder into a zip")
    parser.add_argument("-s", "--strip-metadata", action="store_true", help="Strip metadata from images/files")
    parser.add_argument("--github-token", help="GitHub token (for gist or release)")
    parser.add_argument("--github-release", action="store_true", help="Upload to a GitHub release instead of gist")
    parser.add_argument("--hf-token", help="Hugging Face token")
    parser.add_argument("--hf-repo", help="Hugging Face repo name (e.g., 'username/dataset')")
    parser.add_argument("--mediafire-key", help="MediaFire API key")
    parser.add_argument("--mediafire-email", help="MediaFire account email")
    parser.add_argument("--discord-webhook", help="Discord webhook URL")
    parser.add_argument("--no-prompt", action="store_true", help="Run without interactive prompts")
    parser.add_argument("--strategy", default="type", choices=["type","date","size","size-dist","exif","id3"],
                        help="Organization strategy")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    parser.add_argument("--parallel", action="store_true", help="Use parallel processing for large folders")
    parser.add_argument("--symlink", action="store_true", help="Create symlinks instead of moving/copying")
    parser.add_argument("--undo", action="store_true", help="Undo the last organization (uses manifest)")
    parser.add_argument("--watch", help="Watch a folder and organize new files in real-time")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    args = parser.parse_args()

    config = load_config(args.config)
    logger = Logger()
    io = IOHandler(logger)
    handler = FileHandler(logger, config=config)

    # ---- UNDO ----
    if args.undo:
        success = handler.undo_organization()
        if success:
            logger.log_info("Organization undone.")
        else:
            logger.log_error("No manifest found or undo failed.")
        sys.exit(0)

    # ---- WATCH MODE ----
    if args.watch:
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            class OrganizeHandler(FileSystemEventHandler):
                def on_created(self, event):
                    if not event.is_directory:
                        handler.organize_files(event.src_path, dry_run=args.dry_run, move=not args.symlink)
            observer = Observer()
            observer.schedule(OrganizeHandler(), args.watch, recursive=True)
            observer.start()
            logger.log_info(f"Watching {args.watch}... Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                observer.stop()
            observer.join()
        except ImportError:
            logger.log_error("watchdog module not installed. Run: pip install watchdog")
        sys.exit(0)

    # ---- NORMAL ORGANIZATION ----
    target_dir = args.directory
    if not target_dir:
        target_dir = io.prompt_input("Enter the directory path to organize: ")
        if not target_dir:
            logger.log_error("No directory provided.")
            sys.exit(1)

    if not os.path.isdir(target_dir):
        logger.log_error(f"Directory does not exist: {target_dir}")
        sys.exit(1)

    do_zip = args.zip
    strip_meta = args.strip_metadata
    dry_run = args.dry_run
    strategy = args.strategy
    parallel = args.parallel
    symlink = args.symlink

    if not args.no_prompt:
        if not args.zip:
            do_zip = io.prompt_yes_no("Compress organized folder into a zip? (y/n): ")
        if not args.strip_metadata:
            strip_meta = io.prompt_yes_no("Strip metadata from images/files? (y/n): ")
        if not args.dry_run:
            dry_run = io.prompt_yes_no("Dry run (preview only)? (y/n): ")
        if not args.strategy:
            strategy = io.prompt_choice("Choose organization strategy:", ["type","date","size","size-dist","exif","id3"])
        if not args.parallel:
            parallel = io.prompt_yes_no("Use parallel processing for speed? (y/n): ")
        if not args.symlink:
            symlink = io.prompt_yes_no("Create symlinks instead of moving? (y/n): ")

    @retry_on_error(max_attempts=3, delay=2, logger=logger)
    def do_organize():
        return handler.organize_files(
            source_dir=target_dir,
            strategy=strategy,
            move=not symlink,
            recursive=True,
            dry_run=dry_run,
            parallel=parallel
        )

    try:
        result = do_organize()
        logger.log_info(f"Organization completed. Target folders: {list(result.keys())}")
    except Exception as e:
        logger.log_error(f"Organization failed after retries: {e}")
        sys.exit(1)

    # ---- METADATA STRIPPING ----
    if strip_meta and not dry_run:
        try:
            count = handler.strip_metadata(target_dir, recursive=True, image_only=False, sanitize_filenames=True)
            logger.log_info(f"Stripped metadata from {count} files.")
        except Exception as e:
            logger.log_error(f"Metadata stripping failed: {e}")

    # ---- COMPRESSION ----
    zip_path = None
    if do_zip and not dry_run:
        try:
            zip_path = handler.compress(target_dir, format='zip', compression_level=9)
            logger.log_info(f"Compressed to: {zip_path}")
        except Exception as e:
            logger.log_error(f"Compression failed: {e}")
            try:
                zip_path = handler.compress(target_dir, format='zip')
                logger.log_info(f"Fallback compression succeeded: {zip_path}")
            except Exception as e2:
                logger.log_error(f"Fallback compression failed: {e2}")

    # ---- UPLOADS ----
    upload_success = False
    if args.github_token and not dry_run:
        try:
            handler.upload_to_github(args.github_token, target_dir, zip_path, release=args.github_release)
            upload_success = True
        except Exception as e:
            logger.log_error(f"GitHub upload failed: {e}")

    if args.hf_token and args.hf_repo and not dry_run:
        try:
            handler.upload_to_huggingface(args.hf_token, args.hf_repo, target_dir, zip_path)
            upload_success = True
        except Exception as e:
            logger.log_error(f"Hugging Face upload failed: {e}")

    if args.mediafire_key and args.mediafire_email and not dry_run:
        try:
            handler.upload_to_mediafire(args.mediafire_key, args.mediafire_email, target_dir, zip_path)
            upload_success = True
        except Exception as e:
            logger.log_error(f"MediaFire upload failed: {e}")

    if args.discord_webhook and not dry_run and (zip_path or upload_success):
        try:
            handler.send_discord_webhook(args.discord_webhook, target_dir, zip_path)
        except Exception as e:
            logger.log_error(f"Discord webhook failed: {e}")

    # ---- REPORT ----
    report_path = logger.generate_report()
    logger.log_info(f"Report generated: {report_path}")

    # ---- DUPLICATE SCAN ----
    try:
        dup_report = handler.deduplicate(target_dir, action='list', recursive=True)
        if dup_report:
            logger.log_info(f"Found {len(dup_report)} sets of duplicate files.")
            with open(os.path.join(os.path.dirname(target_dir), 'duplicates.txt'), 'w') as f:
                for h, paths in dup_report.items():
                    f.write(f"Hash: {h}\n")
                    for p in paths:
                        f.write(f"  {p}\n")
                    f.write("\n")
    except Exception as e:
        logger.log_error(f"Duplicate scan failed: {e}")

if __name__ == "__main__":
    main()