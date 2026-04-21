import sys
import os

# Add the parent directory to sys.path to import spelling_checker
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from spelling_checker import _is_suspicious_correction, _diff_words
except ImportError:
    # If standard import fails, try relative to the script
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from spelling_checker import _is_suspicious_correction, _diff_words

def test_logic():
    cases = [
        # Original, Suggested, ShouldBeFiltered
        ("Print", "Print.", True),
        ("Date:", "Date, Date, Notes.", True),
        ("PRN:", "PRNLP", True),
        ("Action", "Action.", True),
        ("LEVEL", "level,", True),
        ("ABCID.", "ABCID.2", True),
        ("Yes No", "Yes? No,", True),
        ("Note:", "Note Notes", True),
        ("&", "and", True), # Very short/symbol
        ("Course(s)", "Course (s)", True), # Punctuation/spacing
        
        # Valid errors should NOT be filtered
        ("Goregous", "Gorgeous", False),
        ("recieve", "receive", False),
        ("identy", "identity", False),
    ]

    print("Running Spelling Logic Tests...")
    passed = 0
    fail = 0

    for orig, corr, should_filter in cases:
        filtered = _is_suspicious_correction(orig, corr)
        if filtered == should_filter:
            print(f" [PASS] '{orig}' -> '{corr}' (Filtered: {filtered})")
            passed += 1
        else:
            print(f" [FAIL] '{orig}' -> '{corr}'")
            print(f"      Expected Filtered: {should_filter}, but Got: {filtered}")
            fail += 1

    print(f"\nSummary: {passed} passed, {fail} failed.")
    
    if fail > 0:
        sys.exit(1)

if __name__ == "__main__":
    test_logic()
