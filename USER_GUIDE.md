# YouTube Video Documentation System - User Guide

## Overview

The YouTube Video Documentation System is a comprehensive Python application designed for journalistic documentation of police misconduct incidents. The system automatically searches YouTube for relevant videos, downloads them, filters content based on configurable criteria, and creates organized compilation videos with proper source attribution.

## Features

### Core Functionality
- **Automated YouTube Search**: Searches across 29 predefined keywords related to police misconduct
- **Intelligent Filtering**: Filters videos by date range (2010-present), region (US only), duration, and view count
- **Content Categorization**: Automatically categorizes videos into incident types (traffic stops, protests, arrests, etc.)
- **Video Download**: Downloads videos in best available quality with metadata preservation
- **Compilation Creation**: Creates organized compilation videos with source attribution overlays
- **Comprehensive Reporting**: Generates detailed reports on search results, filtering statistics, and compilation metrics

### Key Capabilities
- **Duplicate Detection**: Identifies and removes duplicate videos based on content similarity
- **Quality Control**: Validates video files and ensures compilation integrity
- **Source Attribution**: Adds text overlays with video source information for transparency
- **Batch Processing**: Handles large-scale video processing with progress tracking
- **Session Management**: Maintains detailed logs and session data for reproducibility

## Installation

### Prerequisites
- Python 3.11 or higher
- FFmpeg (automatically installed with MoviePy)
- Sufficient disk space for video storage

### Required Dependencies
```bash
pip3 install yt-dlp moviepy PyYAML
```

### System Setup
1. Clone or download the project files
2. Ensure all dependencies are installed
3. Verify the configuration file (`config.yaml`) is properly set up

## Configuration

The system uses a YAML configuration file (`config.yaml`) to customize behavior:

### Search Settings
```yaml
search_settings:
  keywords: [list of search terms]
  start_date: "2010-01-01"
  end_date: "today"
  region: "US"
  language: "en"
  max_results_per_keyword: 500
  request_delay: 1.0
```

### Content Filtering
```yaml
content_filter:
  min_duration_seconds: 30
  max_duration_seconds: 3600
  min_views: 100
  required_keywords: ["police"]
  excluded_keywords: ["fake", "parody"]
  min_resolution_height: 240
  max_file_size_mb: 500
```

### Video Compilation
```yaml
compilation_settings:
  output_dir: "compilations"
  target_duration_minutes: 15
  max_duration_minutes: 20
  min_duration_minutes: 10
  video_quality: "720p"
  attribution_duration: 5
  attribution_position: "bottom"
```

### Categorization
```yaml
categorization:
  categories:
    traffic_stop:
      keywords: ["traffic stop", "pulled over", "speeding"]
      priority: 1
    protest:
      keywords: ["protest", "demonstration", "blm"]
      priority: 2
    # Additional categories...
```

## Usage

### Command Line Interface

The system provides several operation modes:

#### Full Pipeline
Runs the complete process from search to compilation:
```bash
python3 main.py --max-videos 50
```

#### Search Only
Performs only the video search phase:
```bash
python3 main.py --mode search --max-videos 100
```

#### Download from File
Downloads videos from a saved search results file:
```bash
python3 main.py --mode download --input-file search_results.json
```

#### Compile Existing Downloads
Creates compilations from already downloaded videos:
```bash
python3 main.py --mode compile --downloads-dir downloads/
```

### Command Line Options

- `--config, -c`: Configuration file path (default: config.yaml)
- `--mode, -m`: Operation mode (full, search, download, compile)
- `--max-videos, -n`: Maximum number of videos to process
- `--input-file, -i`: Input file for download or compile modes
- `--downloads-dir, -d`: Downloads directory for compile mode

## Output Structure

The system creates organized output directories:

```
video_documentation_system/
├── sessions/
│   └── YYYYMMDD_HHMMSS/
│       ├── search_results.json
│       ├── filter_report.json
│       ├── download_report.json
│       ├── compilation_report.json
│       └── pipeline_results.json
├── downloads/
│   ├── raw_videos/
│   └── metadata/
├── compilations/
│   └── [category]_compilation_[number]_[timestamp].mp4
└── logs/
    └── app.log
```

## Workflow Process

### 1. Video Search Phase
- Searches YouTube using predefined keywords
- Applies regional and temporal filters
- Removes duplicate results
- Saves search results to JSON file

### 2. Content Filtering Phase
- Filters videos by duration, views, and quality criteria
- Applies keyword-based content filtering
- Categorizes videos by incident type
- Generates filtering statistics report

### 3. Video Download Phase
- Downloads videos in best available quality
- Preserves video metadata and subtitles
- Downloads thumbnails for reference
- Validates downloaded files

### 4. Video Compilation Phase
- Groups videos by category and duration targets
- Creates compilation videos with source attribution
- Adds text overlays with video source information
- Generates final compilation reports

## Reports and Analytics

The system generates comprehensive reports:

### Search Report
- Total videos found per keyword
- Duplicate removal statistics
- Regional and temporal filtering results

### Filter Report
- Content filtering statistics
- Category distribution analysis
- Quality metrics and validation results

### Download Report
- Download success/failure rates
- File size and quality information
- Error logs and retry attempts

### Compilation Report
- Number of compilations created
- Source video counts per compilation
- Total duration and file sizes

## Best Practices

### Performance Optimization
- Use `--max-videos` parameter to limit processing for testing
- Monitor disk space usage during large-scale operations
- Consider running overnight for extensive video collections

### Quality Control
- Review filter reports to adjust criteria as needed
- Validate compilation outputs before distribution
- Maintain backup copies of original downloaded videos

### Legal and Ethical Considerations
- Ensure compliance with YouTube Terms of Service
- Respect copyright and fair use principles
- Include proper source attribution in all compilations
- Consider privacy implications when processing content

## Troubleshooting

### Common Issues

#### Search Phase Problems
- **No videos found**: Check keyword relevance and date ranges
- **API rate limiting**: Increase request_delay in configuration
- **Regional filtering too restrictive**: Adjust US indicator keywords

#### Download Phase Problems
- **Download failures**: Check internet connectivity and disk space
- **Quality issues**: Verify yt-dlp is up to date
- **Metadata errors**: Ensure proper file permissions

#### Compilation Phase Problems
- **Memory issues**: Reduce target compilation duration
- **Video codec errors**: Verify FFmpeg installation
- **Attribution overlay problems**: Check text encoding settings

### Error Recovery
- Use session directories to resume interrupted operations
- Check log files for detailed error information
- Validate configuration file syntax before running

## Advanced Usage

### Custom Keyword Lists
Modify the keywords list in `config.yaml` to focus on specific types of incidents or geographic regions.

### Batch Processing
For large-scale operations, consider running the system in phases:
1. Search and save results
2. Filter and download in smaller batches
3. Create compilations from downloaded content

### Integration with Other Tools
The system outputs standard JSON files that can be integrated with other analysis tools or databases.

## Support and Maintenance

### Regular Maintenance
- Update yt-dlp regularly for continued YouTube compatibility
- Monitor and clean up old session files
- Review and update keyword lists based on current events

### Performance Monitoring
- Check log files for errors and warnings
- Monitor disk usage and cleanup old downloads
- Validate compilation quality periodically

## Legal Disclaimer

This tool is designed for journalistic and educational purposes. Users are responsible for:
- Complying with YouTube Terms of Service
- Respecting copyright and fair use laws
- Ensuring proper attribution of source material
- Following applicable privacy and data protection regulations

The system is provided as-is without warranty. Users assume all responsibility for its use and any resulting content.
