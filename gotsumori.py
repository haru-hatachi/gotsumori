from flask import Flask, request, render_template_string, redirect, url_for, session

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
            <p class="m"><strong>{{ name }}</strong>: {{ text }}</p>
        {% endfor %}
        </ul>
    {% endif %}

    <p>名前を入力してください:</p>
    <form method="POST">
        <textarea id="name" name="name" rows="2" cols="19">{{ session.get('name', '') }}</textarea>
    <p>文章を入力してください:</p>
        <textarea id="text" name="text" rows="10" cols="94"></textarea>
        <input type="submit" value="送信">
    </form>
    <p>名前を入力した後メッセージを送信してください。</p>
    <p>名前を入力しなかった場合、名前は「名無し」になります。</p>
</body>
</html>
"""

textlist = []
namelist = []


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        name = request.form.get("name")
        text = request.form.get("text")
        if name:
            session["name"] = name
        else:
            session["name"] = "名無し"
        if text:
            namelist.append(session["name"])
            textlist.append(text)
        return redirect(url_for('index'))
    
    messages = list(zip(namelist, textlist))
    return render_template_string(template, messages=messages)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
