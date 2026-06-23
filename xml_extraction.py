import anthropic
import re
import os
from dotenv import load_dotenv

load_dotenv()

# ── Step 1: The meeting note to parse ───────────────────────────────────────
meeting_note = """
Alice will schedule the budget review meeting for July 5th.
Bob needs to send the Q2 report to the finance team by end of day.
"""

# ── Step 2: Build the prompt with XML tags ───────────────────────────────────
# - <meeting_note> wraps the data so the model won't confuse it with instructions
# - The model is told to wrap EACH action item in <item> tags with child tags
prompt = f"""
Extract every action item from the meeting note below.

<meeting_note>
{meeting_note}
</meeting_note>

Respond ONLY with XML. No explanation, no markdown, no code fences.

Use this exact structure for each action item:
<items>
  <item>
    <name>person responsible</name>
    <date>date mentioned, or null if none</date>
    <action>what they need to do</action>
  </item>
</items>
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

# ── Step 4: Extract data using regex on XML tags ──────────────────────────────
def extract_tag(text, tag):
    """Pull the first match of <tag>...</tag> from text."""
    match = re.search(f"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return match.group(1).strip() if match else None

def extract_all_tags(text, tag):
    """Pull every match of <tag>...</tag> from text."""
    return re.findall(f"<{tag}>(.*?)</{tag}>", text, re.DOTALL)

# Extract each <item> block, then pull fields from each
item_blocks = extract_all_tags(raw_response, "item")

print("Action items:")
for block in item_blocks:
    name   = extract_tag(block, "name")
    date   = extract_tag(block, "date")
    action = extract_tag(block, "action")
    print(f"  Name:   {name}")
    print(f"  Date:   {date}")
    print(f"  Action: {action}")
    print()
