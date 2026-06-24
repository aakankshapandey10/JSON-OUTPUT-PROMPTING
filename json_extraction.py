# json_extraction.py — 2-step pipeline
# Step 1: extract action items → JSON
# Step 2: reformat that JSON → Markdown table

import anthropic   # the official Anthropic Python SDK — lets us talk to Claude
import json        # standard library — converts between JSON strings and Python dicts/lists
import os          # standard library — reads environment variables (API keys, etc.)
import re          # standard library — regular expressions, used to strip accidental code fences
from dotenv import load_dotenv   # third-party — reads key=value pairs from a .env file into os.environ

load_dotenv()   # actually reads the .env file; must come before any os.getenv() call


# ─────────────────────────────────────────────────────────────────────────────
# INPUT — accept multi-line text from the terminal
# ─────────────────────────────────────────────────────────────────────────────
print("Paste your text (then press Enter twice when done):")

lines = []          # empty list; each line the user types gets appended here
while True:         # loop forever until we hit the break condition below
    line = input()  # input() pauses and waits for the user to type a line + press Enter
    if line == "":  # an empty line (just Enter) signals "done typing"
        break       # exit the while loop
    lines.append(line)   # store the non-empty line

meeting_note = "\n".join(lines)   # glue all lines back together with real newlines


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 PROMPT — tell Claude to return valid JSON only
# ─────────────────────────────────────────────────────────────────────────────
# f-string: curly braces {} inject Python values; {{ }} is a literal brace in the output
step1_prompt = f"""
Extract every action item from the meeting note below.

Think step by step to ensure you don't miss any action items.

Here are examples of correct extractions:

Example 1:
Meeting note: "Alice will send the report by Friday."
Output: {{"items": [{{"name": "Alice", "date": "Friday", "action": "send the report"}}]}}

Example 2:
Meeting note: "Bob and Carol need to review the contract. No deadline given."
Output: {{"items": [{{"name": "Bob", "date": null, "action": "review the contract"}}, {{"name": "Carol", "date": null, "action": "review the contract"}}]}}

Example 3:
Meeting note: "The team agreed David will set up the server by June 30."
Output: {{"items": [{{"name": "David", "date": "June 30", "action": "set up the server"}}]}}

Now extract from this meeting note:

Return a JSON object with a single key "items", which is a list of objects.
"name": the full name of the person responsible for the action item
"date": the date mentioned in the action item, or null if none
"action": a brief description of what they need to do

If there are multiple people quoted in the same action item, return them as separate objects.

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


# ─────────────────────────────────────────────────────────────────────────────
# API CLIENT — one client object, reused for both calls
# ─────────────────────────────────────────────────────────────────────────────
# anthropic.Anthropic() creates the client; base_url + api_key come from .env
client = anthropic.Anthropic(
    base_url=os.getenv("AZURE_BASE_URL"),   # Azure-hosted Claude endpoint
    api_key=os.getenv("AZURE_API_KEY"),     # secret key — never hardcode this
)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 CALL — send the prompt, get JSON back
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Step 1: extracting action items as JSON ──")

step1_response = client.messages.create(
    model="claude-haiku-4-5",          # which Claude model to use
    max_tokens=512,                    # hard cap on how many tokens the reply can use
    messages=[
        {"role": "user", "content": step1_prompt}   # the conversation so far (just one message)
    ]
)

# message.content is a list of content blocks; [0] is the first (and only) block
# .text extracts the plain string from that block
raw_json = step1_response.content[0].text

print("Raw Step 1 response:")
print(raw_json)
print()


# ─────────────────────────────────────────────────────────────────────────────
# PARSE — convert the raw string into a real Python object
# ─────────────────────────────────────────────────────────────────────────────
try:
    # re.sub() finds the pattern and replaces it with "" (nothing)
    # pattern: optional opening ```json or ``` at the start, optional closing ``` at the end
    # flags=re.MULTILINE makes ^ and $ match start/end of each line, not just the whole string
    clean_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_json.strip(), flags=re.MULTILINE)

    # json.loads() parses a JSON string → Python dict/list; raises json.JSONDecodeError on bad input
    parsed = json.loads(clean_json)

    print("Parsed Python object:")
    print(parsed)          # shows the dict so you can verify the structure
    print()

    # parsed["items"] is a list of dicts, one per action item
    items = parsed["items"]

    # Quick preview of what Step 1 found
    print("Action items found:")
    for item in items:
        # item is a dict with keys: name, date, action
        print(f"  {item['name']} | {item['date']} | {item['action']}")
    print()


    # ─────────────────────────────────────────────────────────────────────────
    # STEP 2 PROMPT — give Claude the JSON, ask for a Markdown table
    # ─────────────────────────────────────────────────────────────────────────
    # json.dumps() converts the Python dict back to a formatted JSON string
    # indent=2 adds two spaces of indentation per level — makes it readable
    json_for_step2 = json.dumps(parsed, indent=2)

    step2_prompt = f"""
You are a formatter. Convert the JSON below into a clean Markdown table.

Rules:
- Column headers must be: | Name | Due Date | Action Item |
- One row per item in the "items" array
- If "date" is null, write "No date" in that cell
- Output ONLY the Markdown table — no explanation, no extra text

JSON:
{json_for_step2}
"""

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 2 CALL — send the JSON, get a Markdown table back
    # ─────────────────────────────────────────────────────────────────────────
    print("── Step 2: reformatting JSON into a Markdown table ──")

    step2_response = client.messages.create(
        model="claude-haiku-4-5",   # same model; Haiku is fast and cheap for formatting tasks
        max_tokens=512,             # a table won't need many tokens
        messages=[
            {"role": "user", "content": step2_prompt}
        ]
    )

    # pull the plain text out of the response, same pattern as Step 1
    markdown_table = step2_response.content[0].text.strip()

    print("\nMarkdown table output:")
    print(markdown_table)   # this is the final deliverable — ready to paste into any .md file


# ─────────────────────────────────────────────────────────────────────────────
# ERROR HANDLING — if Step 1 returned something unparseable, explain why
# ─────────────────────────────────────────────────────────────────────────────
except json.JSONDecodeError as e:
    # json.JSONDecodeError tells us exactly where the bad character was
    print(f"Failed to parse JSON from Step 1: {e}")
    print("Claude returned something that isn't valid JSON — check the raw response above.")
