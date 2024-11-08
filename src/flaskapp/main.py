from flask import Flask, render_template, request
import websocket #NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import uuid
import json
import urllib.request
import urllib.parse
#from IPython.display import Image
import random
#from PIL import Image
import io
from io import BytesIO
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def myapp():
    generated_image = None

    server_address = "127.0.0.1:8188"
    client_id = str(uuid.uuid4())

    prompt_text = {}

    if request.method == 'POST':
      def queue_prompt(prompt):
          p = {"prompt": prompt, "client_id": client_id}
          data = json.dumps(p).encode('utf-8')
          req =  urllib.request.Request("http://{}/prompt".format(server_address), data=data)
          return json.loads(urllib.request.urlopen(req).read())

      def get_image(filename, subfolder, folder_type):
          data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
          url_values = urllib.parse.urlencode(data)
          print(url_values)
          #with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
              #return response.read()
          #resp = requests.get(f"http://127.0.0.1:8188/view?{url_values}")
          #image = Image.open(BytesIO(resp.content))
          #image.show()
          if not os.path.exists('./output'):
              os.makedirs('./output')
          urllib.request.urlretrieve(f"http://127.0.0.1:8188/view?{url_values}", f"./output/{filename}.png")
          #Image("./filename.png")

      def get_history(prompt_id):
          with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
              return json.loads(response.read())

      def get_images(ws, prompt):
        prompt_id = queue_prompt(prompt)['prompt_id']
        output_images = {}
        current_node = ""
        while True:
            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['prompt_id'] == prompt_id:
                        if data['node'] is None:
                            break #Execution is done
                        else:
                            current_node = data['node']
            else:
                if current_node == 'save_image_websocket_node':
                    images_output = output_images.get(current_node, [])
                    images_output.append(out[8:])
                    output_images[current_node] = images_output
        data = get_history(prompt_id)
        img_data = data[prompt_id]['outputs']['9']['images'][0]
        filename = img_data['filename']
        subfolder = img_data['subfolder']
        folder_type = img_data['type']
        get_image(filename, subfolder, folder_type)
        #print(data, prompt_id)
        #image = Image.open(io.BytesIO(images[node_id]))
        #image.show()
        return output_images
      
      
      
      with open('prompt_text.json',) as f:
        prompt_text = json.load(f)
      
      prompt_text_str = json.dumps(prompt_text)
      prompt = json.loads(prompt_text_str)
      #set the text prompt for our positive CLIPTextEncode
      prompt["6"]["inputs"]["text"] = "Photo of stunning woman, spiral curls, long auburn hair, some freckles, beautiful low cut blouse, long skirt, sitting on a chair in a dark room, amazing smile, perfect eyes . High dynamic range, vivid, rich details, clear shadows and highlights, realistic, intense, enhanced contrast, highly detailed"

      #set the seed for our KSampler node
      prompt["3"]["inputs"]["seed"] = random.randint(1, 100000000)

      ws = websocket.WebSocket()
      ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
      get_images(ws, prompt)
      #ws.close() # for in case this example is used in an environment where it will be repeatedly called, like in a Gradio app. otherwise, you'll randomly receive connection timeouts
      #Commented out code to display the output images:
      #image = Image.open(io.BytesIO(images[node_id]))
      #image.show()


    return render_template('index.html', generated_image=generated_image)


if __name__ == '__main__':
    app.run(debug=True, port=9000)