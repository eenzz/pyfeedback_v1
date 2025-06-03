import streamlit as st
import requests
import openai
import subprocess
import tempfile
import os
import re
# GPT API Key (Streamlit Cloud secrets.toml에 저장)
# openai.api_key = st.secrets["OPENAI_API_KEY"]

# GPT API Key 설정 (secrets.toml에서 가져옴)
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


st.set_page_config(page_title="Python 코드 실행 with input", layout="wide")
st.title("🐍 Python 코드 피드백 시스템 ")

code = st.text_area("Python 코드 입력", height=300, placeholder="여기에 Python 코드를 작성하세요...")


# 코드에서 input() 감지
input_prompts = re.findall(r'input\((.*?)\)', code)
input_values = []

if input_prompts:
    st.info(f"이 코드에는 {len(input_prompts)}개의 input()이 있습니다. 아래 입력값을 작성해주세요.")
    for i, prompt in enumerate(input_prompts):
        user_input = st.text_input(f"Input {i+1}: {prompt.strip('\"')}", key=f"input_{i}")
        input_values.append(user_input)
if st.button("코드 실행 및 피드백"):
    if not code.strip():
        st.warning("코드를 작성해주세요!")
    else:
        # ❗️ input 값 미입력 체크
        if input_prompts and ("" in input_values or None in input_values):
            st.warning("모든 input() 입력값을 작성해주세요!")
        else:
            # 1️⃣ input() 치환
            processed_code = code
            for val in input_values:
                processed_code = re.sub(r'input\((.*?)\)', f'"{val}"', processed_code, count=1)

            # 2️⃣ 코드 실행
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
                tmp.write(processed_code)
                tmp_path = tmp.name

            try:
                result = subprocess.check_output(["python3", tmp_path], stderr=subprocess.STDOUT, text=True, timeout=5)
                st.success("✅ 실행 결과")
                st.code(result)
            except subprocess.CalledProcessError as e:
                st.error(f"❌ 실행 오류\n{e.output}")
            except subprocess.TimeoutExpired:
                st.error("⏰ 실행 시간 초과")
            finally:
                os.remove(tmp_path)

            # 3️⃣ Linter API 호출 (Express 서버 연동)
            linter_result = None
            try:
                linter_response = requests.post(
                    "https://pyfeedback-v1.onrender.com/lint",
                    json={"language": "python", "code": processed_code}
                )
                linter_result = linter_response.json()
                if 'error' in linter_result:
                    st.error(f"Linter 오류: {linter_result['error']}")
                else:
                    lint_lines = linter_result['feedback']

                    # 사용자에게 보기 쉽게 출력
                    st.subheader("📝 Linter 피드백")
                    for line in lint_lines:
                        st.write(f"• {line}")

                    # GPT로 보낼 텍스트 만들기
                    lint_feedback_text = "\n".join(lint_lines)

                    # 4️⃣ GPT API 호출
                    prompt = f"""아래는 Python 코드에 대한 Linter 피드백입니다.
    문제를 이해하기 쉽게 설명하고, 개선 방안을 알려주세요.

    Lint 결과:
    {lint_feedback_text}
    """
                    try:
                        gpt_response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[{"role": "user", "content": prompt}]
            )
                    
                        gpt_feedback = gpt_response.choices[0].message.content
                        st.subheader("🤖 GPT 해석 피드백")
                        st.write(gpt_feedback)
                    except Exception as e:
                        st.error(f"❌ GPT API 호출 오류: {e}")
            except Exception as e:
                st.error(f"❌ Linter 서버 호출 오류: {e}")
