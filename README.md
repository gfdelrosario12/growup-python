# 🌱 GrowUp IoT System - Raspberry Pi

> Professional, modular aquaponics monitoring and control system with hybrid automation

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)](#)

**Version:** 2.0.0 | **Last Updated:** March 2026

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [MQTT Control](#-mqtt-control)
- [Camera Streaming](#-camera-streaming)
- [API Reference](#-api-reference)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Hardware Setup](#-hardware-setup)
- [Troubleshooting](#-troubleshooting)
- [Project Structure](#-project-structure)

---

## 🎯 Overview

GrowUp IoT is a complete aquaponics monitoring and control system for Raspberry Pi that provides:

- **Real-time Monitoring** - 6 environmental sensors (temperature, pH, humidity, ammonia, light, water flow)
- **Smart Control** - GPIO-based relay control for 4 devices (pump, fan, aerator, grow light)
- **Hybrid Automation** - Preset-based automation with manual override support
- **Remote Control** - MQTT-based control from any platform
- **AI Vision** - YOLO object detection with WebSocket streaming
- **REST API** - Flask-based API for external integrations
- **External Access** - ngrok-ready for remote monitoring

### What Makes It Special

✅ **Modular Architecture** - 24 independent modules, easy to maintain and extend  
✅ **Hybrid Control** - Preset automation + manual override with priority management  
✅ **Production Ready** - Systemd service, deployment scripts, comprehensive testing  
✅ **Development Friendly** - Mock GPIO support, no hardware required for dev  
✅ **Complete Documentation** - Everything you need in this single README  

---

## ✨ Features

### Monitoring
- 🌡️ **Water Temperature** - DS18B20 sensor
- 🌡️ **Air Temperature** - BME280 sensor
- 💧 **Humidity** - BME280 sensor
- 🧪 **pH Level** - PH4502C sensor
- ☠️ **Ammonia** - MQ137 sensor
- 💡 **Light Intensity** - BH1750 sensor
- 💦 **Water Flow** - YF-S201 sensor

### Control
- 🔌 **GPIO Relay Control** - 4 devices with individual control
- 🤖 **Preset Automation** - 4 pre-configured presets (growth, night, maintenance, eco)
- ✋ **Manual Override** - Per-device manual control with priority management
- 🔄 **Dynamic Switching** - Change presets on the fly
- 📡 **MQTT Integration** - Real-time control via MQTT topics

### Services
- 📷 **AI Vision** - YOLO v8 object detection
- 📡 **WebSocket Streaming** - Real-time camera feed
- 🌐 **REST API** - Flask-based HTTP API
- 🖥️ **LCD Viewer** - Optional Tkinter GUI
- 📊 **InfluxDB** - Time-series data storage (optional)

### Deployment
- 🚀 **Systemd Service** - Auto-start on boot
- 🔧 **Automated Setup** - One-command deployment
- 🧪 **Test Suite** - Comprehensive testing
- 📝 **Complete Logging** - systemd journal integration

