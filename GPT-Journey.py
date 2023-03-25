# For the UI
from flask import Flask, render_template, request, session
# OpenAI API
import openai
# Regular expressions:
import re
import requests
import json
from PIL import Image
import io
import base64

# Set the OpenAI API key
openai.api_key = open("key.txt", "r").read().strip("\n")
preprompt = open("preprompt.txt", "r").read().strip("\n")


url = "http://127.0.0.1:7860/sdapi/v1/txt2img"

# Create a new Flask app and set the secret key
app = Flask(__name__)
app.secret_key = "mysecretkey"

# Define a function to generate an image using the OpenAI API
def get_img(prompt):
    img_url = None
    try:
        payload = json.dumps({
        "prompt": prompt,
        "steps": 12
        })
        headers = {
        'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        r = response.json()
        #print(r)
        image_64 = r["images"][0]
        #for i in r['images']:
        #image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))
        #img_url = Image.open(io.BytesIO(base64.b64decode(image_64)))
        img_url = image_64
        
    except Exception as e:
        # if it fails (e.g. if the API detects an unsafe image), use a default image
        img_url = "https://pythonprogramming.net/static/images/imgfailure.png"
        print(e)
        
    return img_url




# Define a function to generate a chat response using the OpenAI API
def chat(inp, message_history, role="user"):

    # Append the input message to the message history
    message_history.append({"role": role, "content": f"{inp}"})

    # Generate a chat response using the OpenAI API
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=message_history
    )

    # Grab just the text from the API completion response
    reply_content = completion.choices[0].message.content

    # Append the generated response to the message history
    message_history.append({"role": "assistant", "content": f"{reply_content}"})

    # Return the generated response and the updated message history
    return reply_content, message_history


# Define the homepage route for the Flask app
@app.route('/', methods=['GET', 'POST'])
def home():
    # Page's title:
    title = "GPT-Journey"
    
    # Initialize the button messages and button states dictionaries
    button_messages = {}
    button_states = {}

    # If the request method is GET (i.e., the page has just been loaded), set up the initial chat
    if request.method == 'GET':

        # Initialize the message history
        session['message_history'] = [{"role": "user", "content": preprompt},
                                      {"role": "assistant", "content": f"""OK, I understand. Begin when you're ready."""}]
        
        # Retrieve the message history from the session
        message_history = session['message_history']

        # Generate a chat response with an initial message ("Begin")
        reply_content, message_history = chat("Begin", message_history)
        
        # get the text before the scene description
        pretext = reply_content.split("]=-")[0]
        
        # Extract the text from the response
        #text = reply_content.split("Option 1")[0]
    
        try:
            # Extract the text from the response
            text = reply_content.split("Option 1")[0]
            # Extract text from between ]=- and Option 1
            scenetext = reply_content.split("]=-")[1].split("Option 1")[0]
        except IndexError:
            print("Error: 'Option 1' or ']=-'' not found in reply_content")
            # Handle the error here (e.g. assign default values to text and scenetext)




        # Using regex, grab the natural language options from the response
        options = re.findall(r"Option \d:.*", reply_content)

        # Create a dictionary of button messages
        for i, option in enumerate(options):
            button_messages[f"button{i+1}"] = option

        # Initialize the button states
        for button_name in button_messages.keys():
            button_states[button_name] = False


    # If the request method is POST (i.e., a button has been clicked), update the chat
    message = None
    button_name = None
    if request.method == 'POST':

        # Retrieve the message history and button messages from the session
        message_history = session['message_history']
        button_messages = session['button_messages']

        # Get the name of the button that was clicked  ***
        button_name = request.form.get('button_name')

        # Set the state of the button to "True"
        button_states[button_name] = True

        # Get the message associated with the clicked button
        message = button_messages.get(button_name)

        # Generate a chat response with the clicked message
        reply_content, message_history = chat(message, message_history)
        print(reply_content)
        
        # Extract the text and options from the response
        text = reply_content.split("Option 1")[0]
        options = re.findall(r"Option \d:.*", reply_content)

        # Extract the alttext and options from the response
        #alttext = reply_content.split("Alt Img Text")[0]
        #altoptions = re.findall(r"Alt Img Text \d:.*", reply_content)
        #print (altoptions)
        
        # Update the button messages and states
        button_messages = {}
        for i, option in enumerate(options):
            button_messages[f"button{i+1}"] = option
        for button_name in button_messages.keys():
            button_states[button_name] = False

    # Store the updated message history and button messages in the session
    session['message_history'] = message_history
    session['button_messages'] = button_messages

    # Generate an image based on the chat response text   
    
    #img_url = get_img(text)
    img_url = get_img(scenetext)
    #print(img_url)
    #image_url = image_url["images"][0]
    #print(image_url)
    
    # Render the template with the updated information
    return render_template('home.html', title=title, text=text, image_url=img_url, button_messages=button_messages, button_states=button_states, message=message)

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, port=5001)
