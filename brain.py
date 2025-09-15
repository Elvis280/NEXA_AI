import os
from groq import Groq
import datetime as t
from twilio.rest import Client
import json
import database_ops
import api_secrets

client = Groq(api_key=api_secrets.GROQ_API_KEY)
conversation = [{"role": "system",
                    "content": """You are a command classifier.
Your Job is to only return a JSON with format:
{
    "action": "open_website | play_music | post_social | send_message | chat | todo_list-insertion | todo_list-deletion | todo_list-display",
    "params": { 
        "url": "...", 
        "song": "...", 
        "platform": "linkedin | twitter", 
        "post": "...", 
        "recipient": "...", 
        "message": "...",
        "task": "..." 
    },
    "prompt": "a ready-to-use instructional prompt that can be directly sent to GPT-5 or Gemini.",
    "ans": "answer to the user  current query in short"
}

Rules:
   - If user says "open <site>", → action = open_website
   - If user says "play music" or "play video", → action = play_music
   - If user says "post on linkedin" or "post on twitter", → action = post_social
   - If user says "send whatsapp message" or "send message", → action = send_message
   - If user says "add <task>" or "insert <task>" → action = todo_list-insertion
   - If user says "delete <task>" or "remove <task>" → action = todo_list-deletion
   - If user says "show tasks" or "display tasks" → action = todo_list-display
   - Otherwise, → action = chat

    """
    }]

def open_website(web_url:str):
    pass

def play_music(title_of_vid):
    kit.playonyt(title_of_vid)

def post_social():
    pass
def send_message( params):
    account_sid = 'AC8a9a27b995de81b60a6375576aa3222d'
    auth_token = '70d5eb9d965da82ac35e05955a5cbd2b'
    client = Client(account_sid, auth_token)

    message = client.messages.create(
    from_='whatsapp:+14155238886',
    body=params['message'],
    to='whatsapp:+918081874158'
    )

    print(message.sid)


def todo_list(action, parm=" "):
    parm = parm.lower().strip()
    
    if action == 'todo_list-insertion':
        return database_ops.insert_into_list(parm)
    
    elif action == 'todo_list-deletion':
        # Check if user wants to delete by position
        import re
        pos_match = re.search(r"(\d+)(?:st|nd|rd|th)? task", parm)
        reverse_match = re.search(r"(\d+)(?:st|nd|rd|th)? last task", parm)
        
        if pos_match:
            pos = int(pos_match.group(1))
            return database_ops.delete_task_by_position(pos)
        elif reverse_match:
            pos = int(reverse_match.group(1))
            return database_ops.delete_task_by_reverse_position(pos)
        elif "last" in parm:
            return database_ops.delete_task_by_reverse_position(1)

        else:
            # Default: delete by exact task name
            return database_ops.delete_from_list_by_name(parm)
    
    elif action == 'todo_list-display':
        return database_ops.display_list()
    
    else:
        return ""


def process_query(user_query):
    global conversation

    try:
        # Add user query to conversation
        conversation.append({"role": "user", "content": user_query})

        # Get AI response
        chat = client.chat.completions.create(
            messages=conversation,
            model="openai/gpt-oss-120b"
        )

        response = chat.choices[0].message.content
        
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            # If JSON parsing fails, return a default chat response
            return {
                "action": "chat",
                "ans": response,
                "status": "success"
            }

        # Process the action
        result = {"action": data.get("action", "chat"), "status": "success"}
        
        if data['action'] == "play_music":
            try:
                play_music(data['params']['song'])
                result["ans"] = data['ans']
                result["action_taken"] = f"Playing music: {data['params']['song']}"
                result["note"] = "Task SUCCESSFUL"
            except Exception as e:
                result["ans"] = f"Sorry, I couldn't play the music. Error: {str(e)}"
                
        elif data['action'] == "send_message":
            try:

                send_message(data['params'])

                result["ans"] = data['ans']
                result["action_taken"] = f"Sent WhatsApp message: {data['params']['message']}"
                result["note"] = "Task SUCCESSFUL"
            except Exception as e:
                result["ans"] = f"Sorry, I couldn't send the message. Error: {str(e)}"
                
        elif data['action'] == "open_website":
            result["ans"] = data['ans']
            result["action_taken"] = f"Would open website: {data['params'].get('url', 'N/A')}"
            result["note"] = "Website opening not implemented yet"
            
        elif data['action'] == "post_social":
            result["ans"] = data['ans']
            result["action_taken"] = f"Would post on {data['params'].get('platform', 'social media')}"
            result["note"] = "Social media posting not implemented yet"
            

        elif data['action'] in ["todo_list-display", "todo_list-insertion", "todo_list-deletion"]:
            action_result = todo_list(data['action'], data['params'].get('task', ''))
            result["ans"] = action_result or data.get('ans', "Todo list updated.")
            result["action_taken"] = "Todo list management"
            result["note"] = "Task SUCCESSFUL"

            
        else:  # chat action
            result["ans"] = data.get('ans', response)
            result["action_taken"] = "General conversation"
            result["note"] = "Task SUCCESSFUL"
        
        print(data)
        print(result)
        database_ops.save_chat_conversation(user_query,result['ans'],data['action'],result["action_taken"],result['note'])
        return result

    except Exception as e:
        return {
            "action": "error",
            "ans": f"Sorry, I encountered an error processing your request: {str(e)}",
            "status": "error"
        }

if __name__=='__main__':
    while True:
        msg=input("User : ")
        print(process_query(msg))
