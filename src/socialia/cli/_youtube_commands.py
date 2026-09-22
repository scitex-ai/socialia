"""CLI commands for YouTube batch operations."""

import json
import sys
from pathlib import Path
import scitex_logging as slogging
log = slogging.getLogger(__name__)


def cmd_youtube(args, output_json: bool = False) -> int:
    """Handle YouTube subcommands."""
    if args.youtube_command == "batch":
        return cmd_youtube_batch(args, output_json)
    elif args.youtube_command == "config":
        return cmd_youtube_config(args, output_json)
    elif args.youtube_command == "list":
        return cmd_youtube_list(args, output_json)
    else:
        log.error("Error: Specify youtube subcommand (batch, config, list)")
        return 1


def cmd_youtube_batch(args, output_json: bool = False) -> int:
    """Handle batch upload command."""
    from ..youtube_batch import YouTubeBatch, create_scitex_config

    config_path = getattr(args, "config", None)
    use_scitex = getattr(args, "scitex", False)
    dry_run = getattr(args, "dry_run", False)
    video_index = getattr(args, "index", None)

    # Load configuration
    if use_scitex:
        config = create_scitex_config()
        log.info("Using SciTeX demo video configuration")
    elif config_path:
        if not Path(config_path).exists():
            log.error(f"Error: Config file not found: {config_path}")
            return 1
        batch = YouTubeBatch(config_path=config_path)
        config = batch.config
    else:
        log.error("Error: Provide --config or --scitex")
        return 1

    batch = YouTubeBatch(config=config)

    # Validate
    validation = batch.validate()
    if not validation["valid"]:
        log.error("Configuration errors:")
        for error in validation["errors"]:
            log.error(f"  - {error}")
        return 1

    # Single video upload
    if video_index is not None:
        if video_index < 1 or video_index > len(batch.videos):
            log.error(f"Error: Index must be 1-{len(batch.videos)}, got {video_index}")
            return 1

        video = batch.videos[video_index - 1]
        log.info(f"\nUploading video {video_index}: {video['title']}")

        if dry_run:
            sys.stdout.write("  [DRY RUN]" + "\n")

        result = batch.upload_one(video, dry_run=dry_run)

        if output_json:
            sys.stdout.write(json.dumps(result, indent=2) + "\n")
        elif result.get("success"):
            if dry_run:
                sys.stdout.write(f"  Would upload: {result['path']}" + "\n")
                sys.stdout.write(f"  Title: {result['title']}" + "\n")
                sys.stdout.write(f"  Tags: {', '.join(result.get('tags', []))}" + "\n")
            else:
                log.info(f"  SUCCESS: {result.get('url')}")
        else:
            log.error(f"  FAILED: {result.get('error')}")
            return 1

        return 0

    # Batch upload all
    log.info(f"\nBatch uploading {len(batch.videos)} videos")
    if dry_run:
        sys.stdout.write("[DRY RUN MODE]" + "\n")
    log.info("-" * 50)

    def progress_callback(index, total, result):
        status = "OK" if result.get("success") else "FAIL"
        if dry_run:
            status = "DRY"
        log.info(f"[{index}/{total}] {status}: {result.get('title', 'Unknown')}")
        if result.get("url"):
            log.info(f"         URL: {result['url']}")
        elif result.get("error"):
            log.info(f"         Error: {result['error']}")

    results = batch.upload_all(dry_run=dry_run, callback=progress_callback)
    summary = batch.summary()

    log.info("-" * 50)
    log.info(f"Complete: {summary['successful']}/{summary['total']} successful")

    if output_json:
        sys.stdout.write(json.dumps({"results": results, "summary": summary}, indent=2) + "\n")

    if summary["urls"]:
        log.info("\nUploaded URLs:")
        for url in summary["urls"]:
            log.info(f"  {url}")

    if summary["errors"]:
        log.info("\nErrors:")
        for err in summary["errors"]:
            log.info(f"  {err['title']}: {err['error']}")

    return 0 if summary["failed"] == 0 else 1


def cmd_youtube_config(args, output_json: bool = False) -> int:
    """Generate YouTube upload configuration."""
    from ..youtube_batch import generate_config_from_directory, create_scitex_config

    directory = getattr(args, "directory", None)
    output_path = getattr(args, "output", None)
    use_scitex = getattr(args, "scitex", False)
    preset = getattr(args, "preset", "scitex-demo")

    if use_scitex:
        config = create_scitex_config(output_path=output_path)
        log.info("Generated SciTeX demo configuration")
    elif directory:
        if not Path(directory).is_dir():
            log.error(f"Error: Not a directory: {directory}")
            return 1
        config = generate_config_from_directory(
            directory, preset=preset, output_path=output_path
        )
        log.info(f"Generated configuration for {len(config['videos'])} videos")
    else:
        log.error("Error: Provide --directory or --scitex")
        return 1

    if output_json:
        sys.stdout.write(json.dumps(config, indent=2) + "\n")
    elif output_path:
        log.info(f"Saved to: {output_path}")
    else:
        # Print YAML to stdout
        import yaml

        sys.stdout.write(yaml.dump(config, default_flow_style=False, sort_keys=False) + "\n")

    return 0


def cmd_youtube_list(args, output_json: bool = False) -> int:
    """List configured videos or channel videos."""
    from ..youtube import YouTube
    from ..youtube_batch import create_scitex_config

    config_path = getattr(args, "config", None)
    use_scitex = getattr(args, "scitex", False)
    channel = getattr(args, "channel", False)
    limit = getattr(args, "limit", 10)

    if channel:
        # List videos from YouTube channel
        yt = YouTube()
        if not yt.validate_credentials():
            log.error("Error: YouTube credentials not configured")
            return 1

        result = yt.list_videos(max_results=limit)
        if not result.get("success"):
            log.error(f"Error: {result.get('error')}")
            return 1

        if output_json:
            sys.stdout.write(json.dumps(result, indent=2) + "\n")
        else:
            log.info(f"Channel videos ({result.get('count', 0)}):\n")
            for video in result.get("videos", []):
                log.info(f"  {video['title']}")
                log.info(f"    URL: {video['url']}")
                log.info(f"    Published: {video['published_at'][:10]}")
                log.info("")

        return 0

    # List videos from config
    if use_scitex:
        config = create_scitex_config()
    elif config_path:
        from ..youtube_batch import load_video_config

        config = load_video_config(config_path)
    else:
        log.error("Error: Provide --config, --scitex, or --channel")
        return 1

    videos = config.get("videos", [])

    if output_json:
        sys.stdout.write(json.dumps({"videos": videos, "count": len(videos)}, indent=2) + "\n")
    else:
        log.info(f"Configured videos ({len(videos)}):\n")
        for i, video in enumerate(videos, 1):
            path = Path(video["path"])
            exists = path.exists()
            size = f"{path.stat().st_size / 1024 / 1024:.1f}MB" if exists else "N/A"
            status = "OK" if exists else "MISSING"

            log.info(f"  {i}. {video.get('title', path.name)}")
            log.info(f"     Path: {video['path']}")
            log.info(f"     Size: {size} [{status}]")
            if video.get("tags"):
                log.info(f"     Tags: {', '.join(video['tags'][:5])}")
            log.info("")

    return 0


def add_youtube_parser(subparsers, parent_parser=None):
    """Add YouTube batch subcommand parsers."""
    youtube_parser = subparsers.add_parser(
        "youtube",
        help="YouTube batch operations",
        description="Batch upload and manage YouTube videos",
    )
    youtube_sub = youtube_parser.add_subparsers(
        dest="youtube_command", help="YouTube operations"
    )

    # batch command
    batch_parser = youtube_sub.add_parser(
        "batch",
        help="Batch upload videos",
        description="Upload multiple videos from configuration",
    )
    batch_parser.add_argument(
        "-c", "--config", type=str, help="YAML configuration file path"
    )
    batch_parser.add_argument(
        "--scitex",
        action="store_true",
        help="Use built-in SciTeX demo configuration",
    )
    batch_parser.add_argument(
        "-i",
        "--index",
        type=int,
        help="Upload only video at this index (1-based)",
    )
    batch_parser.add_argument(
        "-n", "--dry-run", action="store_true", help="Show what would be uploaded"
    )

    # config command
    config_parser = youtube_sub.add_parser(
        "config",
        help="Generate upload configuration",
        description="Create YAML configuration from directory or preset",
    )
    config_parser.add_argument(
        "-d", "--directory", type=str, help="Directory containing MP4 files"
    )
    config_parser.add_argument(
        "--scitex",
        action="store_true",
        help="Generate SciTeX demo configuration",
    )
    config_parser.add_argument("-o", "--output", type=str, help="Output YAML file path")
    config_parser.add_argument(
        "--preset",
        choices=["scitex-demo", "tutorial", "presentation"],
        default="scitex-demo",
        help="Preset for default settings",
    )

    # list command
    list_parser = youtube_sub.add_parser(
        "list",
        help="List videos",
        description="List configured videos or channel uploads",
    )
    list_parser.add_argument(
        "-c", "--config", type=str, help="YAML configuration file path"
    )
    list_parser.add_argument(
        "--scitex",
        action="store_true",
        help="List SciTeX demo videos",
    )
    list_parser.add_argument(
        "--channel",
        action="store_true",
        help="List videos from your YouTube channel",
    )
    list_parser.add_argument(
        "-l", "--limit", type=int, default=10, help="Number of videos to list"
    )

    return youtube_parser
