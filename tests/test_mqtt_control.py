#!/usr/bin/env python3
"""
MQTT Control Test Script
Tests MQTT device control functionality
"""

import time
import sys

def test_mqtt_import():
    """Test if MQTT module can be imported"""
    print("Testing MQTT imports...")
    try:
        import paho.mqtt.client as mqtt
        print("✅ paho-mqtt installed")
        return True
    except ImportError:
        print("❌ paho-mqtt not installed")
        print("   Install with: pip install paho-mqtt")
        return False


def test_mqtt_control_module():
    """Test if mqtt_control module can be imported"""
    print("\nTesting mqtt_control module...")
    try:
        from mqtt_control import MQTTControlHandler, get_mqtt_handler
        print("✅ mqtt_control.py imports successfully")
        return True
    except ImportError as e:
        print(f"❌ mqtt_control.py import failed: {e}")
        return False
    except Exception as e:
        print(f"⚠️  mqtt_control.py has issues: {e}")
        return False


def test_hardware_control():
    """Test if hardware control is available"""
    print("\nTesting hardware_control module...")
    try:
        from hardware_control import get_hardware_controller
        hw = get_hardware_controller()
        print("✅ hardware_control initialized")
        
        # Test getting states
        states = hw.get_all_states()
        print(f"   Current states: {states}")
        return True
    except Exception as e:
        print(f"❌ hardware_control failed: {e}")
        return False


def test_mqtt_connection(broker="localhost", port=1883):
    """Test MQTT broker connection"""
    print(f"\nTesting MQTT broker connection to {broker}:{port}...")
    try:
        import paho.mqtt.client as mqtt
        
        connected = [False]
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                connected[0] = True
            else:
                print(f"   Connection failed with code {rc}")
        
        client = mqtt.Client()
        client.on_connect = on_connect
        
        try:
            client.connect(broker, port, keepalive=5)
            client.loop_start()
            
            # Wait for connection
            for _ in range(10):
                if connected[0]:
                    break
                time.sleep(0.1)
            
            client.loop_stop()
            client.disconnect()
            
            if connected[0]:
                print(f"✅ MQTT broker reachable at {broker}:{port}")
                return True
            else:
                print(f"⚠️  Could not connect to MQTT broker at {broker}:{port}")
                return False
                
        except Exception as e:
            print(f"⚠️  MQTT broker not available: {e}")
            print("   This is OK if you haven't installed Mosquitto yet")
            print("   Install with: sudo apt-get install mosquitto mosquitto-clients")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def test_mqtt_handler_creation():
    """Test creating MQTT handler"""
    print("\nTesting MQTT handler creation...")
    try:
        from mqtt_control import get_mqtt_handler
        handler = get_mqtt_handler("test-device")
        print("✅ MQTT handler created successfully")
        print(f"   Device ID: {handler.device_id}")
        return True
    except Exception as e:
        print(f"❌ MQTT handler creation failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("MQTT Device Control - Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: paho-mqtt installed
    results.append(("paho-mqtt", test_mqtt_import()))
    
    # Test 2: mqtt_control module
    results.append(("mqtt_control", test_mqtt_control_module()))
    
    # Test 3: hardware_control
    results.append(("hardware_control", test_hardware_control()))
    
    # Test 4: MQTT broker
    results.append(("MQTT broker", test_mqtt_connection()))
    
    # Test 5: Handler creation
    results.append(("Handler creation", test_mqtt_handler_creation()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} - {name}")
        if result:
            passed += 1
    
    print("=" * 60)
    print(f"Results: {passed}/{len(results)} tests passed")
    print("=" * 60)
    
    if passed == len(results):
        print("\n🎉 All tests passed! MQTT control is ready to use.")
        print("\nQuick start:")
        print("  1. python main.py")
        print('  2. mosquitto_pub -t "growup/device/rpi-001/pump" -m "true"')
        return 0
    else:
        print("\n⚠️  Some tests failed. Review the output above.")
        if not results[0][1]:  # paho-mqtt not installed
            print("\n📦 Install required package:")
            print("   pip install paho-mqtt")
        if not results[3][1]:  # MQTT broker not available
            print("\n📡 Install MQTT broker (optional for testing):")
            print("   sudo apt-get install mosquitto mosquitto-clients")
        return 1


if __name__ == "__main__":
    sys.exit(main())
