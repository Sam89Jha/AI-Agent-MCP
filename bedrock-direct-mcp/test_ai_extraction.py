#!/usr/bin/env python3
"""
Test script to see what the AI is actually extracting
"""

import json
import boto3

def test_ai_extraction():
    """Test the AI extraction directly"""
    
    # Initialize Bedrock client
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    test_inputs = [
        "Send message to driver that I am running late",
        "Tell the passenger I'm on my way", 
        "Call the driver",
        "Get message history"
    ]
    
    print("🤖 Testing AI Extraction Directly")
    print("=" * 50)
    
    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n📝 Test {i}: {user_input}")
        
        prompt = f"""
You are a communication assistant for a Grab-like system. Your job is to understand natural language inputs from the user and route them to a backend API through structured parameters.

You will receive inputs like:
- "Send message to driver that I am waiting for him"
- "Call the passenger"
- "Show me the chat history"

You must extract and return these fields in the final API call:

- `user_type`: either "driver" or "passenger"
- `intent`: one of the following 3 values:
    - "send-message"
    - "make-call"
    - "get-message-list"
- `message`: only when the intent is "send-message", this is the actual content the user wants sent
- `user_input`: original user query (string)
- `confidence`: confidence score for intent (numeric)

---

🔹 Examples:

Input: "Send message to driver that I'm on the way"  
→ intent: `send-message`  
→ message: `"I'm on the way"`

Input: "Call the passenger now"  
→ intent: `make-call`  
→ message: `null`

Input: "Show me my message history"  
→ intent: `get-message-list`  
→ message: `null`

---

User Input: "{user_input}"

Respond with ONLY a JSON object in this format:
{{
    "intent": "send-message|make-call|get-message-list",
    "message": "extracted message content or null",
    "user_type": "driver|passenger",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of why this intent was chosen"
}}
"""
        
        try:
            # Use Claude 3 Haiku for fast intent detection
            response = bedrock.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 200,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            print(f"🤖 AI Response: {content}")
            
            # Try to extract JSON
            try:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = content[start:end]
                    result = json.loads(json_str)
                    print(f"✅ Parsed JSON: {json.dumps(result, indent=2)}")
                else:
                    print("❌ No JSON found in response")
            except json.JSONDecodeError as e:
                print(f"❌ JSON parse error: {e}")
                
        except Exception as e:
            print(f"❌ Bedrock error: {str(e)}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_ai_extraction() 