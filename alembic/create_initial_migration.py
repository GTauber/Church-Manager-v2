#!/usr/bin/env python
"""
Script to create the initial database migration.

Run this script to generate the first Alembic migration with all models.
"""

import subprocess
import sys
from datetime import datetime


def main():
    """Create the initial database migration."""
    
    print("Creating initial database migration...")
    
    # Generate migration name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    migration_message = "initial_schema"
    
    try:
        # Run alembic revision command
        result = subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", migration_message],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("Migration created successfully!")
        print(result.stdout)
        
        print("\nTo apply the migration, run:")
        print("  alembic upgrade head")
        
    except subprocess.CalledProcessError as e:
        print(f"Error creating migration: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: Alembic not found. Please ensure it's installed:")
        print("  pip install alembic")
        sys.exit(1)


if __name__ == "__main__":
    main()