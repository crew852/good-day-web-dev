from flask import Flask, render_template, request
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import re

app = Flask(__name__)

# 모델과 토크나이저 로드
model = AutoModelForSequenceClassification.from_pretrained("rlaaudrb1104/models", num_labels=10)
tokenizer = AutoTokenizer.from_pretrained("microsoft/graphcodebert-base")

def preprocess_and_tokenize_c_code(code_text, tokenizer):
    # 주석 제거
    code_text = re.sub(r'//.*?\n', '', code_text, flags=re.DOTALL)
    code_text = re.sub(r'/\*.*?\*/', '', code_text, flags=re.MULTILINE)
    code_text = re.sub(r'^#define\s+<.*?>\s*\n', '', code_text, flags=re.MULTILINE)
    code_text = re.sub(r'#include .*?\n', '', code_text, flags=re.DOTALL)
    code_text = re.sub(r'#include "*.*?\n', '', code_text, flags=re.DOTALL)
    code_text = re.sub(r'#define .*?\n', '', code_text, flags=re.DOTALL)
    code_text = re.sub(r'#undef\s+\w+', '', code_text, flags=re.DOTALL)
    code_text = re.sub(r'#if\s+\w+', '', code_text, flags=re.DOTALL)
    code_text = re.sub(r'#else\s+\w+', '', code_text, flags=re.DOTALL)
    code_text = re.sub(r'#elif\s+\w+', '', code_text, flags=re.DOTALL)
    code_text = re.sub(r'#endif', '', code_text, flags=re.DOTALL)
    code_text = re.sub(r'[\t ]+', '', code_text, flags=re.DOTALL)
    code_text = re.sub(r'\n\s*\n', '', code_text, flags=re.DOTALL)
    code_text = re.sub(r'\n', '', code_text, flags=re.DOTALL)
    code_text = re.sub(r'return*.*?;', '', code_text, flags=re.DOTALL)
    code_text = re.sub(r'return;', '', code_text, flags=re.DOTALL)
    code_text = re.sub(r'\b([a-zA-Z_]\w*)\s+([a-zA-Z_]\w*)\s*\(([^)]*)\)\s*{', r"void func(\3){", code_text, flags=re.DOTALL)

    # 코드 내의 공백 및 줄 바꿈 제거
    code_text = re.sub(r'\s+', ' ', code_text)
    # 토큰화
    inputs = tokenizer(code_text, return_tensors="pt", padding=True, truncation=True)

    return inputs

def predict_with_model(input_data, model):
    # 입력 데이터를 모델에 전달하여 예측 수행
    with torch.no_grad():
        outputs = model(**input_data)

    # 로짓 값을 소프트맥스 함수를 통과하여 확률값으로 변환
    probabilities = torch.softmax(outputs.logits, dim=1)

    # 가장 높은 확률을 가진 클래스를 예측값으로 선택
    predicted_class = torch.argmax(probabilities, dim=1)

    # 각 클래스에 대한 확률값 출력
    class_probabilities = probabilities.squeeze().tolist()

    # 예측 클래스에 따른 설명
    predicted_class_label = {
        0: "안전한 코드입니다.",
        1: "CWE-119 취약점\nImproper Restriction of Operations within the Bounds of a Memory Buffer",
        2: "CWE-20 취약점\nImproper Input Validation",
        3: "CWE-125 취약점\nOut-of-bounds Read",
        4: "CWE-787 취약점\nOut-of-bounds Write",
        5: "CWE-415 취약점\nDouble Free",
        6: "CWE-399 취약점\nResource Management Errors",
        7: "CWE-416 취약점\nUse after Free",
        8: "CWE-476 취약점\nNULL Pointer Dereference",
        9: "CWE-190 취약점\nInteger Overflow or Wraparound"
    }

    predicted_class_label_text = predicted_class_label[predicted_class.item()]

    return class_probabilities, predicted_class_label_text

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    input_text = request.form['input_text']
    lang = request.form['lang']  # 추가된 부분

    # 입력 데이터 전처리 및 토큰화
    input_data = preprocess_and_tokenize_c_code(input_text, tokenizer)

    # 모델 예측 결과
    class_probabilities, predicted_class_label_text = predict_with_model(input_data, model)

    return render_template('index.html', 
        input_text=input_text, 
        output_text=predicted_class_label_text, 
        class_probabilities=class_probabilities,
        lang=lang)  # 언어도 전달


if __name__ == '__main__':
    app.run(debug=True)