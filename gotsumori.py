from flask import Flask, request, render_template_string, redirect, url_for, session
import os
import shutil
from PIL import Image
from io import BytesIO


app = Flask(__name__)
app.secret_key = "秘密のキー"

# HTMLテンプレート
template = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>ごつ盛りチャット</title>
    <style>
    .m{
        border: 3px solid #00E5A8;
        width: 800px;
        word-wrap: break-word;
        white-space: pre-line;
    }
    </style>
</head>
<body>
    <h1>ごつ盛りチャット</h1>

    {% if messages %}
        <h2>受け取った文章</h2>
        <ul>
        {% for name, text in messages %}
            {% if text[0] == "t" %}
                <p class="m"><strong>{{ name }}</strong>: {{ text[1:] }}</p>
            {% elif text[0] == "i" %}
                <p class="m"><strong>{{ name }}</strong>:
                    <img src="{{ url_for('static', filename=text[1:]) }}" width="400">
                </p>
            {% elif text[0] == "f" %}
                <p class="m"><strong>{{ name }}</strong>:
                    <a href="{{ url_for('static', filename=text[1:]) }}" download>{{ text[1:] }} をダウンロード</a>
                </p>
            {% endif %}
        {% endfor %}
        </ul>
    {% endif %}

    <p>名前を入力してください:</p>
    <form method="POST" enctype="multipart/form-data">
        <textarea id="name" name="name" rows="2" cols="19">{{ session.get('name', '') }}</textarea>
    <p>文章を入力してください:</p>
        <textarea id="text" name="text" rows="10" cols="94"></textarea>
    <p>ファイルを選択してください
        <input type="file" name="file">
        <button type="submit">送信</button>
    </form>
    <p>名前を入力し決定を押した後メッセージを送信してください。</p>
    <p>名前を入力しなかった場合、名前は「名無し」になります。</p>


</body>
</html>
"""

textlist = []
namelist = []
UPLOAD_FOLDER = "static"  # 保存先フォルダ
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        name = request.form.get("name")
        text = request.form.get("text")
        file = request.files.get("file")
        if name:
            session["name"] = name
        else:
            session["name"] = "名無し"
        if text:
            namelist.append(session["name"])
            textlist.append("t"+text)
        if file and file.filename != "":
            if name:
                session["name"] = name
            else:
                session["name"] = "名無し"
            data = file.read()
            file.seek(0)

            # Pillowを使って画像かどうか判定
            try:
                Image.open(BytesIO(data))
                is_image = True
            except:
                is_image = False

            if is_image:
                textlist.append("i" + file.filename)
            else:
                textlist.append("f" + file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            namelist.append(session["name"])
            
        return redirect(url_for('index'))
    
    messages = list(zip(namelist, textlist))
    return render_template_string(template, messages=messages)

@app.route('/clear')
def clear():
    global textlist, namelist
    textlist = []
    namelist = []
    # フォルダを削除（中身も含めて全部）
    if os.path.exists("static"):
        shutil.rmtree("static")
    # 再作成
    os.makedirs("static", exist_ok=True)
    return redirect(url_for('index'))


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))  # Renderが指定するポートを取得
    app.run(host="0.0.0.0", port=port)