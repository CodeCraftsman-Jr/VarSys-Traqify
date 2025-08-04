#!/usr/bin/env python3
"""
Deploy Traqify setup to Firebase Hosting
"""

import os
import sys
import shutil
import json
import logging
from pathlib import Path
from datetime import datetime

def setup_logging():
    """Setup logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def prepare_hosting_files(logger):
    """Prepare files for Firebase Hosting (ZIP + version.txt approach)"""
    try:
        import zipfile

        project_root = Path(__file__).parent.parent
        hosting_dir = project_root / "hosting"
        dist_dir = project_root / "dist"

        # Create hosting directory structure
        apps_dir = hosting_dir / "apps"
        apps_dir.mkdir(exist_ok=True)

        # Find the setup file
        installer_dir = dist_dir / "installer"
        setup_files = list(installer_dir.glob("Traqify_Setup_*.exe"))

        if not setup_files:
            logger.error("No setup file found in dist/installer/")
            logger.error("Please build the installer first using Inno Setup")
            return False

        setup_file = setup_files[0]  # Get the first (should be only one)
        logger.info(f"Found setup file: {setup_file}")

        # Create ZIP file containing the setup
        zip_filename = f"Traqify_v1.0.1_Update.zip"
        zip_path = apps_dir / zip_filename

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(setup_file, setup_file.name)

        logger.info(f"Created ZIP file: {zip_path}")

        # Create simple version.txt file
        version_txt = apps_dir / "latest_version.txt"
        with open(version_txt, 'w') as f:
            f.write("1.0.1")

        logger.info(f"Created version file: {version_txt}")

        # Create detailed version info JSON
        version_info = {
            "latest_version": "1.0.1",
            "download_url": f"https://jointjourney-a12d2.web.app/apps/{zip_filename}",
            "file_name": zip_filename,
            "file_size": zip_path.stat().st_size,
            "release_date": datetime.now().isoformat(),
            "release_notes": "Initial release with secure authentication and auto-update functionality",
            "force_update": False,
            "min_supported_version": "1.0.0",
            "update_type": "zip"
        }

        version_file = hosting_dir / "version.json"
        with open(version_file, 'w') as f:
            json.dump(version_info, f, indent=2)

        logger.info(f"Created version info: {version_file}")

        # Update index.html for download page
        create_download_page(hosting_dir, version_info, logger)

        logger.info("✅ Hosting files prepared successfully!")
        logger.info(f"📦 ZIP file: {zip_filename}")
        logger.info(f"📄 Version file: latest_version.txt")
        return True

    except Exception as e:
        logger.error(f"Error preparing hosting files: {e}")
        return False

def create_download_page(hosting_dir, version_info, logger):
    """Create a download page"""
    try:
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Traqify - Personal Finance Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
            max-width: 500px;
            width: 90%;
        }}
        h1 {{
            color: #333;
            margin-bottom: 1rem;
        }}
        .version {{
            background: #f0f0f0;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            margin: 1rem 0;
            font-weight: bold;
        }}
        .download-btn {{
            background: #007ACC;
            color: white;
            padding: 1rem 2rem;
            border: none;
            border-radius: 5px;
            font-size: 1.1rem;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin: 1rem 0;
            transition: background 0.3s;
        }}
        .download-btn:hover {{
            background: #005A9E;
        }}
        .file-info {{
            color: #666;
            font-size: 0.9rem;
            margin-top: 1rem;
        }}
        .features {{
            text-align: left;
            margin: 1.5rem 0;
        }}
        .features ul {{
            list-style-type: none;
            padding: 0;
        }}
        .features li {{
            padding: 0.3rem 0;
            position: relative;
            padding-left: 1.5rem;
        }}
        .features li:before {{
            content: "✓";
            color: #28a745;
            font-weight: bold;
            position: absolute;
            left: 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Traqify</h1>
        <p>Personal Finance Dashboard</p>
        
        <div class="version">
            Version {version_info['latest_version']}
        </div>
        
        <div class="features">
            <h3>Features:</h3>
            <ul>
                <li>Secure cloud authentication</li>
                <li>Automatic updates</li>
                <li>Personal finance tracking</li>
                <li>Investment portfolio management</li>
                <li>Budget planning and analysis</li>
                <li>Data visualization and reports</li>
            </ul>
        </div>
        
        <a href="apps/{version_info['file_name']}" class="download-btn">
            📥 Download Traqify Setup
        </a>
        
        <div class="file-info">
            File: {version_info['file_name']}<br>
            Size: {version_info['file_size'] / (1024*1024):.1f} MB<br>
            Released: {version_info['release_date'][:10]}
        </div>
        
        <p style="margin-top: 2rem; color: #666; font-size: 0.9rem;">
            System Requirements: Windows 10 or later, Internet connection
        </p>
    </div>
</body>
</html>"""
        
        index_file = hosting_dir / "index.html"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Created download page: {index_file}")
        
    except Exception as e:
        logger.error(f"Error creating download page: {e}")

def deploy_to_firebase(logger):
    """Deploy to Firebase Hosting"""
    try:
        logger.info("Deploying to Firebase Hosting...")
        
        # Change to project root directory
        project_root = Path(__file__).parent.parent
        os.chdir(project_root)
        
        # Deploy using Firebase CLI
        result = os.system("firebase deploy --only hosting")
        
        if result == 0:
            logger.info("✅ Successfully deployed to Firebase Hosting!")
            logger.info("🌐 Your app is available at: https://jointjourney-a12d2.web.app")
            logger.info("📥 Download URL: https://jointjourney-a12d2.web.app/apps/")
            return True
        else:
            logger.error("❌ Firebase deployment failed!")
            return False
            
    except Exception as e:
        logger.error(f"Error deploying to Firebase: {e}")
        return False

if __name__ == "__main__":
    logger = setup_logging()
    
    logger.info("🚀 Starting Firebase deployment process...")
    
    # Step 1: Prepare hosting files
    if not prepare_hosting_files(logger):
        logger.error("❌ Failed to prepare hosting files")
        sys.exit(1)
    
    # Step 2: Deploy to Firebase
    if not deploy_to_firebase(logger):
        logger.error("❌ Failed to deploy to Firebase")
        sys.exit(1)
    
    logger.info("🎉 Deployment completed successfully!")
    print("\n" + "="*60)
    print("🎉 FIREBASE DEPLOYMENT COMPLETE!")
    print("="*60)
    print("✅ Setup file uploaded to Firebase Hosting")
    print("✅ Download page created")
    print("✅ Version info updated")
    print("\n🌐 Access your app at:")
    print("   https://jointjourney-a12d2.web.app")
    print("\n📋 Next steps:")
    print("   1. Update your Replit backend version info")
    print("   2. Test the download link")
    print("   3. Share the download URL with users")
    print("="*60)
