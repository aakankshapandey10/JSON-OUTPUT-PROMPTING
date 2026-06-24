import anthropic
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

# ── Step 1: Accept any text from the terminal ───────────────────────────────
print("Paste your text (then press Enter twice when done):")
lines = []
while True:
    line = input()
    if line == "":
        break
    lines.append(line)
meeting_note = "\n".join(lines)

# ── Step 2: Build the prompt ─────────────────────────────────────────────────
# - XML tags wrap the data so the model doesn't confuse it with instructions
# - The JSON schema tells the model exactly what fields to return
# - "Respond ONLY with valid JSON" is the hard constraint
prompt = f"""
Extract every action item from the meeting note below.

Think step by step to ensure you don't miss any action items.

Now extract from this meeting note:

Return a JSON object with a single key "items", which is a list of objects.
"name": the full name of the person responsible for the action item
"date": the date mentioned in the action item, or null if none
"action": a brief description of what they need to do

if there are multiple people quoted in the same action item, return them as separate objects in the list.


<meeting_note>
{meeting_note}
</meeting_note>

Respond ONLY with valid JSON. No explanation, no markdown, no code fences.

Return this exact structure:
{{
  "items": [
    {{
      "name": "person responsible",
      "date": "date mentioned, or null if none",
      "action": "what they need to do"
    }}
  ]
}}
"""

# ── Step 3: Call the Claude API ──────────────────────────────────────────────
client = anthropic.Anthropic(base_url=os.getenv("AZURE_BASE_URL"), api_key=os.getenv("AZURE_API_KEY"))

message = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=512,
    messages=[
        {"role": "user", "content": prompt}
    ]
)

raw_response = message.content[0].text
print("Raw response from Claude:")
print(raw_response)
print()

# ── Step 4: Parse the JSON with json.loads() ─────────────────────────────────
# json.loads() converts the JSON string into a Python dict/list
try:
    clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_response.strip(), flags=re.MULTILINE)
    parsed = json.loads(clean)
    print("Parsed Python object:")
    print(parsed)
    print()

    # ── Step 5: Use the structured data ─────────────────────────────────────
    print("Action items:")
    for item in parsed["items"]:
        print(f"  Name:   {item['name']}")
        print(f"  Date:   {item['date']}")
        print(f"  Action: {item['action']}")
        print()

except json.JSONDecodeError as e:
    print(f"Failed to parse JSON: {e}")
    print("Claude returned something that isn't valid JSON.")
