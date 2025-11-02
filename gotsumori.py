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
        white-space: normal;
    }
    </style>
</head>
<body>
    <h1>ごつ盛りチャット</h1>

    {% if messages %}
        <h2>受け取った文章</h2>
        <ul>
        {% for name, text in messages %}
            {% set parts = text.split('_date_') %}
            {% if parts|length == 1 %}
                {% if parts[0][0] == "t" %}
                    <p class="m"><strong>{{ name }}</strong>: {{ parts[0][1:] }}</p>
                {% elif parts[0][0] == "i" %}
                    <p class="m"><strong>{{ name }}</strong>:
                        <img src="{{ url_for('static', filename=parts[0][1:]) }}" width="400">
                    </p>
                {% elif parts[0][0] == "f" %}
                    <p class="m"><strong>{{ name }}</strong>:
                        <a href="{{ url_for('static', filename=parts[0][1:]) }}" download>{{ parts[0][1:] }} をダウンロード</a>
                    </p>
                {% endif %}
            {% elif parts|length == 2 %}
                {% set main = parts[0] %}
                {% set attach = parts[1] %}
                <div class="m">
                    {% if main[0] == "t" %}
                        <p><strong>{{ name }}</strong>: {{ main[1:] }}</p>
                    {% endif %}
                    {% if attach[0] == "i" %}
                        <img src="{{ url_for('static', filename=attach[1:]) }}" width="400">
                    {% elif attach[0] == "f" %}
                        <a href="{{ url_for('static', filename=attach[1:]) }}" download>{{ attach[1:] }} をダウンロード</a>
                    {% endif %}
                </div>
            {% endif %}
        {% endfor %}
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
    <p>URLの「gotsumori.com/main」の「main」の部分を任意の英数字にすることで、同じURLどうしでだけチャットが出来ます。</p>


</body>
<script>
let oldCount = {{ messages|length }};  // ← ここを変更！
const thread = "{{ thread_name }}";

async function checkUpdate() {
    const response = await fetch(`/check_update/${thread}`);
    const data = await response.json();

    if (data.count > oldCount) {
        location.reload();
    }
    oldCount = data.count;
}

setInterval(checkUpdate, 3000);
if (window.history.replaceState) {
    window.history.replaceState(null, null, window.location.href);
}

</script>
</html>
"""
os.makedirs("threads", exist_ok=True)

@app.route("/")
def root_redirect():
    return redirect(url_for("index", thread="main"))

@app.route('/clear')
def clear():
    global textlist, namelist
    textlist = []
    namelist = []
    # フォルダを削除（中身も含めて全部）
    if os.path.exists("static"):
        shutil.rmtree("static")
    if os.path.exists("threads"):
        shutil.rmtree("threads")

    # 再作成
    os.makedirs("static", exist_ok=True)
    os.makedirs("threads", exist_ok=True)
    return redirect(url_for("index", thread="main"))

UPLOAD_FOLDER = "static"  # 保存先フォルダ
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/<thread>", methods=["GET", "POST"])
def index(thread):


    if any('！' <= ch <= '～' or '\u3000' <= ch <= '\uff9f' for ch in thread):
        if thread != "main":
            return redirect(url_for("index", thread="main"))

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
            if os.path.exists(os.path.join("threads", thread + ".txt")):
                with open(os.path.join("threads", thread + ".txt"), "a", encoding="utf-8") as f:
                    f.write("\n"+"t"+text)
                with open(os.path.join("threads", thread + "name" + ".txt"), "a", encoding="utf-8") as f:
                    f.write("\n"+session["name"])
            else:
                with open(os.path.join("threads", thread + ".txt"), "w", encoding="utf-8") as f:
                    f.write("t"+text)
                with open(os.path.join("threads", thread + "name" + ".txt"), "w", encoding="utf-8") as f:
                    f.write(session["name"])

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
                if text:
                    if os.path.exists(os.path.join("threads", thread + ".txt")):
                        with open(os.path.join("threads", thread + ".txt"), "a", encoding="utf-8") as f:
                            f.write("_date_"+"i"+file.filename)
                    else:
                        with open(os.path.join("threads", thread + ".txt"), "w", encoding="utf-8") as f:
                            f.write("_date_"+"i"+file.filename)
                else:
                    if os.path.exists(os.path.join("threads", thread + ".txt")):
                        with open(os.path.join("threads", thread + ".txt"), "a", encoding="utf-8") as f:
                            f.write("\n"+"i"+file.filename)
                    else:
                        with open(os.path.join("threads", thread + ".txt"), "w", encoding="utf-8") as f:
                            f.write("i"+file.filename)
            else:
                if text:
                    if os.path.exists(os.path.join("threads", thread + ".txt")):
                        with open(os.path.join("threads", thread + ".txt"), "a", encoding="utf-8") as f:
                            f.write("_date_"+"f"+file.filename)
                    else:
                        with open(os.path.join("threads", thread + ".txt"), "w", encoding="utf-8") as f:
                            f.write("_date_"+"f"+file.filename)
                else:
                    if os.path.exists(os.path.join("threads", thread + ".txt")):
                        with open(os.path.join("threads", thread + ".txt"), "a", encoding="utf-8") as f:
                            f.write("\n"+"f"+file.filename)
                    else:
                        with open(os.path.join("threads", thread + ".txt"), "w", encoding="utf-8") as f:
                            f.write("f"+file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            if os.path.exists(os.path.join("threads", thread + "name.txt")):
                with open(os.path.join("threads", thread + "name" + ".txt"), "a", encoding="utf-8") as f:
                    f.write("\n"+session["name"])
            else:
                with open(os.path.join("threads", thread + "name" + ".txt"), "w", encoding="utf-8") as f:
                    f.write(session["name"])
            
            return redirect(url_for('index', thread=thread))
        
    if os.path.exists(os.path.join("threads", thread + ".txt")) and os.path.exists(os.path.join("threads", thread + "name.txt")):
        with open(os.path.join("threads", thread + ".txt"), "r", encoding="utf-8") as ft, \
            open(os.path.join("threads", thread + "name.txt"), "r", encoding="utf-8") as fn:

            textlist = ft.read().splitlines()
            namelist = fn.read().splitlines()
    else:
        textlist = []
        namelist = []

    messages = list(zip(namelist, textlist))
    return render_template_string(template, messages=messages, thread_name=thread)



@app.route("/check_update/<thread>")
def check_update(thread):
    import os

    filename = os.path.join("threads", thread + ".txt")
    if not os.path.exists(filename):
        return {"count": 0}

    with open(filename, "r", encoding="utf-8") as f:
        count = len(f.read().splitlines())
    return {"count": count}



if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))  # Renderが指定するポートを取得
    app.run(host="0.0.0.0", port=port, debug=True)
