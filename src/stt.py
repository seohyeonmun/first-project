import whisper
import requests
import re
import sounddevice as sd
import scipy.io.wavfile as wav
import xml.etree.ElementTree as ET
import Levenshtein
import os
from dotenv import load_dotenv

load_dotenv()
SERVICE_KEY = os.getenv("BUS_API_KEY")
# Whisper - base 모델 로드
model = whisper.load_model("base")

# 실시간 녹음
def record_audio(filename="temp.wav", duration=5, fs=16000):
    print('말씀해주세요')

    recording = sd.rec(
        int(duration * fs),
        samplerate=fs,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    wav.write(filename, fs, recording)
    print("녹음완료!")

    return filename

# STT
def speech_to_text(audio_path):
    result = model.transcribe(audio_path, language="ko")
    return result["text"]


# 버스 번호 추출
def extract_bus_number(text):
    text = text.replace("번", "")
    numbers = re.findall(r"\d{1,4}", text)
    return numbers[0] if numbers else None

# 정류소 이름 후보 추출
def extract_busstop_name(text, bus_number):
    if not bus_number or bus_number not in text:
        return None
    
    front = text.split(bus_number)[0]
    particles = ["의", "에서", "에", "쪽", "근처"]

    for p in particles:
        front = front.replace(p, " ")

    words = front.split()
    # print(words)

    if words:
        candidates = []
        for i in range(len(words)):
            combined = "".join(words[i:])
            candidates.append(combined)
        return candidates[::-1]
        # return words[0]
    
    return None

# 정류소 ID 찾기 
def find_busstop_id(keywords, service_key):
    url = "http://api.gwangju.go.kr/xml/stationInfo"  # 여기 URL 넣어야 함

    params = {
        "serviceKey": service_key
    }

    response = requests.get(url, params=params, timeout=5)

    # print(response.text)

    if not response.text.strip():
        print("❌ 정류소 목록 응답 없음")
        return []

    root = ET.fromstring(response.text)

    id = [] 
    # best = None
    best_name = None
    best_score = 0


    for keyword in keywords :
        for item in root.iter("STATION"): # 같은 이름의 정류소가 존재(상행/하행에 따라)
            name = item.find("BUSSTOP_NAME").text
            busstop_id = item.find("BUSSTOP_ID").text
            # next_busstop = item.find("NEXT_BUSSTOP").text => 모든 정류소마다 항상 있는 값이 아님! 실제 데이터는 불완전하다!
            
            score = Levenshtein.ratio(keyword, name)

            if score > best_score:
                best_score = score
                best_name = name
                id = [(best_name, busstop_id)]
            elif name == best_name:
                id.append((name, busstop_id))
            
        # for i in root.iter('STATION'):
        #     busstop_id = i.find("BUSSTOP_ID").text
        #     name2 = i.find("BUSSTOP_NAME").text
        #     if best == name2:
        #         id.append((best, busstop_id))

        
            # if name in keyword:
            #     # print(f"정류소 찾음: {name} / ID: {busstop_id}")
            #     id.append((name,busstop_id))

                # for elem in root.iter():
                #     print(elem.tag)

                # return busstop_id

    if id:
        return id
    else:
        print("❌ 정류소 못 찾음")
        return None

    
# 도착정보 조회
def get_arrival_data(busstop_id, service_key):
    url = "http://api.gwangju.go.kr/xml/arriveInfo"

    params = {
        "serviceKey": service_key,
        "BUSSTOP_ID": busstop_id
    }

    response = requests.get(url, params=params, timeout=5)

    if not response.text.strip():
        print("❌ 도착정보 응답 없음")
        return None

    return response.text


# 특정 버스 필터링
def get_arrival_time(xml_data, target_bus):
    root = ET.fromstring(xml_data)

    for item in root.iter("ARRIVE"):
        bus = item.find("LINE_NAME").text

        # print("현재 버스:", bus)  # 디버깅

        if target_bus in bus:  # 🔥 핵심
            remain = item.find("REMAIN_MIN").text

            # 방향 정보 추가
            direction = item.find("DIR_END").text

            return remain, direction

    return None, None


# main.py에서 사용할 함수
def process_voice():
    audio_path = record_audio()

    text = speech_to_text(audio_path)
    print("인식한 문장: ", text)

    bus_number = extract_bus_number(text)
    names = extract_busstop_name(text, bus_number)

    busstop_id = find_busstop_id(names)

    if not bus_number or not names:
        return "버스 번호 또는 정류소를 이해하지 못했습니다."

    if busstop_id and bus_number:
        #  도착정보 조회
        for i in range(len(busstop_id)):
            xml_data = get_arrival_data(busstop_id[i][1], SERVICE_KEY)

            if xml_data:
                arrival, direction = get_arrival_time(xml_data, bus_number)

                if arrival:
                    return f"{busstop_id[i][0]}, {bus_number}번 버스 ({direction} 방향)은 {arrival}분 후 도착합니다."
                
    else:
        return "도착 정보를 찾지 못했습니다."
    
