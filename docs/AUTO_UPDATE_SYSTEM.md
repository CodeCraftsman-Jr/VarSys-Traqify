# Auto-Update System Documentation

This document describes the auto-update system for the Personal Finance Dashboard application.

## Overview

The auto-update system provides seamless updates for the desktop application using Firebase Hosting as the distribution platform. It includes:

- **Version Management**: Automatic version checking and comparison
- **Secure Downloads**: Integrity verification with checksums
- **Safe Installation**: Backup and rollback capabilities
- **User Interface**: Intuitive update notifications and progress tracking
- **Multiple Channels**: Support for stable, beta, and development releases

## Architecture

### Core Components

1. **VersionManager** (`src/core/version_manager.py`)
   - Checks for updates from Firebase Hosting
   - Compares versions and determines update availability
   - Manages update settings and preferences

2. **UpdateDownloader** (`src/core/update_downloader.py`)
   - Downloads update files with progress tracking
   - Verifies file integrity using checksums
   - Supports resume functionality

3. **UpdateInstaller** (`src/core/update_installer.py`)
   - Creates backups before installation
   - Replaces application files safely
   - Provides rollback capabilities

4. **UpdateManager** (`src/core/update_manager.py`)
   - Coordinates all update operations
   - Manages UI interactions
   - Handles automatic update checking

### User Interface Components

1. **UpdateNotificationDialog** (`src/ui/update_dialogs.py`)
   - Shows available updates to users
   - Displays changelog and update information
   - Allows users to accept, decline, or skip updates

2. **UpdateProgressDialog** (`src/ui/update_dialogs.py`)
   - Shows download and installation progress
   - Provides cancellation options
   - Displays speed and ETA information

3. **UpdateSettingsWidget** (`src/ui/update_dialogs.py`)
   - Configures update preferences
   - Manages update channels
   - Controls automatic update behavior

## Firebase Hosting Structure

```
hosting/
├── index.html                 # Update center homepage
└── updates/
    ├── stable/
    │   ├── version.json       # Latest stable version info
    │   └── *.exe             # Stable release executables
    ├── beta/
    │   ├── version.json       # Latest beta version info
    │   └── *.exe             # Beta release executables
    └── dev/
        ├── version.json       # Latest dev version info
        └── *.exe             # Development build executables
```

### Version JSON Format

```json
{
  "version": "1.0.1",
  "build_number": 10001,
  "release_date": "2025-07-13T10:00:00Z",
  "channel": "stable",
  "required": false,
  "download_url": "https://jointjourney-a12d2.web.app/updates/stable/PersonalFinanceDashboard-1.0.1.exe",
  "download_size": 52428800,
  "checksum": {
    "sha256": "abc123...",
    "md5": "def456..."
  },
  "changelog": {
    "version": "1.0.1",
    "date": "2025-07-13",
    "changes": [
      {
        "type": "feature",
        "description": "New dashboard widgets"
      },
      {
        "type": "bugfix",
        "description": "Fixed authentication issues"
      }
    ]
  },
  "system_requirements": {
    "os": "Windows 10 or later",
    "architecture": "x64",
    "ram": "4GB minimum, 8GB recommended",
    "disk_space": "500MB"
  },
  "update_notes": "This update includes new features and bug fixes.",
  "rollback_supported": true,
  "auto_update_eligible": true
}
```

## Deployment Process

### Prerequisites

1. **Firebase CLI**: Install with `npm install -g firebase-tools`
2. **Firebase Project**: Ensure you have access to the `jointjourney-a12d2` project
3. **Built Application**: Use py-auto-to-exe to build the executable

### Manual Deployment

1. **Build the application**:
   ```bash
   python build_scripts/py_auto_to_exe_build.py
   ```

2. **Deploy update**:
   ```bash
   python scripts/deploy_update.py --version 1.0.1 --channel stable --deploy
   ```

3. **Or use the batch script** (Windows):
   ```cmd
   scripts\deploy_update.bat
   ```

### Automated Deployment

Use the integrated build and deploy script:

```bash
# Build and deploy to dev channel
python scripts/build_and_deploy.py --version 1.0.1 --channel dev --deploy

# Build and deploy to stable channel (required update)
python scripts/build_and_deploy.py --version 1.0.1 --channel stable --required --deploy
```

## Update Channels

### Stable Channel
- **Purpose**: Production-ready releases
- **Auto-update**: Enabled by default
- **Testing**: Thoroughly tested
- **Frequency**: Monthly or as needed

### Beta Channel
- **Purpose**: Pre-release testing
- **Auto-update**: Disabled by default
- **Testing**: Basic testing completed
- **Frequency**: Weekly or bi-weekly

### Development Channel
- **Purpose**: Latest development builds
- **Auto-update**: Disabled by default
- **Testing**: Minimal testing
- **Frequency**: Daily or as needed

## User Experience

### Automatic Updates

1. **Background Checking**: App checks for updates every 24 hours (configurable)
2. **Notification**: Users see a notification when updates are available
3. **User Choice**: Users can accept, decline, or skip specific versions
4. **Download**: Updates download in the background with progress indication
5. **Installation**: Users can choose when to install (requires restart)

### Manual Updates

1. **Menu Access**: Help → Check for Updates
2. **Settings**: Help → Update Settings
3. **History**: Help → Update History

### Update Settings

Users can configure:
- **Auto-check frequency**: 1-168 hours
- **Update channel**: Stable, Beta, or Development
- **Auto-download**: Download updates automatically
- **Auto-install**: Install updates automatically
- **Backup creation**: Create backup before installing

## Security Features

### File Integrity
- **SHA256 checksums**: Verify downloaded files
- **MD5 checksums**: Additional verification
- **Size validation**: Ensure complete downloads

### Safe Installation
- **Backup creation**: Automatic backup before updates
- **Rollback capability**: Restore previous version if needed
- **Atomic operations**: Minimize risk of corruption

### Network Security
- **HTTPS only**: All downloads use secure connections
- **Firebase Hosting**: Leverages Google's CDN security
- **Authentication**: Uses existing Firebase authentication

## Troubleshooting

### Common Issues

1. **Update check fails**
   - Check internet connection
   - Verify Firebase project access
   - Check firewall settings

2. **Download fails**
   - Check available disk space
   - Verify download URL accessibility
   - Try manual download

3. **Installation fails**
   - Ensure application is not running
   - Check file permissions
   - Try running as administrator

4. **Rollback needed**
   - Use Help → Update History
   - Select previous backup
   - Follow restoration prompts

### Logs

Update system logs are written to:
- **Main log**: `logs/app_debug.log`
- **Update events**: Included in main application log
- **Error details**: Check log for specific error messages

## Development

### Adding New Features

1. **Version Manager**: Extend version checking logic
2. **Downloader**: Add new download sources or methods
3. **Installer**: Enhance installation process
4. **UI Components**: Create new dialogs or widgets

### Testing

1. **Local Testing**: Use development channel
2. **Beta Testing**: Deploy to beta channel
3. **Production**: Deploy to stable channel

### Configuration

Update system configuration is stored in:
- **Settings**: `updates/update_settings.json`
- **Cache**: `updates/version_cache.json`
- **Metadata**: `updates/backups/backup_metadata.json`

## Best Practices

### For Developers

1. **Version Numbering**: Use semantic versioning (e.g., 1.2.3)
2. **Changelog**: Always provide detailed changelogs
3. **Testing**: Test updates thoroughly before stable release
4. **Backup**: Always create backups for major updates

### For Users

1. **Regular Updates**: Keep the application updated
2. **Backup Data**: Backup important data before major updates
3. **Stable Channel**: Use stable channel for production work
4. **Report Issues**: Report update problems promptly

## Support

For update-related issues:
1. Check the application logs
2. Verify internet connectivity
3. Try manual update check
4. Contact support with log details
