from flask import Flask, render_template, request
from main import process_input

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    output_string = None
    if request.method == "POST":
        input_string = request.form["user_input"]
        output_string = process_input(input_string)
    return render_template("index.html", output_string=output_string)

if __name__ == "__main__":
    app.run(debug=True)
