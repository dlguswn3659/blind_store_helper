from flask import Flask, render_template
app = Flask(__name__)


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


if __name__ == '__main__':
    run_quickstart("whale_bob.jpg")


@app.route("/result")
def result():
    if __name__ == '__main__':
        run_quickstart("./static/images/whale_bob.jpg")

    return render_template('img_static.html', image_file='images/whale_bob.jpg', result=run_quickstart("./static/images/whale_bob.jpg"))
    # return run_quickstart("whale_bob.jpg")


@app.route("/")
def home():
    if __name__ == '__main__':
        run_quickstart("./static/images/whale_bob.jpg")

    return run_quickstart("./static/images/whale_bob.jpg")
    # return run_quickstart("whale_bob.jpg")


if __name__ == '__main__':
    # app.run(debug=True, host='192.168.0.8')
    app.debug = True
    app.run(host="0.0.0.0", debug=True)
