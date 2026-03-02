#!/bin/bash

# Documentation Cleanup Verification Script
# Ensures all documentation is properly organized

echo "╔════════════════════════════════════════════════════════╗"
echo "║   GrowUp IoT - Documentation Verification             ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

PROJECT_ROOT="/home/gladwin/Documents/Personal/Grow Up/rpi"
cd "$PROJECT_ROOT" || exit 1

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

echo "📍 Project Root: $PROJECT_ROOT"
echo ""

# Check 1: Root directory should only have README.md
echo "═══════════════════════════════════════════════════════"
echo "1️⃣  Checking Root Directory..."
echo "═══════════════════════════════════════════════════════"

ROOT_MD_COUNT=$(find . -maxdepth 1 -name "*.md" -not -name "README_OLD.md" | wc -l)

if [ "$ROOT_MD_COUNT" -eq 1 ]; then
    echo -e "${GREEN}✅ PASS${NC}: Only README.md in root directory"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}: Found $ROOT_MD_COUNT markdown files in root (expected 1)"
    echo "Files:"
    find . -maxdepth 1 -name "*.md" -not -name "README_OLD.md"
    ((FAILED++))
fi

# Check 2: Docs folder exists
echo ""
echo "═══════════════════════════════════════════════════════"
echo "2️⃣  Checking Docs Folder..."
echo "═══════════════════════════════════════════════════════"

if [ -d "docs" ]; then
    echo -e "${GREEN}✅ PASS${NC}: docs/ folder exists"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}: docs/ folder not found"
    ((FAILED++))
fi

# Check 3: All required docs exist
echo ""
echo "═══════════════════════════════════════════════════════"
echo "3️⃣  Checking Required Documentation Files..."
echo "═══════════════════════════════════════════════════════"

REQUIRED_DOCS=(
    "docs/README.md"
    "docs/ARCHITECTURE.md"
    "docs/API_DOCUMENTATION.md"
    "docs/SETUP_GUIDE.md"
    "docs/QUICK_REFERENCE.md"
)

for doc in "${REQUIRED_DOCS[@]}"; do
    if [ -f "$doc" ]; then
        SIZE=$(du -h "$doc" | cut -f1)
        echo -e "${GREEN}✅${NC} $doc ($SIZE)"
        ((PASSED++))
    else
        echo -e "${RED}❌${NC} $doc (MISSING)"
        ((FAILED++))
    fi
done

# Check 4: Old docs removed from root
echo ""
echo "═══════════════════════════════════════════════════════"
echo "4️⃣  Checking for Old Documentation in Root..."
echo "═══════════════════════════════════════════════════════"

OLD_DOCS=(
    "SYSTEM_ARCHITECTURE.md"
    "INTEGRATION_GUIDE.md"
    "QUICK_START.md"
    "CONSOLIDATION_SUMMARY.md"
    "API_CONFIG.md"
    "DEPLOYMENT_GUIDE.md"
)

FOUND_OLD=0
for old_doc in "${OLD_DOCS[@]}"; do
    if [ -f "$old_doc" ]; then
        echo -e "${YELLOW}⚠️  WARN${NC}: Found old doc in root: $old_doc"
        FOUND_OLD=$((FOUND_OLD + 1))
    fi
done

if [ $FOUND_OLD -eq 0 ]; then
    echo -e "${GREEN}✅ PASS${NC}: No old documentation in root"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  WARN${NC}: Found $FOUND_OLD old documentation file(s) in root"
    echo "Run: bash scripts/cleanup_docs.sh"
fi

# Check 5: Documentation statistics
echo ""
echo "═══════════════════════════════════════════════════════"
echo "5️⃣  Documentation Statistics..."
echo "═══════════════════════════════════════════════════════"

if [ -d "docs" ]; then
    DOCS_COUNT=$(find docs/ -name "*.md" | wc -l)
    DOCS_SIZE=$(du -sh docs/ | cut -f1)
    TOTAL_LINES=$(find docs/ -name "*.md" -exec wc -l {} + | tail -1 | awk '{print $1}')
    
    echo "📊 Files: $DOCS_COUNT markdown files"
    echo "📦 Size: $DOCS_SIZE"
    echo "📝 Lines: $TOTAL_LINES total lines"
    ((PASSED++))
fi

# Summary
echo ""
echo "═══════════════════════════════════════════════════════"
echo "📊 VERIFICATION SUMMARY"
echo "═══════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Passed${NC}: $PASSED checks"
echo -e "${RED}❌ Failed${NC}: $FAILED checks"

if [ $FOUND_OLD -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Warnings${NC}: $FOUND_OLD old files"
fi

echo ""

# Final status
if [ $FAILED -eq 0 ]; then
    echo "═══════════════════════════════════════════════════════"
    echo -e "${GREEN}✨ ALL CHECKS PASSED! Documentation is properly organized.${NC}"
    echo "═══════════════════════════════════════════════════════"
    exit 0
else
    echo "═══════════════════════════════════════════════════════"
    echo -e "${RED}❌ VERIFICATION FAILED! Please review the errors above.${NC}"
    echo "═══════════════════════════════════════════════════════"
    exit 1
fi
