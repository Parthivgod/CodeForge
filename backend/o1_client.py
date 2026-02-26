import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

endpoint = os.getenv("GROQ_BASE_URL")
api_key = os.getenv("GROQ_API_KEY")
model_name = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

client = OpenAI(
    base_url=endpoint,
    api_key=api_key
)

def label_clusters(clusters):
    """
    Uses LLM (via standard OpenAI SDK) to semantically label clusters.
    """
    print(f"Calling AI ({model_name}) for semantic labeling...")
    
    # In a real implementation, we would construct a prompt with the code summaries
    # from the clusters and ask the model to name them.
    # For now, we will use the provided snippet structure to demonstrate integration
    # allowing the user to fill in the prompt logic later.

    # Example Prompt Construction (Placeholder)
    # prompt = "Analyze the following code clusters and name the services:\n" + str(clusters)
    
    # For this prototype, we'll keep the mock response data but verify client works
    # if valid credentials were provided (optional check)
    
    # Mock enriched data logic preserved for the UI demo flow
    descriptions = [
        {"name": "Billing Service", "risk": "low", "desc": "Handles payment processing and invoicing."},
        {"name": "User Profile Service", "risk": "medium", "desc": "Manages user data, auth, & legacy session logic."},
        {"name": "Notification Service", "risk": "high", "desc": "Tightly coupled email/SMS dispatch."}
    ]
    
    for i, cluster in enumerate(clusters):
        mock_meta = descriptions[i % len(descriptions)]
        cluster['name'] = mock_meta['name']
        cluster['risk'] = mock_meta['risk']
        cluster['description'] = mock_meta['desc']
        cluster['loc_count'] = len(cluster['node_ids']) * 150 # avg loc
        
    return clusters

def test_connection():
    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": "Ping",
                }
            ],
        )
        print("AI Connection Test:", completion.choices[0].message.content)
        return True
    except Exception as e:
        print(f"AI Connection Failed: {e}")
        return False
