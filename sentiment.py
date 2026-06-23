import anthropic
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

review = """
I've been using this product for three months and it's mostly great. The interface is clean and
the customer support team responded within minutes when I had an issue. That said, the mobile app
crashes at least once a day and the export feature has been broken for weeks. I really want to
love it but these bugs are making it hard to recommend to my team.
"""

prompt = f"""
Analyze the sentiment of the review below.

<review>
{review}
</review>

Respond ONLY with valid JSON. No explanation, no markdown, no code fences.

Return this exact structure:
{{
  "overall": "positive | negative | mixed",
  "score": <number from 1 (very negative) to 5 (very positive)>,
  "positives": ["thing they liked 1", "thing they liked 2"],
  "negatives": ["complaint 1", "complaint 2"],
  "would_recommend": true or false,
  "summary": "one sentence summary of the review"
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
    print(f"Overall:         {parsed['overall']}")
    print(f"Score:           {parsed['score']} / 5")
    print(f"Would recommend: {parsed['would_recommend']}")
    print(f"Summary:         {parsed['summary']}")
    print("\nPositives:")
    for p in parsed["positives"]:
        print(f"  + {p}")
    print("\nNegatives:")
    for n in parsed["negatives"]:
        print(f"  - {n}")
except json.JSONDecodeError as e:
    print(f"Parse error: {e}\nRaw: {raw}")
