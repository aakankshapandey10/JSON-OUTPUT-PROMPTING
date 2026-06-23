import anthropic
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

document = """
Our Q2 results showed strong growth in the enterprise segment, with revenue up 34% year over year.
However, the SMB segment underperformed due to increased churn in the first half of the quarter.
The product team shipped three major features: real-time collaboration, an improved onboarding flow,
and a new analytics dashboard. Customer satisfaction scores rose to 4.6 out of 5.
Action items: Sarah will lead a churn reduction initiative by July 15th. Engineering will prioritize
performance fixes next sprint. Marketing needs to update the pricing page before the campaign launch.
"""

prompt = f"""
Summarize the document below.

<document>
{document}
</document>

Respond ONLY with valid JSON. No explanation, no markdown, no code fences.

Return this exact structure:
{{
  "title": "short title for this document",
  "key_points": ["point 1", "point 2", "point 3"],
  "next_steps": [
    {{
      "owner": "person responsible",
      "task": "what they need to do",
      "deadline": "deadline or null"
    }}
  ],
  "sentiment": "positive | negative | mixed"
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
    print(f"Title:      {parsed['title']}")
    print(f"Sentiment:  {parsed['sentiment']}")
    print("\nKey points:")
    for point in parsed["key_points"]:
        print(f"  - {point}")
    print("\nNext steps:")
    for step in parsed["next_steps"]:
        print(f"  [{step['owner']}] {step['task']} — {step['deadline']}")
except json.JSONDecodeError as e:
    print(f"Parse error: {e}\nRaw: {raw}")
