# JSON Parsing Problem Fix

The JSON parsing issue was found in the `handle_tool_call` method from the `kubectl_mcp_tool/core/mcp_server.py` file. Here's how I tried resolving it.

## The Issue
The original code had the potential for a JSON parsing issue at this line: 
```python
tool_input = params.get("input", {})
```
This line had the assumption the input was always going to be a dictionary (JSON Object) and did not account for three different cases where:
1. The input would be a JSON string that would need to be parsed.
2. The input may or may not actually contain valid JSON.
3. The input could actually be of a different unexpected type

## The Fix
The fix introduces proper handling of JSON with the following code improvements:

1. **Type Checking**: The code will now check to see if the input is one of the following:   
   - A string (indicating the input requires JSON parsing)   
   - A dict (indicating the input is already parsed JSON)   
   - Any other type (indicating invalid input case) 
   
2. **Proper Error Handling**: A try-catch block was added specifically for parsing errors in the following way:    
   - Provided clear, explicit error messages   
   - Use proper JSON-RPC error codes,   
   - Logging the error   
   - Failure responses are sent to the client follow a clean pattern.

3. **Default Value**:  The default value was changed to "{}" (empty JSON string), which can easily be parsed into an empty dict.