import json

def assert_response(response, expected_code: int, test_step_name: str, check_json=None):
    """
    Asserts the response status code and prints a formatted test result.
    
    Format:
    Test case {name} | Expected: {expected} | Actual: {actual} | Status: {PASS/FAIL}
    """
    actual_code = response.status_code
    status = "PASS" if actual_code == expected_code else "FAIL"
    
    print(f"\nTest case {test_step_name} | Expected: {expected_code} | Actual: {actual_code} | Status: {status}")
    
    if status == "FAIL":
        print(f"   > Response Body: {response.text}")
    
    assert actual_code == expected_code
    
    if check_json:
        data = response.json()
        for key, value in check_json.items():
            actual_val = data.get(key)
            match = actual_val == value
            sub_status = "PASS" if match else "FAIL"
            print(f"   - Check '{key}': Expected '{value}' | Actual '{actual_val}' | {sub_status}")
            assert match, f"JSON field '{key}' mismatch"
