from google.cloud import storage
import os
import pandas as pd
from os.path import isfile, join
from os import listdir
from flask import Flask, render_template
import logging
from google.cloud import vision
from google.cloud.vision_v1 import types
from google.cloud import vision_v1 as vision
from google.oauth2.service_account import Credentials

# vision_credentials = Credentials.from_service_account_info(info)
# client = vision.ImageAnnotatorClient(credentials=vision_credentials)

app = Flask(__name__)

client = vision.ImageAnnotatorClient()


def run_quickstart(file_name):
    import io
    import os

    # 구글 라이브러리 import
    from google.cloud import vision
    from google.cloud.vision_v1 import types

    # 사용할 클라이언트 설정
    client = vision.ImageAnnotatorClient()

    # 이미지 읽기
    with io.open(file_name, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)

    # label 뽑아냄.
    response = client.label_detection(image=image)
    labels = response.label_annotations

    result = []

    print('Labels:')
    for label in labels:
        print(label.description + " = " + str(int(label.score*100)) + "%")
        result.append(label.description + " = " +
                      str(int(label.score*100)) + "%\n")

    result = '\n'.join(result)
    return result


# 구글 Cloud Vision API: 제품 검색 입력 데이터 생성(CSV file)

# 이미지 파일이름 -> gcs_url로 변경
product_list = pd.read_csv('./static/csv/product_list.csv')
product_id = list(product_list['product_id'])
snack_product = product_list[product_list['product_category'] == '봉지과자']
cookie_product = product_list[product_list['product_category'] == '상자과자']

file_path = 'C:/Users/HyunjuLee/Documents/blind_store_helper/flask_server/static/images'


def allfiles(path):
    res = []

    for root, dirs, files in os.walk(path):
        rootpath = os.path.join(os.path.abspath(path), root)

        for file in files:
            filepath = os.path.join(rootpath, '.jpg')
            filepath = filepath.rstrip('\\.jpg')
            res.append(filepath)

    return res


file_path = allfiles(file_path)
file_path = list(set(file_path))
files_name = []

for i in file_path:
    temp_name = [f for f in listdir(i) if isfile(join(i, f))]
    files_name += temp_name

print(files_name)
# files_name.remove('product_list.csv')  # 사진경로만 필요하기 때문에, 엑셀 파일 경로 지움
gcs_url = ["gs://blind_store_helper2/"+str(url) for url in files_name]
gcs_url
files_name

# 2. 필수 정보 추가
data = pd.DataFrame()
data['image_url'] = gcs_url
data['item_id'] = 1
for i in range(len(data)):
    name = 'item' + str(i)
    data['item_id'][i] = name
data['project_set_id'] = 'blind_store_helper2'

data['product_id'] = 1
for i in range(len(data['image_url'])):
    temp_url = data['image_url'][i]
    for j in product_id:
        temp_index = temp_url.find(j)
        if temp_index != -1:
            data['product_id'][i] = j

data['product_category'] = 'general-v1'
data['product_display_name'] = 'snack_display'


# 3. 필터 설정(category = snack/cookie)
data['labels'] = 1
for i in range(len(data['product_id'])):
    if data['product_id'][i] in list(snack_product['product_id']):
        data['labels'][i] = "category=snack"
    else:
        data['labels'][i] = "category=cookie"

data['bounding-poly'] = ","  # 경계 박스 none 값 처리할 경우, 쉼표(,) 처리
data.to_csv("item_data.csv", index=False, header=False)
# index와 columns(header) 빼고 추출하기

# ---Google Storage 탐색
# Blob  : 저장할 파일 이름

storage_client = storage.Client()
bucket = storage_client.bucket('blind_store_helper2')
blobs = bucket.list_blobs()
# for blob in blobs:
#     print(blob.name)


def location_path(project_id, location):
    # might as well use an f-string, the new library supports python >=3.6
    return f"projects/{project_id}/locations/{location}"

# 1. CSV 데이터 파일 일괄적으로 불러오기 > PRODUCT SET 및 PRODUCT 동시 생성


def import_product_sets(project_id, location, gcs_uri):
    client = vision.ProductSearchClient()

    # A resource that represents Google Cloud Platform location
    # location_path = client.location_path(project=project_id, location=location)

    # Set the input configuration along with Google Cloud Storage URI
    gcs_source = vision.types.ImportProductSetsGcsSource(csv_file_uri=gcs_uri)
    input_config = vision.types.ImportProductSetsInputConfig(
        gcs_source=gcs_source)

    # Import the product sets from the input URI.
    response = client.import_product_sets(
        parent=location_path(project_id=project_id, location=location), input_config=input_config)

    print('Procseeing operation name : {}', format(response.operation.name))
    # synchronous check of operation status
    result = response.result()
    print('Processing done.')

    for i, status in enumerate(result.statuses):
        # print('Status of processing line {} of the csv: {}', format(i, status))

        # Check the status of reference image
        # '0' is the code for OK in google.rpc.Code.
        if status.code == 0:
            reference_image = result.reference_images[i]
            print(reference_image)
        else:
            print('Status code not OK: {}', format(status.message))


### 제품 및 세트 생성 ###
import_product_sets('analog-primer-297615', 'us-east1',
                    'gs://blind_store_helper2/item_data.csv')

### 제품 등록 확인 ###


def list_product_sets(project_id, location):
    client = vision.ProductSearchClient()

    # A resource that represents Google Cloud Platform location
    # location_path = client.location_path(project=project_id, location=location)

    # List all the product sets available in the region
    product_sets = client.list_product_sets(
        parent=location_path(project_id=project_id, location=location))

    # Display the product set information
    for product_set in product_sets:
        print('Product set name: {}', format(product_set.name))
        print('Product set id: {}', format(product_set.name.split('/')[-1]))
        print('Product set display name: {}', format(product_set.display_name))
        # print('Product set index time:')
        # print(' seconds: {}', format(product_set.index_time.seconds))
        # print(' nanos: {}\n', format(product_set.index_time.nanos))

# [END vision_product_search_list_product_sets]


### 제품 확인 ###
list_product_sets('analog-primer-297615', 'us-east1')

# 2. 유사 제품 이미지 가져오기


# def get_similar_products_file(project_id, location, product_set_id, product_category, file_path, filter):
#     # product_search_client is needed only for its helper methods.
#     product_search_client = vision.ProductSearchClient()
#     image_annotator_client = vision.ImageAnnotatorClient()

#     # Read the image as a stream of bytes
#     with open(file_path, 'rb') as image_file:
#         content = image_file.read()

#     # Create annotate image request along with product search feature.
#     image = vision.types.Image(content=content)

#     # Product search specific parameters
#     product_set_path = product_search_client.product_set_path(
#         project=product_id, location=location, product_set=product_set_id
#     )
#     product_search_params = vision.types.ProductSearchParams(
#         product_set=product_set_path, product_categories=[
#             product_category], filter=filter
#     )
#     image_context = vision.types.ImageContext(
#         product_search_params=product_search_params
#     )

#     # Search products similar to the image.
#     response = image_annotator_client.product_search(
#         image, image_context=image_context
#     )

#     # index_time = response.product_search_results.index_time
#     # print('Product set index time: ')
#     # print(' seconds: {}', format(index_time.seconds))
#     # print(' nanos: {}\n', format(index_time.nanos))

#     results = response.product_search_results.results

#     print('Search results:')

#     score_dict = {}
#     for result in results:
#         product = result.product

#         print('Score(Confidence): {}', format(result.score))
#         print('Image name: {}', format(result.image))

#         print('Product name: {}', format(product.name))
#         print('Product display name: {}', format(product.display_name))
#         print('Product description: {}\n', format(product.description))
#         print('Product labels: {}\n', format(product.product_labels))

#         product_name = product.name
#         product_name = str(product_name)
#         score_dict[product_name] = result.score

#     return score_dict
# # [END vision_product_search_get_similar_products]

def get_similar_products_file(
        project_id, location, product_set_id, product_category,
        file_path, filter):
    """Search similar products to image.
    Args:
        project_id: Id of the project.
        location: A compute region name.
        product_set_id: Id of the product set.
        product_category: Category of the product.
        file_path: Local file path of the image to be searched.
        filter: Condition to be applied on the labels.
        Example for filter: (color = red OR color = blue) AND style = kids
        It will search on all products with the following labels:
        color:red AND style:kids
        color:blue AND style:kids
    """
    # product_search_client is needed only for its helper methods.
    product_search_client = vision.ProductSearchClient()
    image_annotator_client = vision.ImageAnnotatorClient()

    # Read the image as a stream of bytes.
    with open(file_path, 'rb') as image_file:
        content = image_file.read()

    # Create annotate image request along with product search feature.
    image = vision.Image(content=content)

    # product search specific parameters
    product_set_path = product_search_client.product_set_path(
        project=project_id, location=location,
        product_set=product_set_id)
    product_search_params = vision.ProductSearchParams(
        product_set=product_set_path,
        product_categories=[product_category],
        filter=filter)
    image_context = vision.ImageContext(
        product_search_params=product_search_params)

    # Search products similar to the image.
    response = image_annotator_client.product_search(
        image, image_context=image_context)

    index_time = response.product_search_results.index_time
    print('Product set index time: ')
    print(index_time)

    results = response.product_search_results.results

    print('Search results:')

    score_dict = {}

    for result in results:
        product = result.product

        print('Score(Confidence): {}'.format(result.score))
        print('Image name: {}'.format(result.image))

        print('Product name: {}'.format(product.name))
        print('Product display name: {}'.format(
            product.display_name))
        print('Product description: {}\n'.format(product.description))
        print('Product labels: {}\n'.format(product.product_labels))

        product_name = product.name
        product_name = str(product_name)
        score_dict[product_name] = result.score

    return score_dict


result_dict = get_similar_products_file(
    'analog-primer-297615', 'us-east1', 'food', 'general-v1', './static/csv/product_list.csv', '')

######


# image_url = max(result_dict.keys(), key=(lambda k: result_dict[k]))
# print("가장 유사한 이미지 파일 경로: {}", format(image_url))

# model_name = image_url.split("/")[-1]   # 생성되는 image_url 마지막이 모델명으로 담김
# print("가장 유사한 모델: {}", format(model_name))


if __name__ == '__main__':
    logging.error(blobs)
    run_quickstart("whale_bob.jpg")


@ app.route("/result")
def result():
    if __name__ == '__main__':
        run_quickstart("./static/images/whale_bob.jpg")

        image_url = max(result_dict.keys(), key=(lambda k: result_dict[k]))
        print("가장 유사한 이미지 파일 경로: {}", format(image_url))

        model_name = image_url.split("/")[-1]   # 생성되는 image_url 마지막이 모델명으로 담김
        print("가장 유사한 모델: {}", format(model_name))

    return render_template('img_static.html', image_file='images/whale_bob.jpg', result=run_quickstart("./static/images/whale_bob.jpg"))
    # return run_quickstart("whale_bob.jpg")


@ app.route("/")
def home():
    if __name__ == '__main__':
        run_quickstart("./static/images/whale_bob.jpg")

    return run_quickstart("./static/images/whale_bob.jpg")
    # return run_quickstart("whale_bob.jpg")


if __name__ == '__main__':
    # app.run(debug=True, host='192.168.0.8')
    app.debug = True
    app.run(host="0.0.0.0", debug=True)
