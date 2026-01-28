def generate_python(task: str, output_schema: dict) -> str:
    """
    Replace this with OpenAI / local LLM call later.
    For now: simple deterministic codegen for basic numeric tasks.
    Must print a single JSON line.
    """
    t = task.lower()

    # naive number extraction
    import re
    nums = re.findall(r"-?\d+(?:\.\d+)?", t)
    if not nums:
        nums_list = []
    else:
        nums_list = [float(x) if "." in x else int(x) for x in nums]

    if "average" in t or "avg" in t or "mean" in t:
        return f"""import json
nums = {nums_list}
avg = (sum(nums) / len(nums)) if nums else None
print(json.dumps({{"average": avg}}))
"""
    if "sum" in t or "total" in t:
        return f"""import json
nums = {nums_list}
print(json.dumps({{"sum": sum(nums)}}))
"""
    if "min" in t or "minimum" in t:
        return f"""import json
nums = {nums_list}
print(json.dumps({{"min": (min(nums) if nums else None)}}))
"""
    if "max" in t or "maximum" in t:
        return f"""import json
nums = {nums_list}
print(json.dumps({{"max": (max(nums) if nums else None)}}))
"""

    # default: echo back message
    return """import json
print(json.dumps({"message": "Unsupported task in stub LLM. Plug a real LLM in llm.py."}))
"""
