import os
import subprocess
import json

def joern_parse(code_file, output_file):
    joern_cli_dir = os.path.join(os.getcwd(), 'joern-cli')
    joern_parse_command = f'./joern-parse {code_file} --language c -o {output_file}'
    
    try:
        result = subprocess.run(joern_parse_command, shell=True, capture_output=True, text=True, check=True, cwd=joern_cli_dir)
        print("Joern parse completed successfully.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error during joern parse: {e.stderr}")

def joern_slice(cpg_file, output_file):
    joern_cli_dir = os.path.join(os.getcwd(), 'joern-cli')
    joern_slice_command = f'./joern-slice data-flow --slice-depth 3 {cpg_file} -o {output_file}'
    
    try:
        result = subprocess.run(joern_slice_command, shell=True, capture_output=True, text=True, check=True, cwd=joern_cli_dir)
        print("Joern slice completed successfully.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error during joern slice: {e.stderr}")

def joern_extraction(json_file, code_directory, output_txt_path):
    if not os.path.isfile(json_file):
        print(f"Error: JSON file '{json_file}' does not exist.")
        return

    # 코드 파일 내용을 저장할 딕셔너리
    code_files_content = {}

    # 코드 디렉토리의 파일 읽기
    for filename in os.listdir(code_directory):
        if filename.endswith('.c') or filename.endswith('.cpp'):
            file_path = os.path.join(code_directory, filename)
            with open(file_path, 'r') as file:
                code_files_content[filename] = file.readlines()

    # JSON 파일 읽기 및 forward slicing된 라인 번호 추출
    with open(json_file, 'r') as file:
        data = json.load(file)

    # 라벨이 "REACHING_DEF" 또는 "CFG"인 엣지 수집
    forward_slice_edges = [edge for edge in data["edges"] if edge["label"] in ["REACHING_DEF", "CFG"]]

    # 노드 ID를 이용하여 라인 번호 수집
    line_numbers = set()
    node_id_to_line = {node["id"]: node["lineNumber"][0] for node in data["nodes"] if "lineNumber" in node}

    for edge in forward_slice_edges:
        dst_node_id = edge["dst"]
        if dst_node_id in node_id_to_line:
            line_numbers.add(node_id_to_line[dst_node_id])

    sorted_line_numbers = sorted(line_numbers)
    print(f"Extracted Line Numbers: {sorted_line_numbers}")

    # 원본 코드에서 해당 라인 번호의 코드만 추출
    code_filename_c = os.path.basename(json_file).replace('.json', '.c')
    code_filename_cpp = os.path.basename(json_file).replace('.json', '.cpp')

    code_lines = None
    if code_filename_c in code_files_content:
        code_lines = code_files_content[code_filename_c]
    elif code_filename_cpp in code_files_content:
        code_lines = code_files_content[code_filename_cpp]

    if code_lines is not None:
        extracted_lines = []
        for line_number in sorted_line_numbers:
            if 0 < line_number <= len(code_lines):
                extracted_lines.append(code_lines[line_number - 1].strip())

        # 추출된 코드 라인을 텍스트 파일로 저장
        with open(output_txt_path, 'w') as output_file:
            output_file.write('\n'.join(extracted_lines))

        print(f"Extracted code has been saved to '{output_txt_path}'")
    else:
        print(f"Code file corresponding to '{json_file}' not found in '{code_directory}'")
