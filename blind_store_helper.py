# def run_quickstart(file_name):
#     import io
#     import os

#     # 구글 라이브러리 import
#     from google.cloud import vision
#     from google.cloud.vision import types

#     # 사용할 클라이언트 설정
#     client = vision.ImageAnnotatorClient()

#     # 이미지 읽기
#     with io.open(file_name, 'rb') as image_file:
#         content = image_file.read()

#     image = types.Image(content=content)

#     # label 뽑아냄.
#     response = client.label_detection(image=image)
#     labels = response.label_annotations

#     print('Labels:')
#     for label in labels:
#         print(label.description + " = " + str(int(label.score*100)) + "%")


# if __name__ == '__main__':
#     run_quickstart("whale_bob.jpg")


import io
import os

# Imports the Google Cloud client library
from google.cloud import vision

# Instantiates a client
client = vision.ImageAnnotatorClient()

# The name of the image file to annotate
file_name = os.path.abspath('whale_bob.jpg')

# Loads the image into memory
with io.open(file_name, 'rb') as image_file:
    content = image_file.read()

image = vision.Image(content=content)

# Performs label detection on the image file
response = client.label_detection(image=image)
labels = response.label_annotations

print('Labels:')
for label in labels:
    print(label.description)
