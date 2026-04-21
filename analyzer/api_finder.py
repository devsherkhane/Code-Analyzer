def find_apis(parsed_script):
    """
    Returns API calls (axios, fetch, MQL) found natively via the Node AST execution.
    """
    apis = []
    
    try:
        if parsed_script and parsed_script.get("api_calls"):
            for api in parsed_script["api_calls"]:
                apis.append({
                    "method": api.get("method", "GET"),
                    "url": api.get("url", "[dynamic]"),
                    "payload": api.get("payload", "")
                })
    except Exception as e:
        print(f"  -> [APIs] Error mapping AST output: {e}")

    return apis