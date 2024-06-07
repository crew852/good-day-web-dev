from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import re
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 모델과 토크나이저 로드
model = AutoModelForSequenceClassification.from_pretrained("Junbr0/capstone", num_labels=5, ignore_mismatched_sizes=True)
tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base-mlm")

# 데이터베이스 모델 정의
class CodeAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    input_text = db.Column(db.Text, nullable=False)
    output_text = db.Column(db.Text, nullable=False)
    class_probabilities = db.Column(db.Text, nullable=False)

def preprocess_and_tokenize_c_code(code_text, tokenizer):
    code_text = re.sub(r'//.*?\n', '', code_text, flags=re.DOTALL)
    code_text = re.sub(r'/\*.*?\*/', '', code_text, flags=re.MULTILINE)
    code_text = re.sub(r'[\t ]+', " ", code_text, flags=re.DOTALL)
    code_text = re.sub(r'\n\s*\n', " ", code_text, flags=re.MULTILINE)
    code_text = re.sub(r'\n', " ", code_text, flags=re.MULTILINE)
    code_text = re.sub(r'return*.*?;', " ", code_text, flags= re.DOTALL)
    code_text = re.sub(r'return;', " ", code_text, flags=re.DOTALL)
    inputs = tokenizer(code_text, return_tensors="pt", padding=True, truncation=True)
    return inputs

def predict_with_model(input_data, model):
    with torch.no_grad():
        outputs = model(**input_data)
    probabilities = torch.softmax(outputs.logits, dim=1)
    predicted_class = torch.argmax(probabilities, dim=1)
    class_probabilities = probabilities.squeeze().tolist()
    predicted_class_label = {
        0: "안전한 코드입니다.",
        1: "CWE-89 취약점\nSQL Injection",
        2: "CWE-79 취약점\nCross-site Scripting",
        3: "CWE-78 취약점\nOS Command Injection",
        4: "CWE-352 취약점\nCross-Site Request Forgery"
    }
    predicted_class_label_text = predicted_class_label[predicted_class.item()]
    return class_probabilities, predicted_class_label_text

def get_recent_analyses(limit=20):
    return CodeAnalysis.query.order_by(CodeAnalysis.id.desc()).limit(limit).all()

@app.route('/')
def home():
    recent_analyses = get_recent_analyses()
    return render_template('index.html', recent_analyses=recent_analyses)

@app.route('/predict', methods=['POST'])
def predict():
    input_text = request.form['input_text']
    programming_language = request.form['lang']

    if 'fileUpload' in request.files:
        file = request.files['fileUpload']
        if file.filename != '':
            file_path = os.path.join('uploads', file.filename)
            file.save(file_path)
            with open(file_path, 'r') as f:
                input_text = f.read()

    input_data = preprocess_and_tokenize_c_code(input_text, tokenizer)
    class_probabilities, predicted_class_label_text = predict_with_model(input_data, model)

    analysis = CodeAnalysis(
        input_text=input_text,
        output_text=predicted_class_label_text,
        class_probabilities=str(class_probabilities)
    )
    db.session.add(analysis)
    db.session.commit()

    recent_analyses = get_recent_analyses()

    return render_template('index.html', input_text=input_text, output_text=predicted_class_label_text, class_probabilities=class_probabilities, programming_language=programming_language, recent_analyses=recent_analyses)

@app.route('/saved-results')
def saved_results():
    analyses = CodeAnalysis.query.all()
    results = [
        {
            'id': analysis.id,
            'input_text': analysis.input_text,
            'output_text': analysis.output_text,
            'class_probabilities': analysis.class_probabilities
        }
        for analysis in analyses
    ]
    return jsonify(results)

@app.route('/analysis/<int:analysis_id>')
def analysis_detail(analysis_id):
    analysis = CodeAnalysis.query.get(analysis_id)
    if analysis is None:
        return jsonify({"error": "Analysis not found"}), 404
    result = {
        'input_text': analysis.input_text,
        'output_text': analysis.output_text,
        'class_probabilities': analysis.class_probabilities
    }
    return jsonify(result)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)