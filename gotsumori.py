from flask import Flask, request, render_template_string, redirect, url_for


app = Flask(__name__)

# HTMLテンプレート
template = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>仮掲示板</title>
</head>
<body>
    <h1>仮掲示板</h1>
    <p>文章を入力してください:</p>
    <form method="POST">
        <input type="text" id="text" name="text">
        <input type="submit" value="送信">
    </form>

    {% if textlist %}
        <h2>受け取った文章</h2>
        <ul>
        {% for text in textlist %}
            <li>{{ text }}</li>
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
