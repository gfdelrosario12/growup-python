# 📚 GrowUp IoT System - Documentation Quick Reference

## 🗂️ Documentation Location

**All documentation is now in:** `/home/gladwin/Documents/Personal/Grow Up/rpi/docs/`

```
rpi/
├── README.md              ← Start here for quick overview
│
└── docs/                  ← All detailed documentation
    ├── README.md         ← Documentation navigation
    ├── ARCHITECTURE.md   ← System design
    ├── API_DOCUMENTATION.md  ← API reference
    └── SETUP_GUIDE.md    ← Installation guide
```

---

## 🚀 Quick Commands

### View Documentation
```bash
# Main project overview
cat README.md

# Documentation index
cat docs/README.md

# Architecture
cat docs/ARCHITECTURE.md

# API reference
cat docs/API_DOCUMENTATION.md

# Setup guide
cat docs/SETUP_GUIDE.md
```

### Cleanup Old Files
```bash
# Remove old documentation from root
bash scripts/cleanup_docs.sh
```

### Verify Structure
```bash
# Verify documentation organization
bash scripts/verify_docs.sh
```

---

## 📖 What's in Each Document?

### README.md (Root) - 10 min read
- ✅ Project overview
- ✅ Quick start guide
- ✅ Feature list
- ✅ Basic installation
- ✅ Troubleshooting basics

**When to use:** First time learning about the project

---

### docs/README.md - 5 min read
- ✅ Documentation overview
- ✅ Navigation guide
- ✅ Role-based paths
- ✅ Version tracking

**When to use:** Finding the right documentation

---

### docs/ARCHITECTURE.md - 20 min read
- ✅ System architecture diagrams
- ✅ Data flow sequences
- ✅ Hardware specifications
- ✅ Performance metrics
- ✅ Scalability options

**When to use:** Understanding how the system works

---

### docs/API_DOCUMENTATION.md - 30 min read
- ✅ All API endpoints
- ✅ Request/response formats
- ✅ Integration examples
- ✅ Testing commands
- ✅ Error handling

**When to use:** Developing or debugging API calls

---

### docs/SETUP_GUIDE.md - 45 min read
- ✅ Prerequisites
- ✅ Installation steps
- ✅ Configuration
- ✅ Service setup
- ✅ Troubleshooting

**When to use:** Setting up the system

---

## 🎯 Documentation by Use Case

### "I'm setting up for the first time"
1. Read: `README.md` (overview)
2. Follow: `docs/SETUP_GUIDE.md` (step-by-step)
3. Reference: `docs/API_DOCUMENTATION.md` (if needed)

### "I'm developing/integrating"
1. Read: `docs/ARCHITECTURE.md` (understand system)
2. Use: `docs/API_DOCUMENTATION.md` (API reference)
3. Check: Root `README.md` (quick examples)

### "I have a problem"
1. Check: Root `README.md` → Troubleshooting section
2. Review: `docs/SETUP_GUIDE.md` → Troubleshooting
3. Verify: Run `bash scripts/verify_docs.sh`

### "I want to understand the design"
1. Read: `docs/ARCHITECTURE.md` (complete architecture)
2. Check: `docs/API_DOCUMENTATION.md` (data formats)
3. Review: Code comments in `main.py`

---

## 🧹 Maintenance

### Check Documentation Status
```bash
cd /home/gladwin/Documents/Personal/Grow\ Up/rpi
bash scripts/verify_docs.sh
```

### Clean Up Old Files
```bash
cd /home/gladwin/Documents/Personal/Grow\ Up/rpi
bash scripts/cleanup_docs.sh
```

### Update Documentation
```bash
# Edit files in docs/ folder only
nano docs/API_DOCUMENTATION.md
nano docs/SETUP_GUIDE.md
# etc.

# Don't create documentation files in root (except README.md)
```

---

## ✅ Verification Checklist

Before committing/deploying:

- [ ] All docs are in `docs/` folder
- [ ] Root README.md exists
- [ ] No old `.md` files in root (except README.md)
- [ ] `verify_docs.sh` passes
- [ ] All links work
- [ ] Version numbers updated

---

## 📞 Getting Help

### Finding Information
1. **Quick Start**: `README.md`
2. **Navigation**: `docs/README.md`
3. **Deep Dive**: Specific doc in `docs/`

### Common Questions

**Q: Where are the API docs?**  
A: `docs/API_DOCUMENTATION.md`

**Q: How do I install?**  
A: `docs/SETUP_GUIDE.md`

**Q: Where's the architecture?**  
A: `docs/ARCHITECTURE.md`

**Q: Which doc should I read first?**  
A: Start with root `README.md`

---

## 🔗 Quick Links (Local)

```bash
# Project root
cd /home/gladwin/Documents/Personal/Grow\ Up/rpi

# Documentation folder
cd /home/gladwin/Documents/Personal/Grow\ Up/rpi/docs

# Scripts folder
cd /home/gladwin/Documents/Personal/Grow\ Up/rpi/scripts
```

---

## 📊 Documentation Stats

- **Total Files**: 5 markdown files
- **Total Lines**: ~3,500 lines
- **Read Time**: ~2 hours (all docs)
- **Setup Time**: ~45 minutes (following guide)

---

**Last Updated**: January 2024  
**Status**: ✅ Organized & Complete
