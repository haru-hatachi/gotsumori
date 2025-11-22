from flask import Flask, request, render_template_string, redirect, url_for, session
import os
import shutil
from PIL import Image
from io import BytesIO
import random


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
    <h1>{{ threadname }}</h1>

    {% if messages %}
        <h2>受け取った文章</h2>
        <ul>
        {% for name, text in messages %}
            {% set parts = text.split('_date_') %}
            {% if parts|length == 1 %}
                {% if parts[0][0] == "t" %}
                    <p class="m"><strong>{{ name }}</strong>: {{ parts[0][1:] | safe }}</p>
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
                        <p class="m"><strong>{{ name }}</strong>: {{ parts[0][1:] | safe }}</p>
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
    <p>スレッドを名前を決めて作成できます。作成したスレッドには「スレッド一覧」から参加可能です。</p>
    <button type="button" onclick="location.href='/threads'">スレッド一覧</button>
    <form method="POST">
        <p>スレッド名を入力し、ボタンを押してください。</p>
        <textarea id="threadname" name="threadname" rows="2" cols="19"></textarea>
        <button type="submit">スレッド作成</button>
    </form>



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

threadstemplate = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>ごつ盛りチャット</title>
    <style>
    .m {
        display: block;
        border: 3px solid #00E5A8;
        width: 800px;
        margin: 8px 0;
        padding: 6px;
        word-wrap: break-word;
        white-space: pre-line;
        text-decoration: none;
        color: black;
    }
    .m:hover {
        background-color: #E0FFF5;
    }
    </style>
</head>
<body>
    <h1>チャット一覧</h1>

    {% if threads %}
        <ul style="list-style: none; padding: 0;">
        {% for ID, name in threads %}
            <li><a class="m" href="{{ url_for('index', thread=ID) }}">{{ name }}</a></li>
        {% endfor %}
        </ul>
    {% else %}
        <p>スレッドがまだありません。</p>
    {% endif %}
</body>
</html>
"""




os.makedirs("threads", exist_ok=True)

if not os.path.exists("threadsname.txt"):
    with open("threadsname.txt", "w", encoding="utf-8") as f:
        f.write("main ごつ盛りチャット")


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
    with open("threadsname.txt", "w", encoding="utf-8") as f:
        f.write("main ごつ盛りチャット")

    return redirect(url_for("index", thread="main"))


UPLOAD_FOLDER = "static"  # 保存先フォルダ
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



@app.route("/<thread>", methods=["GET", "POST"])
def index(thread):
    threadname = "ごつ盛りチャット"
    if os.path.exists("threadsname.txt"):
        with open("threadsname.txt", "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(" ", 1)
                if len(parts) == 2:
                    tid, tname = parts
                    if tid == thread:
                        threadname = tname
                        break
    try:
        thread = int(thread)
        thread = str(thread)
    except ValueError:
        if thread != "main" and thread != "clear" and thread != "threads" and thread != "makethread":
            return redirect(url_for("index", thread="main"))

        
    if request.method == "POST":
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        name = request.form.get("name")
        text = request.form.get("text")
        text = text.replace("\r\n", "\n").replace("\n", "<br>")
        file = request.files.get("file")
        threadname = request.form.get("threadname")
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
        
        if threadname:
            threadID=str(random.randint(0,9))
            for i in range(7):
                threadID=threadID+str(random.randint(0,9))
            with open("threadsname.txt", "a", encoding="utf-8") as f:
                f.write(f"\n{threadID} {threadname}")
            return redirect(url_for('index', thread=threadID))
        else:
            return redirect(url_for('index', thread=thread))
        
    if os.path.exists(os.path.join("threads", thread + ".txt")) and os.path.exists(os.path.join("threads", thread + "name.txt")):
        with open(os.path.join("threads", thread + ".txt"), "r", encoding="utf-8") as ft, \
            open(os.path.join("threads", thread + "name.txt"), "r", encoding="utf-8") as fn:

            textlist = ft.read().splitlines()
            namelist = fn.read().splitlines()
    else:
        textlist = []
        namelist = []

    threadID = thread

    with open("threadsname.txt", "r", encoding="utf-8") as f:
        text = f.read()

    if threadID in text:
        messages = list(zip(namelist, textlist))
        return render_template_string(template, messages=messages, thread_name=thread, threadname=threadname)

    else:
        return redirect(url_for('index', thread="main"))




@app.route("/threads")
def show_threads():
    threads = []

    # threadsname.txt を開いて1行ずつ読む
    if os.path.exists("threadsname.txt"):
        with open("threadsname.txt", "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(" ", 1)  # 例: "12345678 雑談スレッド" → ["12345678", "雑談スレッド"]
                if len(parts) == 2:
                    thread_id, thread_name = parts
                    threads.append((thread_id, thread_name))  # リストに追加

    return render_template_string(threadstemplate, threads=threads)





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
