#!/bin/bash

# GrowUp IoT System - Cleanup Script
# Removes old documentation files from root directory
# All docs should be in docs/ folder

echo "🧹 Cleaning up old documentation files..."

# Navigate to project root
cd "$(dirname "$0")/.." || exit 1

# List of files to remove (if they exist in root)
OLD_FILES=(
    "ARCHITECTURE.md"
    "API_DOCUMENTATION.md"
    "SETUP_GUIDE.md"
    "TROUBLESHOOTING.md"
    "CHANGELOG.md"
    "SECURITY.md"
    "MAINTENANCE.md"
    "PERFORMANCE.md"
)

# Remove old documentation files from root
removed_count=0
for file in "${OLD_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ❌ Removing: $file"
        rm "$file"
        ((removed_count++))
    fi
done

if [ $removed_count -eq 0 ]; then
    echo "  ✅ No old files to remove - all clean!"
else
    echo "  ✅ Removed $removed_count old documentation file(s)"
fi

# Verify docs folder exists with correct structure
echo ""
echo "📁 Verifying docs/ folder structure..."

if [ ! -d "docs" ]; then
    echo "  ⚠️  docs/ folder not found - creating it..."
    mkdir -p docs
fi

# Check for required documentation files
REQUIRED_DOCS=(
    "docs/README.md"
    "docs/ARCHITECTURE.md"
    "docs/API_DOCUMENTATION.md"
    "docs/SETUP_GUIDE.md"
)

missing_count=0
for doc in "${REQUIRED_DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo "  ✅ Found: $doc"
    else
        echo "  ⚠️  Missing: $doc"
        ((missing_count++))
    fi
done

if [ $missing_count -eq 0 ]; then
    echo ""
    echo "✨ Documentation cleanup complete!"
    echo "📚 All documentation is properly organized in docs/ folder"
else
    echo ""
    echo "⚠️  Warning: $missing_count documentation file(s) missing"
    echo "Please ensure all documentation is in the docs/ folder"
fi

# List current documentation structure
echo ""
echo "📂 Current documentation structure:"
tree docs/ 2>/dev/null || find docs/ -type f -name "*.md" | sort

echo ""
echo "✅ Cleanup complete!"
