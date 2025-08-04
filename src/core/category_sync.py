"""
Category Synchronization System
Manages category synchronization between the main application and Bank Statement Analyzer
"""

import json
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict


@dataclass
class CategoryRecord:
    """Unified category record structure"""
    id: Optional[int] = None
    category: str = ""
    sub_category: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source: str = "main_app"  # "main_app" or "bank_analyzer"
    
    def __post_init__(self):
        """Post-initialization processing"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        data = asdict(self)
        if isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(data['updated_at'], datetime):
            data['updated_at'] = data['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        return data


class CategorySynchronizer:
    """Handles category synchronization between main app and bank analyzer"""
    
    def __init__(self, main_app_data_dir: str = "data", bank_analyzer_dir: str = "bank_statement_analyzer"):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Paths
        self.main_app_data_dir = Path(main_app_data_dir)
        self.bank_analyzer_dir = Path(bank_analyzer_dir)
        
        # Main application category file
        self.main_categories_file = self.main_app_data_dir / "expenses" / "categories.csv"
        
        # Bank analyzer category files
        self.bank_analyzer_data_dir = self.bank_analyzer_dir / "data" / "expenses"
        self.bank_analyzer_categories_file = self.bank_analyzer_data_dir / "categories.csv"
        
        # Sync metadata file
        self.sync_metadata_file = self.main_app_data_dir / "category_sync_metadata.json"
        
        # Ensure directories exist
        self.main_app_data_dir.mkdir(parents=True, exist_ok=True)
        self.bank_analyzer_data_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("CategorySynchronizer initialized")
    
    def sync_categories(self, direction: str = "bidirectional") -> Tuple[bool, str]:
        """
        Synchronize categories between applications
        
        Args:
            direction: "main_to_bank", "bank_to_main", or "bidirectional"
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if direction == "main_to_bank":
                return self._sync_main_to_bank()
            elif direction == "bank_to_main":
                return self._sync_bank_to_main()
            elif direction == "bidirectional":
                return self._sync_bidirectional()
            else:
                return False, f"Invalid sync direction: {direction}"
                
        except Exception as e:
            self.logger.error(f"Error during category sync: {e}")
            return False, f"Sync failed: {str(e)}"
    
    def _sync_main_to_bank(self) -> Tuple[bool, str]:
        """Sync categories from main app to bank analyzer"""
        try:
            # Read main app categories
            main_categories = self._read_main_categories()
            if main_categories.empty:
                return False, "No categories found in main application"

            # Convert main app categories to bank analyzer format and update ML categories
            success = self._update_bank_analyzer_ml_categories(main_categories)
            if not success:
                return False, "Failed to update bank analyzer ML categories"

            # Also update the bank analyzer CSV file for compatibility
            if not self.bank_analyzer_categories_file.exists():
                main_categories.to_csv(self.bank_analyzer_categories_file, index=False)
                self.logger.info(f"Created bank analyzer categories file with {len(main_categories)} categories")
            else:
                bank_categories = self._read_bank_categories()
                merged_categories = self._merge_categories(main_categories, bank_categories, prefer_main=True)
                merged_categories.to_csv(self.bank_analyzer_categories_file, index=False)
                self.logger.info(f"Updated bank analyzer categories with {len(merged_categories)} categories")

            self._update_sync_metadata("main_to_bank")
            return True, "Successfully synced categories from main app to bank analyzer"

        except Exception as e:
            self.logger.error(f"Error syncing main to bank: {e}")
            return False, f"Failed to sync main to bank: {str(e)}"
    
    def _sync_bank_to_main(self) -> Tuple[bool, str]:
        """Sync categories from bank analyzer to main app"""
        try:
            # Read ML categories from bank analyzer
            ml_categories = self._read_ml_categories()
            if not ml_categories:
                return False, "No ML categories found in bank analyzer"

            # Convert ML categories to CSV format
            bank_categories_csv = self._convert_ml_to_csv_format(ml_categories)
            if bank_categories_csv.empty:
                return False, "Failed to convert ML categories to CSV format"

            # Read main app categories
            main_categories = self._read_main_categories()

            # Merge categories (prefer bank analyzer for conflicts)
            merged_categories = self._merge_categories(main_categories, bank_categories_csv, prefer_main=False)

            # Update main app categories
            merged_categories.to_csv(self.main_categories_file, index=False)
            self.logger.info(f"Updated main app categories with {len(merged_categories)} categories")

            self._update_sync_metadata("bank_to_main")
            return True, "Successfully synced categories from bank analyzer to main app"

        except Exception as e:
            self.logger.error(f"Error syncing bank to main: {e}")
            return False, f"Failed to sync bank to main: {str(e)}"
    
    def _sync_bidirectional(self) -> Tuple[bool, str]:
        """Perform bidirectional sync based on timestamps"""
        try:
            # Read from both sources
            main_categories = self._read_main_categories()
            ml_categories = self._read_ml_categories()

            # Convert ML categories to CSV format for comparison
            bank_categories_csv = self._convert_ml_to_csv_format(ml_categories) if ml_categories else pd.DataFrame()

            if main_categories.empty and bank_categories_csv.empty:
                return False, "No categories found in either application"

            # If one is empty, copy from the other
            if main_categories.empty:
                return self._sync_bank_to_main()
            elif bank_categories_csv.empty:
                return self._sync_main_to_bank()

            # Both have data - merge intelligently
            merged_categories = self._intelligent_merge(main_categories, bank_categories_csv)

            # Update main app CSV file
            merged_categories.to_csv(self.main_categories_file, index=False)

            # Update bank analyzer CSV file for compatibility
            merged_categories.to_csv(self.bank_analyzer_categories_file, index=False)

            # Update bank analyzer ML categories
            self._update_bank_analyzer_ml_categories(merged_categories)

            self._update_sync_metadata("bidirectional")
            self.logger.info(f"Bidirectional sync completed with {len(merged_categories)} categories")

            return True, f"Successfully synchronized {len(merged_categories)} categories bidirectionally"

        except Exception as e:
            self.logger.error(f"Error in bidirectional sync: {e}")
            return False, f"Bidirectional sync failed: {str(e)}"
    
    def _read_main_categories(self) -> pd.DataFrame:
        """Read categories from main application"""
        try:
            if not self.main_categories_file.exists():
                return pd.DataFrame()
            
            df = pd.read_csv(self.main_categories_file)
            
            # Ensure required columns exist
            required_columns = ['category', 'sub_category', 'is_active']
            for col in required_columns:
                if col not in df.columns:
                    if col == 'is_active':
                        df[col] = True
                    else:
                        df[col] = ""
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error reading main categories: {e}")
            return pd.DataFrame()
    
    def _read_bank_categories(self) -> pd.DataFrame:
        """Read categories from bank analyzer"""
        try:
            if not self.bank_analyzer_categories_file.exists():
                return pd.DataFrame()
            
            df = pd.read_csv(self.bank_analyzer_categories_file)
            
            # Ensure required columns exist
            required_columns = ['category', 'sub_category', 'is_active']
            for col in required_columns:
                if col not in df.columns:
                    if col == 'is_active':
                        df[col] = True
                    else:
                        df[col] = ""
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error reading bank categories: {e}")
            return pd.DataFrame()
    
    def _merge_categories(self, main_df: pd.DataFrame, bank_df: pd.DataFrame, prefer_main: bool = True) -> pd.DataFrame:
        """Merge categories from both sources"""
        try:
            # Combine both dataframes
            combined_df = pd.concat([main_df, bank_df], ignore_index=True)
            
            # Remove duplicates based on category + sub_category combination
            # Keep the preferred source's version for duplicates
            if prefer_main:
                # Sort so main app entries come first, then drop duplicates
                combined_df = combined_df.drop_duplicates(subset=['category', 'sub_category'], keep='first')
            else:
                # Sort so bank analyzer entries come first, then drop duplicates
                combined_df = combined_df.drop_duplicates(subset=['category', 'sub_category'], keep='last')
            
            # Reset index and ensure ID column
            combined_df = combined_df.reset_index(drop=True)
            combined_df['id'] = range(1, len(combined_df) + 1)
            
            # Ensure updated_at timestamp
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if 'updated_at' not in combined_df.columns:
                combined_df['updated_at'] = current_time
            
            return combined_df
            
        except Exception as e:
            self.logger.error(f"Error merging categories: {e}")
            return pd.DataFrame()
    
    def _intelligent_merge(self, main_df: pd.DataFrame, bank_df: pd.DataFrame) -> pd.DataFrame:
        """Intelligently merge categories based on timestamps and changes"""
        try:
            # Create a comprehensive merge
            all_categories = {}
            
            # Process main app categories
            for _, row in main_df.iterrows():
                key = (row['category'], row['sub_category'])
                all_categories[key] = {
                    'category': row['category'],
                    'sub_category': row['sub_category'],
                    'is_active': row.get('is_active', True),
                    'created_at': row.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    'updated_at': row.get('updated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    'source': 'main_app'
                }
            
            # Process bank analyzer categories (may override main app if newer)
            for _, row in bank_df.iterrows():
                key = (row['category'], row['sub_category'])
                bank_updated = row.get('updated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                
                if key in all_categories:
                    # Compare timestamps if both exist
                    main_updated = all_categories[key]['updated_at']
                    try:
                        if datetime.strptime(bank_updated, '%Y-%m-%d %H:%M:%S') > datetime.strptime(main_updated, '%Y-%m-%d %H:%M:%S'):
                            # Bank analyzer version is newer
                            all_categories[key].update({
                                'is_active': row.get('is_active', True),
                                'updated_at': bank_updated,
                                'source': 'bank_analyzer'
                            })
                    except:
                        # If timestamp parsing fails, keep main app version
                        pass
                else:
                    # New category from bank analyzer
                    all_categories[key] = {
                        'category': row['category'],
                        'sub_category': row['sub_category'],
                        'is_active': row.get('is_active', True),
                        'created_at': row.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                        'updated_at': bank_updated,
                        'source': 'bank_analyzer'
                    }
            
            # Convert back to DataFrame
            merged_data = list(all_categories.values())
            merged_df = pd.DataFrame(merged_data)
            merged_df['id'] = range(1, len(merged_df) + 1)
            
            return merged_df
            
        except Exception as e:
            self.logger.error(f"Error in intelligent merge: {e}")
            return self._merge_categories(main_df, bank_df, prefer_main=True)
    
    def _update_sync_metadata(self, sync_type: str):
        """Update sync metadata"""
        try:
            metadata = {
                'last_sync': datetime.now().isoformat(),
                'sync_type': sync_type,
                'version': '1.0'
            }
            
            with open(self.sync_metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error updating sync metadata: {e}")

    def _read_ml_categories(self) -> List[Dict]:
        """Read ML categories from bank analyzer"""
        ml_categories_file = self.bank_analyzer_dir / "bank_analyzer_config" / "ml_data" / "ml_categories.json"

        if not ml_categories_file.exists():
            return []

        try:
            with open(ml_categories_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error reading ML categories: {e}")
            return []

    def _convert_ml_to_csv_format(self, ml_categories: List[Dict]) -> pd.DataFrame:
        """Convert ML categories to CSV format"""
        try:
            # Create a mapping of IDs to categories
            id_to_category = {cat['id']: cat for cat in ml_categories}

            csv_data = []

            for category in ml_categories:
                if category['parent_id'] is None:
                    # This is a main category
                    main_category = category['name']

                    # Find all subcategories
                    subcategories = [cat for cat in ml_categories if cat['parent_id'] == category['id']]

                    if subcategories:
                        # Add each subcategory
                        for subcat in subcategories:
                            csv_data.append({
                                'category': main_category,
                                'sub_category': subcat['name'],
                                'is_active': subcat.get('is_active', True),
                                'created_at': subcat.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                                'updated_at': subcat.get('updated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                                'source': 'bank_analyzer'
                            })
                    else:
                        # Main category without subcategories
                        csv_data.append({
                            'category': main_category,
                            'sub_category': 'General',
                            'is_active': category.get('is_active', True),
                            'created_at': category.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                            'updated_at': category.get('updated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                            'source': 'bank_analyzer'
                        })

            df = pd.DataFrame(csv_data)
            if not df.empty:
                df['id'] = range(1, len(df) + 1)

            return df

        except Exception as e:
            self.logger.error(f"Error converting ML to CSV format: {e}")
            return pd.DataFrame()

    def _convert_csv_to_ml_format(self, csv_categories: pd.DataFrame) -> List[Dict]:
        """Convert CSV categories to ML format"""
        try:
            ml_categories = []
            category_id_counter = 1

            # Group by main category
            grouped = csv_categories.groupby('category')

            for main_category, group in grouped:
                # Create main category
                main_cat_id = f"ml_{main_category.lower().replace(' ', '_').replace('&', 'and')}_{category_id_counter}"
                category_id_counter += 1

                main_category_data = {
                    "id": main_cat_id,
                    "name": main_category,
                    "parent_id": None,
                    "description": "",
                    "is_active": True,
                    "is_system": False,
                    "color": "#007ACC",
                    "icon": "folder",
                    "category_type": "expense",  # Default, can be updated based on category
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }

                # Determine category type based on category name
                if any(keyword in main_category.lower() for keyword in ['income', 'salary', 'revenue', 'refund', 'return']):
                    main_category_data["category_type"] = "income"

                ml_categories.append(main_category_data)

                # Create subcategories
                for _, row in group.iterrows():
                    if row['sub_category'] != 'General':  # Skip generic subcategories
                        subcat_id = f"ml_{row['sub_category'].lower().replace(' ', '_').replace('&', 'and')}_{category_id_counter}"
                        category_id_counter += 1

                        subcategory_data = {
                            "id": subcat_id,
                            "name": row['sub_category'],
                            "parent_id": main_cat_id,
                            "description": "",
                            "is_active": row.get('is_active', True),
                            "is_system": False,
                            "color": "#007ACC",
                            "icon": "folder",
                            "category_type": main_category_data["category_type"],
                            "created_at": row.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                            "updated_at": row.get('updated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        }

                        ml_categories.append(subcategory_data)

            return ml_categories

        except Exception as e:
            self.logger.error(f"Error converting CSV to ML format: {e}")
            return []

    def _update_bank_analyzer_ml_categories(self, csv_categories: pd.DataFrame) -> bool:
        """Update bank analyzer ML categories file"""
        try:
            ml_categories_file = self.bank_analyzer_dir / "bank_analyzer_config" / "ml_data" / "ml_categories.json"

            # Read existing ML categories
            existing_ml_categories = self._read_ml_categories()

            # Convert CSV to ML format
            new_ml_categories = self._convert_csv_to_ml_format(csv_categories)

            # Merge with existing (prefer existing for conflicts)
            merged_ml_categories = self._merge_ml_categories(existing_ml_categories, new_ml_categories)

            # Ensure directory exists
            ml_categories_file.parent.mkdir(parents=True, exist_ok=True)

            # Write updated ML categories
            with open(ml_categories_file, 'w') as f:
                json.dump(merged_ml_categories, f, indent=2)

            self.logger.info(f"Updated ML categories file with {len(merged_ml_categories)} categories")
            return True

        except Exception as e:
            self.logger.error(f"Error updating bank analyzer ML categories: {e}")
            return False

    def _merge_ml_categories(self, existing: List[Dict], new: List[Dict]) -> List[Dict]:
        """Merge ML categories, preserving existing ones"""
        try:
            # Create a mapping of existing categories by name
            existing_by_name = {}
            for cat in existing:
                key = (cat['name'], cat.get('parent_id'))
                existing_by_name[key] = cat

            # Add new categories that don't exist
            merged = existing.copy()

            for new_cat in new:
                key = (new_cat['name'], new_cat.get('parent_id'))
                if key not in existing_by_name:
                    merged.append(new_cat)

            return merged

        except Exception as e:
            self.logger.error(f"Error merging ML categories: {e}")
            return existing
    
    def get_sync_status(self) -> Dict:
        """Get current sync status"""
        try:
            if not self.sync_metadata_file.exists():
                return {'status': 'never_synced'}
            
            with open(self.sync_metadata_file, 'r') as f:
                metadata = json.load(f)
            
            metadata['status'] = 'synced'
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error getting sync status: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def add_category_to_both(self, category: str, sub_category: str) -> Tuple[bool, str]:
        """Add a category to both applications"""
        try:
            # Create category record
            new_category = CategoryRecord(
                category=category,
                sub_category=sub_category,
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            # Add to main app
            main_df = self._read_main_categories()
            new_row = pd.DataFrame([new_category.to_dict()])
            main_df = pd.concat([main_df, new_row], ignore_index=True)
            main_df['id'] = range(1, len(main_df) + 1)
            main_df.to_csv(self.main_categories_file, index=False)

            # Add to bank analyzer CSV for compatibility
            bank_df = self._read_bank_categories()
            bank_df = pd.concat([bank_df, new_row], ignore_index=True)
            bank_df['id'] = range(1, len(bank_df) + 1)
            bank_df.to_csv(self.bank_analyzer_categories_file, index=False)

            # Add to bank analyzer ML categories
            self._add_to_ml_categories(category, sub_category)

            self.logger.info(f"Added category '{category}/{sub_category}' to both applications")
            return True, f"Successfully added category '{category}/{sub_category}' to both applications"

        except Exception as e:
            self.logger.error(f"Error adding category to both: {e}")
            return False, f"Failed to add category: {str(e)}"

    def _add_to_ml_categories(self, category: str, sub_category: str):
        """Add a category to ML categories file"""
        try:
            ml_categories_file = self.bank_analyzer_dir / "bank_analyzer_config" / "ml_data" / "ml_categories.json"

            # Read existing ML categories
            ml_categories = self._read_ml_categories()

            # Find or create main category
            main_cat_id = None
            for cat in ml_categories:
                if cat['name'] == category and cat['parent_id'] is None:
                    main_cat_id = cat['id']
                    break

            if not main_cat_id:
                # Create main category
                main_cat_id = f"ml_{category.lower().replace(' ', '_').replace('&', 'and')}_{len(ml_categories) + 1}"
                main_category_data = {
                    "id": main_cat_id,
                    "name": category,
                    "parent_id": None,
                    "description": "",
                    "is_active": True,
                    "is_system": False,
                    "color": "#007ACC",
                    "icon": "folder",
                    "category_type": "expense",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                ml_categories.append(main_category_data)

            # Check if subcategory already exists
            subcat_exists = any(
                cat['name'] == sub_category and cat['parent_id'] == main_cat_id
                for cat in ml_categories
            )

            if not subcat_exists:
                # Create subcategory
                subcat_id = f"ml_{sub_category.lower().replace(' ', '_').replace('&', 'and')}_{len(ml_categories) + 1}"
                subcategory_data = {
                    "id": subcat_id,
                    "name": sub_category,
                    "parent_id": main_cat_id,
                    "description": "",
                    "is_active": True,
                    "is_system": False,
                    "color": "#007ACC",
                    "icon": "folder",
                    "category_type": "expense",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                ml_categories.append(subcategory_data)

            # Write updated ML categories
            ml_categories_file.parent.mkdir(parents=True, exist_ok=True)
            with open(ml_categories_file, 'w') as f:
                json.dump(ml_categories, f, indent=2)

            self.logger.info(f"Added '{category}/{sub_category}' to ML categories")

        except Exception as e:
            self.logger.error(f"Error adding to ML categories: {e}")


def create_category_synchronizer(main_app_data_dir: str = "data", bank_analyzer_dir: str = "bank_statement_analyzer") -> CategorySynchronizer:
    """Factory function to create a category synchronizer"""
    return CategorySynchronizer(main_app_data_dir, bank_analyzer_dir)
