#!/bin/bash

# GrowUp IoT System - Documentation Verification Script
# Verifies all documentation is properly organized

echo "📚 GrowUp IoT System - Documentation Verification"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Navigate to project root
cd "$(dirname "$0")/.." || exit 1

echo "📁 Project Root: $(pwd)"
echo ""

# Check for docs folder
echo "1️⃣  Checking docs/ folder..."
if [ -d "docs" ]; then
    echo -e "   ${GREEN}✅ docs/ folder exists${NC}"
else
    echo -e "   ${RED}❌ docs/ folder not found${NC}"
    exit 1
fi
echo ""

# Check for required documentation files
echo "2️⃣  Checking required documentation files..."
REQUIRED_DOCS=(
    "README.md:Root README"
    "docs/README.md:Documentation Index"
    "docs/ARCHITECTURE.md:Architecture Documentation"
    "docs/API_DOCUMENTATION.md:API Documentation"
    "docs/SETUP_GUIDE.md:Setup Guide"
    "requirements.txt:Python Requirements"
)

missing_count=0
for entry in "${REQUIRED_DOCS[@]}"; do
    IFS=':' read -r file desc <<< "$entry"
    if [ -f "$file" ]; then
        size=$(wc -l < "$file" 2>/dev/null || echo "0")
        echo -e "   ${GREEN}✅ $desc${NC} ($file) - $size lines"
    else
        echo -e "   ${RED}❌ $desc${NC} ($file) - MISSING"
        ((missing_count++))
    fi
done
echo ""

# Check for old documentation files in root (should not exist)
echo "3️⃣  Checking for old documentation files in root..."
OLD_FILES=(
    "ARCHITECTURE.md"
    "API_DOCUMENTATION.md"
    "SETUP_GUIDE.md"
    "TROUBLESHOOTING.md"
    "API_DOCS.md"
    "SETUP.md"
)

old_found=0
for file in "${OLD_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "   ${YELLOW}⚠️  Old file found: $file${NC} (should be in docs/)"
        ((old_found++))
    fi
done

if [ $old_found -eq 0 ]; then
    echo -e "   ${GREEN}✅ No old documentation files in root - Clean!${NC}"
fi
echo ""

# Check for scripts
echo "4️⃣  Checking utility scripts..."
SCRIPTS=(
    "scripts/cleanup_docs.sh:Documentation Cleanup"
)

for entry in "${SCRIPTS[@]}"; do
    IFS=':' read -r file desc <<< "$entry"
    if [ -f "$file" ]; then
        if [ -x "$file" ]; then
            echo -e "   ${GREEN}✅ $desc${NC} ($file) - executable"
        else
            echo -e "   ${YELLOW}⚠️  $desc${NC} ($file) - not executable"
            echo "      Run: chmod +x $file"
        fi
    else
        echo -e "   ${YELLOW}⚠️  $desc${NC} ($file) - not found"
    fi
done
echo ""

# Check documentation structure
echo "5️⃣  Documentation structure:"
if command -v tree &> /dev/null; then
    tree docs/ -L 1 --charset ascii
else
    find docs/ -type f -name "*.md" | sort | sed 's/^/   /'
fi
echo ""

# Count total documentation lines
echo "6️⃣  Documentation statistics:"
total_lines=0
if [ -f "README.md" ]; then
    root_lines=$(wc -l < README.md)
    total_lines=$((total_lines + root_lines))
    echo "   📄 Root README.md: $root_lines lines"
fi

if [ -d "docs" ]; then
    docs_lines=$(find docs/ -name "*.md" -exec wc -l {} + | tail -1 | awk '{print $1}')
    total_lines=$((total_lines + docs_lines))
    echo "   📁 docs/ folder: $docs_lines lines"
fi

echo "   📊 Total documentation: $total_lines lines"
echo ""

# Final summary
echo "=================================================="
if [ $missing_count -eq 0 ] && [ $old_found -eq 0 ]; then
    echo -e "${GREEN}✅ Documentation verification: PASSED${NC}"
    echo ""
    echo "All documentation is properly organized!"
    echo "- All required files present"
    echo "- No old files in root directory"
    echo "- docs/ folder structure correct"
    echo ""
    echo "Next steps:"
    echo "  1. Review root README.md for project overview"
    echo "  2. Check docs/README.md for documentation index"
    echo "  3. Follow docs/SETUP_GUIDE.md for installation"
    exit 0
else
    echo -e "${RED}⚠️  Documentation verification: NEEDS ATTENTION${NC}"
    echo ""
    if [ $missing_count -gt 0 ]; then
        echo "- $missing_count required file(s) missing"
    fi
    if [ $old_found -gt 0 ]; then
        echo "- $old_found old file(s) need cleanup"
        echo "  Run: bash scripts/cleanup_docs.sh"
    fi
    exit 1
fi
