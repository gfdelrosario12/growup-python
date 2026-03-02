#!/bin/bash

# GrowUp IoT System - Cleanup Script
# ==================================
# Removes redundant and temporary files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🧹 GrowUp IoT System - File Cleanup"
echo "===================================="
echo ""

# Confirm before proceeding
read -p "This will delete redundant files. Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "Starting cleanup..."
echo ""

# Counter
deleted=0

# Remove old launcher scripts
echo "📄 Removing old launcher scripts..."
for file in start_lcd_viewer.sh start.sh; do
    if [ -f "$file" ]; then
        rm -f "$file"
        echo "   ✅ Deleted: $file"
        ((deleted++))
    fi
done

# Remove temporary/generated files
echo ""
echo "📄 Removing temporary files..."
for file in system_integration.py system_manager.py influxdb_client.py; do
    if [ -f "$file" ]; then
        rm -f "$file"
        echo "   ✅ Deleted: $file"
        ((deleted++))
    fi
done

# Remove redundant documentation from root
echo ""
echo "📄 Removing redundant documentation from root..."
for file in README_LCD_VIEWER.md README_NEW.md REPOSITORY_SCOPE.md RUN_FIXED.md GPIO_MOCK_FIX.md QUICK_START.md; do
    if [ -f "$file" ]; then
        rm -f "$file"
        echo "   ✅ Deleted: $file"
        ((deleted++))
    fi
done

# Remove old documentation from docs/
echo ""
echo "📄 Removing old documentation from docs/..."
for file in docs/CLEANUP_BACKEND_CODE.md docs/CLEANUP_SUMMARY.md docs/REORGANIZATION_SUMMARY.md docs/CLEANUP_SUMMARY_REFACTOR.md docs/SYSTEM_ARCHITECTURE_FINAL.md docs/FINAL_ARCHITECTURE.md docs/NEXTJS_CONTROL_INTEGRATION.md docs/DOCUMENTATION_ORGANIZATION.md; do
    if [ -f "$file" ]; then
        rm -f "$file"
        echo "   ✅ Deleted: $file"
        ((deleted++))
    fi
done

# Clean Python cache
echo ""
echo "🗑️  Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
echo "   ✅ Cache cleaned"

echo ""
echo "===================================="
echo "✅ Cleanup Complete!"
echo "===================================="
echo ""
echo "📊 Summary:"
echo "   Files deleted: $deleted"
echo "   Cache cleaned: Yes"
echo ""
echo "✨ Project is now clean and organized!"
echo ""
echo "Next steps:"
echo "   python3 test_system.py    # Verify system"
echo "   python3 main.py --lcd --demo  # Run system"
echo ""
