import anthropic
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

text = """
On June 18th, Elon Musk met with Apple CEO Tim Cook at Apple's headquarters in Cupertino, California
to discuss a potential partnership between Tesla and Apple. Microsoft's Satya Nadella also joined
the meeting remotely from Redmond, Washington. The deal, reportedly worth $2 billion, is expected
to be announced at the San Francisco Tech Summit on August 3rd.
"""

prompt = f"""
Extract all named entities from the text below.

<text>
{text}
</text>

Respond ONLY with valid JSON. No explanation, no markdown, no code fences.

Return this exact structure:
{{
  "people": [
    {{"name": "full name", "role": "their title or role"}}
  ],
  "organizations": [
    {{"name": "org name", "type": "company | event | other"}}
  ],
  "locations": ["location 1", "location 2"],
  "dates": ["date 1", "date 2"],
  "monetary_values": ["value 1"]
}}
"""

client = anthropic.Anthropic(base_url=os.getenv("AZURE_BASE_URL"), api_key=os.getenv("AZURE_API_KEY"))

message = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=512,
    messages=[{"role": "user", "content": prompt}]
)

raw = message.content[0].text
clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)

try:
    parsed = json.loads(clean)
    print("People:")
    for p in parsed["people"]:
        print(f"  {p['name']} — {p['role']}")
    print("\nOrganizations:")
    for o in parsed["organizations"]:
        print(f"  {o['name']} ({o['type']})")
    print("\nLocations:  ", ", ".join(parsed["locations"]))
    print("Dates:      ", ", ".join(parsed["dates"]))
    print("Money:      ", ", ".join(parsed["monetary_values"]))
except json.JSONDecodeError as e:
    print(f"Parse error: {e}\nRaw: {raw}")
