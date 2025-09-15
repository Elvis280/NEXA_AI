from flask import Flask, request, render_template, jsonify
import brain as b
import database_ops
from datetime import datetime

app = Flask(__name__)

# Home page
@app.route('/', methods=['GET','POST'])
def home():
    if request.method == 'POST':
        try:
            query = request.form.get('query')
            
            if not query:
                return render_template('home.html')
            
            # Process the query using the brain module
            result = b.process_query(query)
            
            # Prepare result data for template
            result_data = {
                'status': 'success',
                'message': result.get('ans', 'Task completed successfully'),
                'action': result.get('action', 'unknown'),
                'action_taken': result.get('action_taken', ''),
                'note': result.get('note', ''),
                'query': query,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return render_template('home.html', result=result_data)
            
        except Exception as e:
            return render_template('home.html')
    
    return render_template('home.html')

# Features page
@app.route('/features')
def features():
    return render_template('features.html')

# Contact page
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Handle contact form submission
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Here you would typically save the message to a database
        # For now, we'll just redirect back to contact page
        return render_template('contact.html')
    
    return render_template('contact.html')

# Chat history page
@app.route('/history')
def history():
    try:
        # Get chat history from database
        chat_history = database_ops.get_chat_history(limit=50)
        chat_stats = database_ops.get_chat_stats()
        
        # Format the data for the template
        conversations = []
        for chat in chat_history:
            conversations.append({
                'id': chat[0],
                'query': chat[1],
                'response': chat[2],  # This is nexa_response from the database
                'action_type': chat[3] or 'chat',
                'action_taken': chat[4] or ' ',
                'note': chat[5] or ' ',
                'timestamp': chat[6].strftime('%Y-%m-%d %H:%M') if chat[6] else ''
            })
        
        return render_template('history.html', 
                             conversations=conversations, 
                             stats=chat_stats)
    except Exception as e:
        print(f"Error loading chat history: {e}")
        return render_template('history.html', 
                             conversations=[], 
                             stats={"total": 0, "today": 0, "this_week": 0, "this_month": 0})

# Delete chat conversation
@app.route('/delete_chat/<int:chat_id>', methods=['POST'])
def delete_chat(chat_id):
    try:
        success = database_ops.delete_chat_conversation(chat_id)
        if success:
            return jsonify({'status': 'success', 'message': 'Chat deleted successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to delete chat'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
