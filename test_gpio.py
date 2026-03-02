#!/usr/bin/env python3
"""
Quick test for GPIO mock functionality
"""

print("Testing hardware_control import...")
try:
    from hardware_control import get_hardware_controller
    print("✅ Import successful")
    
    print("\nInitializing hardware controller...")
    controller = get_hardware_controller()
    print("✅ Controller initialized")
    
    print("\nTesting control...")
    controller.update_control("pump", True)
    print("✅ Control update successful")
    
    print("\nGetting states...")
    states = controller.get_all_states()
    print(f"✅ States: {states}")
    
    print("\n" + "="*50)
    print("✅ ALL TESTS PASSED - System ready to run!")
    print("="*50)
    print("\nNow try: python3 main.py --lcd --demo")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
