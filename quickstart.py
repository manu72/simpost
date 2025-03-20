"""
This script demonstrates how to use the OpenAI API to generate a response.
It uses the gpt-4o model to generate a one-sentence bedtime story about a unicorn.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

MODEL="gpt-4o-mini"

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# simple example using responses API replacement for chat.completions
response = client.responses.create(
    model=MODEL,
    input="Write a one-sentence bedtime story about a unicorn wedding.",
    instructions="You are a professional social media copywriter.",
    max_output_tokens=100,
    store=True,
    temperature=0.7,
    user="user_123"
)

print(response.output_text)

# simple example using responses API with tools
response2 = client.responses.create(
    model=MODEL,
    tools=[{"type": "web_search_preview"}],
    input="What was a news story about Trump from today?",
    instructions="You are a professional journalist writing for the left-leaning Trumpmania website.",
    max_output_tokens=1000,
    store=True,
    temperature=0.3,
    user="journo_123"
)

print(response2.output_text)
print(response2.output_tokens)

# simple example using responses API with streaming
stream = client.responses.create(
    model=MODEL,
    input=[
        {
            "role": "user",
            "content": "Say 'doublebubblebath' five times fast.",
        },
    ],
    stream=True,
)

#for event in stream:
#    print(event)
