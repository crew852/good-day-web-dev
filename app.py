import os
import re
import sqlite3
import json
import torch
from flask import Flask, render_template, request, redirect, url_for, session
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from joern_utils import joern_parse, joern_slice, joern_extraction

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 세션 사용을 위한 시크릿 키 설정

# 모델과 토크나이저 로드
model = AutoModelForSequenceClassification.from_pretrained("rlaaudrb1104/models", num_labels=10)
tokenizer = AutoTokenizer.from_pretrained("microsoft/graphcodebert-base")

def preprocess_and_tokenize_c_code(code_text, tokenizer):
    # 주석 제거 및 코드 전처리
    code_text = re.sub(r'//.*?\n', '', code_text, flags=re.DOTALL)
    code_text = re.sub(r'/\*.*?\*/', '', code_text, flags=re.MULTILINE)
    code_text = re.sub(r'#.*?\n', '', code_text, flags=re.DOTALL)
    code_text = re.sub(r'return.*?;', '', code_text, flags=re.DOTALL)
    code_text = re.sub(r'\s+', ' ', code_text)  # 공백 제거

    # 토큰화
    inputs = tokenizer(code_text, return_tensors="pt", padding=True, truncation=True)
    return inputs

def predict_with_model(input_data, model):
    # 모델 예측 수행
    with torch.no_grad():
        outputs = model(**input_data)
    probabilities = torch.softmax(outputs.logits, dim=1)
    predicted_class = torch.argmax(probabilities, dim=1)

    class_probabilities = probabilities.squeeze().tolist()

    # 예측 클래스 레이블
    predicted_class_label = {
        0: "CWE-415 취약점\nDouble Free",
        1: "CWE-119 취약점\nImproper Restriction of Operations within the Bounds of a Memory Buffer",
        2: "CWE-20 취약점\nImproper Input Validation",
        3: "CWE-125 취약점\nOut-of-bounds Read",
        4: "CWE-787 취약점\nOut-of-bounds Write",
        5: "CWE-416 취약점\nUse after Free",
        6: "CWE-476 취약점\nNULL Pointer Dereference",
        7: "CWE-399 취약점\nResource Management Errors",
        8: "CWE-190 취약점\nInteger Overflow or Wraparound"
    }

    predicted_class_label_text = predicted_class_label[predicted_class.item()]
    return class_probabilities, predicted_class_label_text

def insert_history(input_text, output_text, class_probabilities, lang):
    conn = sqlite3.connect('history.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO history (function_name, input_text, output_text, class_probabilities, lang)
        VALUES (?, ?, ?, ?, ?)
    ''', ("function",input_text, output_text, json.dumps(class_probabilities), lang))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect('history.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM history ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

@app.route('/')
def home():
    history = get_history()
    return render_template('index.html', history=history)

@app.route('/joern', methods=['POST'])
def joern():
    input_text = request.form['input_text']
    lang = request.form['lang']

    # 파일 경로 설정
    current_dir = os.getcwd()
    joern_cli_dir = os.path.join(current_dir, 'joern-cli')
    input_dir = os.path.join(joern_cli_dir, 'input')
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)

    code_file = os.path.join(input_dir, 'input_code.c')
    cpg_file = os.path.join(input_dir, 'input_code.bin')
    slice_output_file = os.path.join(input_dir, 'input_code.json')
    extracted_txt_path = os.path.join(input_dir, 'extracted_code.txt')

    # 입력 코드를 파일로 저장
    with open(code_file, 'w') as file:
        file.write(input_text)

    # 파일이 없으면 생성
    open(cpg_file, 'a').close()
    open(slice_output_file, 'a').close()
    open(extracted_txt_path, 'a').close()

    # Joern 파싱 및 슬라이싱
    joern_parse(code_file, cpg_file)
    joern_slice(cpg_file, slice_output_file)

    # Joern JSON 파일에서 코드 라인 추출 및 저장
    joern_extraction(slice_output_file, input_dir, extracted_txt_path)

    # 슬라이싱된 코드 읽기
    if os.path.exists(extracted_txt_path):
        with open(extracted_txt_path, 'r') as file:
            extracted_code = file.read()

        # 슬라이싱된 코드를 세션에 저장
        session['extracted_code'] = extracted_code
        print("code 읽음")
    else:
        session['extracted_code'] = ""
        print("code 못읽음")
    
    session['input_text'] = input_text
    session['lang'] = lang

    return redirect(url_for('predict'))

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'GET':
        if 'extracted_code' in session:
            input_text = session['input_text']
            lang = session['lang']
            extracted_code = session['extracted_code']

            # 슬라이싱된 코드 전처리 및 토큰화
            input_data = preprocess_and_tokenize_c_code(extracted_code, tokenizer)

            # 모델 예측 결과
            class_probabilities, predicted_class_label_text = predict_with_model(input_data, model)

            # 예측 결과를 DB에 저장
            insert_history(input_text, predicted_class_label_text, class_probabilities, lang)
            
            return render_template('index.html',
                input_text=input_text,
                output_text=predicted_class_label_text,
                class_probabilities=class_probabilities,
                lang=lang,
                history=get_history())
        else:
            return redirect(url_for('home'))
    else:
        input_text = request.form['input_text']
        lang = request.form['lang']

        # 입력 데이터 전처리 및 토큰화
        input_data = preprocess_and_tokenize_c_code(input_text, tokenizer)

        # 모델 예측 결과
        class_probabilities, predicted_class_label_text = predict_with_model(input_data, model)

        # 예측 결과를 DB에 저장
        insert_history(input_text, predicted_class_label_text, class_probabilities, lang)
        
        return render_template('index.html',
            input_text=input_text,
            output_text=predicted_class_label_text,
            class_probabilities=class_probabilities,
            lang=lang,
            history=get_history())

@app.route('/history/<int:history_id>')
def history_detail(history_id):
    conn = sqlite3.connect('history.db')
    cursor = conn.cursor()
    cursor.execute('SELECT input_text, output_text, class_probabilities, lang FROM history WHERE id = ?', (history_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        input_text, output_text, class_probabilities, lang = row
        class_probabilities = json.loads(class_probabilities)
        return render_template('index.html',
            input_text=input_text,
            output_text=output_text,
            class_probabilities=class_probabilities,
            lang=lang,
            history=get_history())
    else:
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
