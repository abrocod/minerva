#!/usr/bin/env python3
"""
Test script to verify Evernote connectivity and AppleScript functionality.

This script performs basic checks to ensure the Evernote extractor will work properly.
"""

import subprocess
import sys


def run_applescript(script: str) -> tuple[bool, str]:
    """
    Execute AppleScript and return success status and result.
    
    Args:
        script: AppleScript code to execute
        
    Returns:
        Tuple of (success, result/error_message)
    """
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
        return True, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "AppleScript execution timed out"
    except subprocess.CalledProcessError as e:
        return False, f"AppleScript execution failed: {e.stderr.strip()}"
    except FileNotFoundError:
        return False, "osascript command not found (not on macOS?)"


def test_evernote_running():
    """Test if Evernote is running."""
    print("🔍 Checking if Evernote is running...")
    
    script = '''
    tell application "System Events"
        return (name of processes) contains "Evernote"
    end tell
    '''
    
    success, result = run_applescript(script)
    if success:
        is_running = result.lower() == "true"
        if is_running:
            print("✅ Evernote is running")
            return True
        else:
            print("❌ Evernote is not running")
            print("   Please start Evernote and try again")
            return False
    else:
        print(f"❌ Failed to check Evernote status: {result}")
        return False


def test_evernote_accessibility():
    """Test if we can access Evernote via AppleScript."""
    print("\n🔍 Testing Evernote accessibility...")
    
    script = '''
    tell application "Evernote"
        return name
    end tell
    '''
    
    success, result = run_applescript(script)
    if success:
        print(f"✅ Successfully connected to Evernote: {result}")
        return True
    else:
        print(f"❌ Cannot access Evernote: {result}")
        print("   This might be a permissions issue.")
        print("   Go to System Preferences → Security & Privacy → Privacy")
        print("   Add Terminal to Accessibility and Automation permissions")
        return False


def test_notebook_access():
    """Test if we can list notebooks."""
    print("\n🔍 Testing notebook access...")
    
    script = '''
    tell application "Evernote"
        set notebookNames to {}
        repeat with nb in notebooks
            set end of notebookNames to name of nb
        end repeat
        set AppleScript's text item delimiters to "|"
        set notebookString to notebookNames as string
        set AppleScript's text item delimiters to ""
        return notebookString
    end tell
    '''
    
    success, result = run_applescript(script)
    if success:
        if result:
            notebooks = [nb.strip() for nb in result.split('|') if nb.strip()]
            print(f"✅ Found {len(notebooks)} notebooks:")
            for nb in notebooks[:5]:  # Show first 5
                print(f"   📁 {nb}")
            if len(notebooks) > 5:
                print(f"   ... and {len(notebooks) - 5} more")
            return True
        else:
            print("⚠️  No notebooks found (or empty result)")
            return False
    else:
        print(f"❌ Cannot access notebooks: {result}")
        return False


def test_note_count():
    """Test if we can count notes in the first notebook."""
    print("\n🔍 Testing note counting...")
    
    # First get a notebook name
    script = '''
    tell application "Evernote"
        if (count of notebooks) > 0 then
            return name of first notebook
        else
            return ""
        end if
    end tell
    '''
    
    success, notebook_name = run_applescript(script)
    if not success or not notebook_name:
        print("❌ Cannot get notebook name for testing")
        return False
    
    # Now count notes in that notebook
    script = f'''
    tell application "Evernote"
        set targetNotebook to notebook "{notebook_name}"
        return count of notes of targetNotebook
    end tell
    '''
    
    success, result = run_applescript(script)
    if success:
        try:
            count = int(result)
            print(f"✅ Notebook '{notebook_name}' has {count} notes")
            return True
        except ValueError:
            print(f"❌ Invalid note count result: {result}")
            return False
    else:
        print(f"❌ Cannot count notes: {result}")
        return False


def main():
    """Run all tests."""
    print("🧪 Evernote Extractor Connectivity Test")
    print("=" * 40)
    
    tests = [
        test_evernote_running,
        test_evernote_accessibility,
        test_notebook_access,
        test_note_count
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            break  # Stop on first failure
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! The Evernote extractor should work properly.")
        print("\nYou can now run:")
        print("   python3 evernote_extractor_applescript.py --check-only")
        print("   python3 evernote_extractor_applescript.py")
    else:
        print("⚠️  Some tests failed. Please address the issues above before running the extractor.")
        
        if passed == 0:
            print("\n💡 Quick fixes to try:")
            print("   1. Make sure Evernote is running")
            print("   2. Grant permissions in System Preferences")
            print("   3. Restart Terminal and try again")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 