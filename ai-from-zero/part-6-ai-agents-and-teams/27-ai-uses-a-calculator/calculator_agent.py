# Your first AGENT: Claude can use a calculator tool that YOU wrote. The full agent loop, written out.
import sys

import ai


# 1. THE TOOL: a normal Python function
def calculate(expression):
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:                  # safety: only digits and maths symbols
        return "Error: only numbers and + - * / ( ) are allowed"
    return str(eval(expression))


# 2. DESCRIBE the tool so the AI knows it exists and how to call it
calculator_tool = {
    "name": "calculate",
    "description": "Calculates a maths expression exactly. Always use this for arithmetic.",
    "input_schema": {"type": "object", "properties": {"expression": {"type": "string", "description": "e.g. (1234 * 5678) / 2"}},
                     "required": ["expression"]},
}

question = " ".join(sys.argv[1:]) or "I buy 17 notebooks at $3.45 and 4 pens at $1.20. I pay with $100. How much change?"
messages = [{"role": "user", "content": question}]

# 3. THE AGENT LOOP: ask → if it wants the tool, run it and send back the result → ask again
while True:
    response = ai.send(messages=messages, max_tokens=2000, tools=[calculator_tool],
                       system="You are a helpful assistant. Use the calculate tool for every calculation.")
    messages.append({"role": "assistant", "content": response.content})

    if response.stop_reason != "tool_use":              # the AI didn't ask for a tool → it's finished
        print("\n💬", "".join(b.text for b in response.content if b.type == "text"))
        break

    results = []
    for block in response.content:
        if block.type == "tool_use":
            answer = calculate(**block.input)
            print(f"🔧 the AI used calculate({block.input['expression']}) → {answer}")
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": answer})
    messages.append({"role": "user", "content": results})   # hand the results back to the AI
