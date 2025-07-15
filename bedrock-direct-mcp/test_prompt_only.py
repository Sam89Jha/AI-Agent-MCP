#!/usr/bin/env python3
"""
Test script to verify the new prompt is working correctly
"""

import json
import boto3

def test_prompt_extraction():
    """Test the new prompt with various inputs"""
    
    # Initialize Bedrock client
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    test_cases = [
        {
            "input": "Send message to driver that I am running late",
            "expected_intent": "send-message",
            "expected_message": "I am running late"
        },
        {
            "input": "Tell the passenger I'm on my way",
            "expected_intent": "send-message", 
            "expected_message": "I'm on my way"
        },
        {
            "input": "Call the driver",
            "expected_intent": "make-call",
            "expected_message": None
        },
        {
            "input": "Get message history",
            "expected_intent": "get-message-list",
            "expected_message": None
        },
        {
            "input": "Send message: I'm at the pickup point",
            "expected_intent": "send-message",
            "expected_message": "I'm at the pickup point"
        },
        {
            "input": "Message to driver that I'll be there in 2 minutes",
            "expected_intent": "send-message",
            "expected_message": "I'll be there in 2 minutes"
        }
    ]
    
    print("🧪 Testing New Prompt Extraction")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        user_input = test_case["input"]
        expected_intent = test_case["expected_intent"]
        expected_message = test_case["expected_message"]
        
        print(f"\n📝 Test Case {i}: {user_input}")
        print(f"🎯 Expected: intent={expected_intent}, message={expected_message}")
        
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
            
            print(f"🤖 AI Raw Response: {content}")
            
            # Try to extract JSON
            try:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = content[start:end]
                    result = json.loads(json_str)
                    
                    # Check results
                    actual_intent = result.get('intent', 'unknown')
                    actual_message = result.get('message')
                    actual_user_type = result.get('user_type', 'unknown')
                    confidence = result.get('confidence', 0.0)
                    reasoning = result.get('reasoning', '')
                    
                    print(f"✅ Parsed JSON:")
                    print(f"   Intent: {actual_intent} (expected: {expected_intent})")
                    print(f"   Message: {actual_message} (expected: {expected_message})")
                    print(f"   User Type: {actual_user_type}")
                    print(f"   Confidence: {confidence}")
                    print(f"   Reasoning: {reasoning}")
                    
                    # Check if intent matches
                    if actual_intent == expected_intent:
                        print(f"✅ Intent correct!")
                    else:
                        print(f"❌ Intent mismatch!")
                    
                    # Check if message extraction is reasonable
                    if expected_message is None:
                        if actual_message is None or actual_message.lower() in ['null', 'none', '']:
                            print(f"✅ Message extraction correct (null)")
                        else:
                            print(f"⚠️  Message should be null but got: {actual_message}")
                    else:
                        if actual_message and expected_message.lower() in actual_message.lower():
                            print(f"✅ Message extraction looks good!")
                        else:
                            print(f"⚠️  Message extraction may need improvement")
                            print(f"   Expected: {expected_message}")
                            print(f"   Got: {actual_message}")
                    
                else:
                    print("❌ No JSON found in response")
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON parse error: {e}")
                
        except Exception as e:
            print(f"❌ Bedrock error: {str(e)}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_prompt_extraction() 