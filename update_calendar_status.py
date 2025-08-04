#!/usr/bin/env python3
"""
Simple Calendar Status Update Script
Updates calendar events from "Completed" to "Pending" status for UI visibility
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta, date
import logging
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_calendar_status():
    """Update calendar events status from Completed to Pending"""
    
    print("🔄 CALENDAR STATUS UPDATE")
    print("=" * 40)
    
    try:
        from src.modules.todos.models import TodoDataModel, Status, Priority, Category, TodoItem
        from src.core.data_manager import DataManager
        
        # Initialize with proper data manager
        data_manager = DataManager("data")
        todo_model = TodoDataModel(data_manager)
        
        print("✅ Models initialized successfully")
        print()
        
        # Step 1: Get all calendar events
        print("📋 STEP 1: Finding Calendar Events")
        print("-" * 35)
        
        local_df = todo_model.get_all_todos()
        
        if local_df.empty:
            print("❌ No tasks found!")
            return
        
        # Find calendar events
        calendar_mask = (
            local_df['google_task_id'].notna() & 
            local_df['google_task_id'].str.startswith('cal_', na=False)
        )
        calendar_events = local_df[calendar_mask]
        
        print(f"📊 Found {len(calendar_events)} calendar events")
        
        if len(calendar_events) == 0:
            print("❌ No calendar events found!")
            return
        
        # Count by status
        status_counts = calendar_events['status'].value_counts()
        print(f"📊 Status breakdown:")
        for status, count in status_counts.items():
            print(f"   {status}: {count}")
        print()
        
        # Step 2: Update completed calendar events
        completed_events = calendar_events[calendar_events['status'] == 'Completed']
        
        if len(completed_events) == 0:
            print("✅ No completed calendar events to update!")
            return
        
        print("🔄 STEP 2: Updating Calendar Events")
        print("-" * 40)
        
        print(f"🔄 Updating {len(completed_events)} completed calendar events to 'Pending'...")
        
        updated_count = 0
        failed_count = 0
        
        for _, row in completed_events.iterrows():
            try:
                # Create TodoItem from row
                todo_item = TodoItem.from_dict(row.to_dict())
                
                # Update status to Pending
                todo_item.status = Status.PENDING.value
                
                # Update in database using TodoDataModel
                success = todo_model.update_todo(todo_item)
                
                if success:
                    updated_count += 1
                    if updated_count <= 5:  # Show first 5 updates
                        print(f"   ✅ Updated: '{todo_item.title[:50]}{'...' if len(todo_item.title) > 50 else ''}'")
                else:
                    failed_count += 1
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to update calendar event {row.get('id', 'unknown')}: {e}")
        
        print(f"📊 Update Results:")
        print(f"   ✅ Successfully Updated: {updated_count}")
        print(f"   ❌ Failed: {failed_count}")
        print()
        
        # Step 3: Verify the changes
        print("✅ STEP 3: Verification")
        print("-" * 25)
        
        # Get updated data
        local_df_after = todo_model.get_all_todos()
        calendar_events_after = local_df_after[
            local_df_after['google_task_id'].notna() & 
            local_df_after['google_task_id'].str.startswith('cal_', na=False)
        ]
        
        status_counts_after = calendar_events_after['status'].value_counts()
        print(f"📊 Status breakdown after update:")
        for status, count in status_counts_after.items():
            print(f"   {status}: {count}")
        
        pending_count = status_counts_after.get('Pending', 0)
        
        print()
        
        # Step 4: Test UI filtering
        print("🎯 STEP 4: UI Filter Test")
        print("-" * 25)
        
        # Test "Pending" filter
        pending_tasks = local_df_after[local_df_after['status'] == 'Pending']
        pending_calendar = pending_tasks[
            pending_tasks['google_task_id'].notna() & 
            pending_tasks['google_task_id'].str.startswith('cal_', na=False)
        ]
        
        print(f"📊 'Pending' filter results:")
        print(f"   Total Pending Tasks: {len(pending_tasks)}")
        print(f"   Pending Calendar Events: {len(pending_calendar)}")
        
        # Test "Personal" category filter
        personal_tasks = local_df_after[local_df_after['category'] == 'Personal']
        personal_calendar = personal_tasks[
            personal_tasks['google_task_id'].notna() & 
            personal_tasks['google_task_id'].str.startswith('cal_', na=False)
        ]
        
        print(f"📊 'Personal' category filter results:")
        print(f"   Total Personal Tasks: {len(personal_tasks)}")
        print(f"   Personal Calendar Events: {len(personal_calendar)}")
        
        # Test combined filter
        pending_personal = local_df_after[
            (local_df_after['status'] == 'Pending') & 
            (local_df_after['category'] == 'Personal')
        ]
        pending_personal_calendar = pending_personal[
            pending_personal['google_task_id'].notna() & 
            pending_personal['google_task_id'].str.startswith('cal_', na=False)
        ]
        
        print(f"📊 'Pending + Personal' filter results:")
        print(f"   Total: {len(pending_personal)}")
        print(f"   Calendar Events: {len(pending_personal_calendar)}")
        
        print()
        
        # Step 5: Final recommendations
        print("💡 STEP 5: Final Status")
        print("-" * 25)
        
        if pending_count > 0:
            print("🎉 SUCCESS! Calendar events updated to 'Pending' status!")
            print(f"✅ {pending_count} calendar events are now 'Pending'")
            print()
            print("🖥️ Calendar events should now be visible in the UI when:")
            print("   • Status filter is set to 'All' or 'Pending'")
            print("   • Category filter is set to 'All' or 'Personal'")
            print("   • Look for tasks with 📅 emoji prefix")
            print()
            print("🔧 Next steps:")
            print("   1. Restart the Traqify application")
            print("   2. Go to Tasks section")
            print("   3. Ensure filters are set to show Pending tasks")
            print("   4. Calendar events should now be visible!")
        else:
            print("⚠️ No calendar events were updated to 'Pending' status")
            print("💡 Check the error messages above for issues")
        
        return {
            'success': pending_count > 0,
            'updated_count': updated_count,
            'failed_count': failed_count,
            'pending_count': pending_count,
            'total_calendar_events': len(calendar_events_after)
        }
        
    except Exception as e:
        print(f"❌ Update script failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚀 Starting calendar status update...")
    print()
    
    result = update_calendar_status()
    
    if result:
        print()
        print("🏁 UPDATE SCRIPT COMPLETE")
        print("=" * 30)
        print(f"📊 FINAL RESULTS:")
        print(f"   🎉 Success: {result['success']}")
        print(f"   🔄 Updated: {result['updated_count']}")
        print(f"   ❌ Failed: {result['failed_count']}")
        print(f"   ⏳ Pending Events: {result['pending_count']}")
        print(f"   📅 Total Calendar Events: {result['total_calendar_events']}")
        
        if result['success']:
            print()
            print("🎉 SUCCESS! Calendar events should now be visible in the Tasks section!")
            print("💡 Restart the application and check the 'Pending' tasks filter.")
        else:
            print()
            print("⚠️ Calendar events were not successfully updated.")
            print("💡 Please check the error messages above.")
    else:
        print()
        print("❌ Update script encountered errors. Please check the logs above.")
