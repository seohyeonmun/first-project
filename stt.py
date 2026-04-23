import whisper
import requests
import re
import xml.etree.ElementTree as ET

# 1. Whisper - base 모델
model = whisper.load_model("base")


# 2. STT
def speech_to_text(audio_path):
    result = model.transcribe(audio_path, language="ko")
    return result["text"]


# 3. 버스 번호 추출
def extract_bus_number(text):
    text = text.replace("번", "")
    numbers = re.findall(r"\d{1,4}", text)
    return numbers[0] if numbers else None


# 4. 정류소 ID 찾기 
def find_busstop_id(keyword, service_key):
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

    for item in root.iter("STATION"): # 같은 이름의 정류소가 존재(상행/하행에 따라)
        name = item.find("BUSSTOP_NAME").text
        busstop_id = item.find("BUSSTOP_ID").text
        # next_busstop = item.find("NEXT_BUSSTOP").text => 모든 정류소마다 항상 있는 값이 아님! 실제 데이터는 불완전하다!
        
        if keyword in name:
            # print(f"정류소 찾음: {name} / ID: {busstop_id}")
            id.append((name,busstop_id))

            # for elem in root.iter():
            #     print(elem.tag)

            # return busstop_id

    if id:
        return id
    else:
        print("❌ 정류소 못 찾음")
        return None

# 5. 버스 이름 추출
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
        return words[0]
    
    return None

# 6. 자동 선택
# def select_correct_busstop(candidates, bus_number, service_key):
#     for name, busstop_id in candidates:
#         xml_data = get_arrival_data(busstop_id, service_key)

#         if not xml_data:
#             continue
        
#         arrival = get_arrival_time(xml_data, bus_number)
#         if arrival: # 버스가 실제 오는 정류소
#             print('선택된 정류소:', name)
#             return busstop_id
    
#     return None
    

# 7. 도착정보 조회
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


# 8. 특정 버스 필터링
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


# 9. 실행
if __name__ == "__main__":

    SERVICE_KEY = "5d12073e2b1145367a82b4a460f37d262fe158a61d227acd9ad6fa32d0070069"

    # 🎤 음성 입력
    text = speech_to_text("audio/봉선.wav")
    print("인식된 문장:", text)


    # 🚌 버스 번호 추출
    bus_number = extract_bus_number(text)
    print("추출된 버스 번호:", bus_number)

    # 📍 정류소 이름 (일단 수동 입력)
    busstop_name = extract_busstop_name(text, bus_number)
    print("정류소: ", busstop_name)

    # 🔎 정류소 후보 ID 찾기
    busstop_id = find_busstop_id(busstop_name, SERVICE_KEY)
    # busstop_id = find_busstop_id(busstop_name, SERVICE_KEY)
    # print(busstop_id)

    # 자동 선택 => 하나만 선택하게 만든 부분
    # busstop_id = select_correct_busstop(candidates, bus_number, SERVICE_KEY)

    # if not busstop_id:
    #     print('해당 버스가 오는 정류소 없음')
    #     exit()
    
    # xml_data = get_arrival_data(busstop_id, SERVICE_KEY)
    # arrival, direction = get_arrival_time(xml_data, bus_number)

    # if arrival:
    #     print(f"{bus_number}번 버스 ({direction} 방향)은 {arrival}분 후 도착합니다.")
    # else:
    #     print('도착 정보 없음')

    if busstop_id and bus_number:
        # 📡 도착정보 조회
        for i in range(len(busstop_id)):
            xml_data = get_arrival_data(busstop_id[i][1], SERVICE_KEY)

            if xml_data:
                arrival, direction = get_arrival_time(xml_data, bus_number)

                if arrival:
                    print(f"{busstop_id[i][0]}, {bus_number}번 버스 ({direction} 방향)은 {arrival}분 후 도착합니다.")
                
    else:
        print("❌ 버스 번호 또는 정류소 ID 문제")







# 여기는 고민한 흔적이라 굳이 안보셔도 돼요!
# import whisper
# import os
# import re
# import requests
# import xml.etree.ElementTree as ET

# # print(os.getcwd())
# # print("파일 존재:", os.path.exists("audio/날씨별로.wav"))

# # whisper 결과 출력 확인 
# model = whisper.load_model("base")

# result = model.transcribe("audio/운림54.wav", language="ko")
# text = result['text']
# text = text.replace('번', '')
# print(text)

# # def extract_bus_number(text): 
# #     numbers = re.findall(r"\d+", text) 
# #     return numbers[0] if numbers else None

# # 숫자 추출
# def extract_bus_number(text):
#     numbers = re.findall(r"\d{1,4}", text)
#     return numbers[0] if numbers else None

# bus_number = extract_bus_number(result['text'])
# print(bus_number)

# if bus_number:
#     print(f"{bus_number}번 버스 조회")
# else:
#     print("버스 번호 인식 실패")

# # 5d12073e2b1145367a82b4a460f37d262fe158a61d227acd9ad6fa32d0070069
# # def get_bus_arrival(busstop_id):
# #     url = "http://api.gwangju.go.kr/xml/arriveInfo"

# #     params = {
# #         "serviceKey": "5d12073e2b1145367a82b4a460f37d262fe158a61d227acd9ad6fa32d0070069",
# #         "BUSSTOP_ID": busstop_id
# #     }

# #     response = requests.get(url, params=params)

    
# #     print(response.text)  # XML이라 이걸로 확인

# # get_bus_arrival(2513)


# def get_bus_stops():
#     url = "	https://api.gwangju.go.kr/xml/stationInfo"

#     params = {
#         "serviceKey": "5d12073e2b1145367a82b4a460f37d262fe158a61d227acd9ad6fa32d0070069"
#     }

#     response = requests.get(url, params=params)
#     return response.text  # response.text (XML이면), response.json() (JSON이면)




# def find_busstop_id(xml_data, target_name):
#     root = ET.fromstring(xml_data)

#     for item in root.iter("item"):
#         name = item.find("BUSSTOP_NAME").text

#         if target_name in name:
#             return item.find("BUSSTOP_ID").text

#     return None