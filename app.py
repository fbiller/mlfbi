import os
import urllib.request
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename 

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

SUBSCRIPTION_KEY  = 'fSZI8h0BhzbYah62zRUiv2gY2ocTdp5zIcxdmyTdTxeHCiQ8gkc7hHcm9E5VrlKtACcRSGzj4bIp+AStj5RJzg=='
END_POINT = 'DefaultEndpointsProtocol=https;AccountName=storemb6plg2txuwi6;AccountKey=fSZI8h0BhzbYah62zRUiv2gY2ocTdp5zIcxdmyTdTxeHCiQ8gkc7hHcm9E5VrlKtACcRSGzj4bIp+AStj5RJzg==;EndpointSuffix=core.windows.net'
COG_KEY = '58fa0475d6e844a5898652f20ddcedf0'
COG_KEYENDPOINT = 'https://service-cv.cognitiveservices.azure.com/'

import requests
from array import array
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use('Agg')

from PIL import Image, ImageDraw
import time

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes

computervision_client = ComputerVisionClient(COG_KEYENDPOINT, CognitiveServicesCredentials(COG_KEY))
features = ['Description', 'Tags', 'Adult', 'Objects', 'Faces']

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads/'

# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024




app = Flask(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyse_images (filenames):
    print ("analyse_image filenames",filenames," element0 ",filenames[0])
    for image_path in filenames:
        path_image = os.path.join(UPLOAD_FOLDER,image_path)
        print ("path image",path_image," image_path",image_path)
        image_stream = open (path_image,"rb")
        analysis = computervision_client.analyze_image_in_stream(image_stream, visual_features=features)
    return analysis, path_image

def analyse_image (filename):
    print ("analyse_image filenames",filename)
    path_image = os.path.join(UPLOAD_FOLDER,filename)
    print ("path image",path_image)
    image_stream = open (path_image,"rb")
    analysis = computervision_client.analyze_image_in_stream(image_stream, visual_features=features)
    return analysis, path_image

def build_image(image_path, analysis):

    print ("build_image image path ",image_path)
    fig = plt.figure(figsize=(16, 8))
    a = fig.add_subplot(1,2,1)
    img = Image.open(image_path)
    
    # Get the caption
    caption_text = ''
    if (len(analysis.description.captions) == 0):
        caption_text = 'No caption detected'
    else:
        for caption in analysis.description.captions:
            caption_text = caption_text + " '{}'\n(Confidence: {:.2f}%)".format(caption.text, caption.confidence * 100)
    plt.title(caption_text)

    # Get objects
    if analysis.objects:
        # Draw a rectangle around each object
        for object in analysis.objects:
            r = object.rectangle
            bounding_box = ((r.x, r.y), (r.x + r.w, r.y + r.h))
            draw = ImageDraw.Draw(img)
            draw.rectangle(bounding_box, outline='magenta', width=5)
            plt.annotate(object.object_property,(r.x, r.y), backgroundcolor='magenta')

    # Get faces

    if analysis.faces:
        # Draw a rectangle around each face
        for face in analysis.faces:
            r = face.face_rectangle
            bounding_box = ((r.left, r.top), (r.left + r.width, r.top + r.height))
            draw = ImageDraw.Draw(img)
            draw.rectangle(bounding_box, outline='lightgreen', width=5)
            annotation = 'Person aged approxilately {}'.format(face.age)
            plt.annotate(annotation,(r.left, r.top), backgroundcolor='lightgreen')

    # Add a second plot for addition details
    plt.axis("off")
    plt.imshow(img)
    a = fig.add_subplot(1,2,2)

    # Get ratings
    ratings = 'Ratings:\n - Adult: {}\n - Racy: {}\n - Gore: {}'.format(analysis.adult.is_adult_content,
                                                                           analysis.adult.is_racy_content,
                                                                           analysis.adult.is_gory_content,)

    # Get tags
    # This code returns a tag (key word) for each thing in the image.
    
    tags = 'Tags:'
    if (len(analysis.tags) == 0):
        print("No tags detected.")
    for tag in analysis.tags:
        tags = tags + '\n - {} with confidence {:.2f}%'.format(tag.name, tag.confidence * 100)

    # Print details

    details = '{}\n\n{}'.format(ratings, tags)
    a.text(0,0.4, details, fontsize=12)

    plt.axis('off')
    name_file_ia = image_path.split(".")[0] + "_ia."+image_path.split(".")[-1]
    plt.savefig(name_file_ia)	

def image_ia(filename):
    print('display_image filename: ' + filename)
    analysis, path_image =analyse_image (filename)
    print('analysis', type(analysis))
    build_image (path_image,analysis)
    print('display path image: ', path_image)
    name_file_ia = (path_image.split('.')[0] + '_ia.' + path_image.split('.')[-1])
    print('name_file_ia ',name_file_ia)
    return (name_file_ia)

    
@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/', methods=['POST'])
def upload_image():
    print ()
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No image selected for uploading')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        print('upload_image filename: ' + filename)
        flash('Image successfully uploaded and displayed below')
        filename_ia = image_ia (filename)
        return render_template('upload.html', filename="static/uploads/"+filename, filename_ia=filename_ia)
    else:
        flash('Allowed image types are -> png, jpg, jpeg, gif')
        return redirect(request.url)


if __name__ == "__main__":
    app.secret_key = "secret key"
    app.run(debug=True)