"""Use it only for start launcher module
"""

try:
    import launcher
    launcher.launch()
except:
    import traceback
    print "\nUnexpected error:\n"
    traceback.print_exc()
    raw_input("\nProcess canceled. Press Enter for close...")
