import time
import sys
from config import Config
from core.agent import PersonalAgent

def main():
    print(f"Starting {Config.AGENT_NAME}...")
    Config.validate()
    
    agent = PersonalAgent()
    
    print("Agent is running. Press Ctrl+C to stop.")
    
    # Mock loop for demonstration since we don't have real Plato webhooks
    try:
        while True:
            # In a real app, this would poll the API or run a flask server
            # messages = agent.plato.get_updates()
            # for msg in messages:
            #     agent.process_message(msg)
            
            # For demo purposes, we can manually trigger a test message if in DEBUG mode
            # and it's the first run
            if Config.DEBUG and len(sys.argv) > 1 and sys.argv[1] == "test":
                 print("Running test message...")
                 test_msg = {"chat_id": "test_user", "text": "Hello, who are you?"}
                 agent.process_message(test_msg)
                 break
                 
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Agent...")

if __name__ == "__main__":
    main()
