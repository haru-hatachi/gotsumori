from flask import Flask, request, render_template_string, redirect, url_for


app = Flask(__name__)

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
         width: 800px;
         white-space: pre-line;
    }
    </style>
</head>
<body>
    <h1>ごつ盛りチャット</h1>
    <p>文章を入力してください:</p>
    <form method="POST">
        <textarea id="text" name="text" rows="10" cols="94"></textarea>
        <input type="submit" value="送信">
    </form>

    {% if textlist %}
        <h2>受け取った文章</h2>
        <ul>
        {% for text in textlist %}
            <p class="m">{{ text }}</p>
        {% endfor %}
        </ul>
    {% endif %}
</body>
</html>
"""

textlist = []

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        text = request.form.get("text")
        if text:
            textlist.append(text)
        # POST後にリダイレクトしてGETに変換
        return redirect(url_for('index'))
    return render_template_string(template, textlist=textlist)

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000,debug=True)
