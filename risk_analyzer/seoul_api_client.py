# risk_analyzer/seoul_api_client.py
import os
import requests
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SEOUL_API_KEY = os.getenv("SEOUL_API_KEY", "sample")
SEOUL_API_BASE = "http://openapi.seoul.go.kr:8088"


def call_seoul_rental_api(
    cgg_cd: str = None,
    cgg_nm: str = None,
    rcpt_yr: str = None,
    start_index: int = 1,
    end_index: int = 100
) -> Optional[List[Dict]]:
    """
    서울시 부동산 실거래가 API 호출
    
    Args:
        cgg_cd: 자치구 코드 (5자리, 예: 11140)
        cgg_nm: 자치구명 (예: 중구)
        rcpt_yr: 접수연도 (YYYY)
        start_index: 시작 위치 (페이징)
        end_index: 종료 위치 (페이징)
    
    Returns:
        실거래가 데이터 리스트
    """
    
    # URL 구성
    url = f"{SEOUL_API_BASE}/{SEOUL_API_KEY}/xml/tbLnOpendataRtmsV/{start_index}/{end_index}"
    
    # 선택 파라미터 추가
    params = []
    if rcpt_yr:
        params.append(rcpt_yr)
    if cgg_cd:
        params.append(cgg_cd)
    elif cgg_nm:
        params.append(cgg_nm)
    
    # URL에 파라미터 추가
    if params:
        url += "/" + "/".join(params)
    
    try:
        print(f"  🌐 API 호출: {url[:80]}...")
        response = requests.get(url, timeout=15)
        
        if response.status_code != 200:
            print(f"  ❌ HTTP 오류: {response.status_code}")
            return None
        
        # XML 파싱
        root = ET.fromstring(response.content)
        
        # 결과 코드 확인
        result_elem = root.find('RESULT')
        if result_elem is not None:
            code = result_elem.find('CODE')
            message = result_elem.find('MESSAGE')
            
            if code is not None and code.text != "INFO-000":
                print(f"  ❌ API 오류: {code.text} - {message.text if message is not None else ''}")
                return None
        
        # 총 건수
        total_count = root.find('list_total_count')
        if total_count is not None:
            print(f"  📊 총 {total_count.text}건 중 {end_index-start_index+1}건 조회")
        
        # 데이터 파싱
        data_list = []
        for row in root.findall('row'):
            try:
                data = {
                    "접수연도": safe_text(row, 'RCPT_YR'),
                    "자치구코드": safe_text(row, 'CGG_CD'),
                    "자치구": safe_text(row, 'CGG_NM'),
                    "법정동코드": safe_text(row, 'STDG_CD'),
                    "법정동": safe_text(row, 'STDG_NM'),
                    "지번구분": safe_text(row, 'LOTNO_SE_NM'),
                    "본번": safe_text(row, 'MNO'),
                    "부번": safe_text(row, 'SNO'),
                    "건물명": safe_text(row, 'BLDG_NM'),
                    "계약일": safe_text(row, 'CTRT_DAY'),
                    "거래금액": safe_int(row, 'THING_AMT'),  # 만원
                    "건물면적": safe_float(row, 'ARCH_AREA'),  # ㎡
                    "토지면적": safe_float(row, 'LAND_AREA'),  # ㎡
                    "층수": safe_text(row, 'FLR'),
                    "권리구분": safe_text(row, 'RGHT_SE'),
                    "취소일": safe_text(row, 'RTRCN_DAY'),
                    "건축연도": safe_text(row, 'ARCH_YR'),
                    "건물용도": safe_text(row, 'BLDG_USG'),
                    "신고구분": safe_text(row, 'DCLR_SE'),
                }
                data_list.append(data)
            except Exception as e:
                continue  # 파싱 오류 무시
        
        print(f"  ✅ {len(data_list)}건 파싱 완료")
        return data_list
    
    except requests.exceptions.Timeout:
        print(f"  ❌ API 타임아웃 (15초)")
        return None
    except Exception as e:
        print(f"  ❌ 예외 발생: {e}")
        return None


def safe_text(element, tag: str) -> str:
    """XML에서 텍스트 안전하게 추출"""
    child = element.find(tag)
    return child.text if child is not None and child.text else ""


def safe_int(element, tag: str) -> int:
    """XML에서 정수 안전하게 추출"""
    text = safe_text(element, tag)
    try:
        return int(text) if text else 0
    except:
        return 0


def safe_float(element, tag: str) -> float:
    """XML에서 실수 안전하게 추출"""
    text = safe_text(element, tag)
    try:
        return float(text) if text else 0.0
    except:
        return 0.0


def get_district_code(district_name: str) -> str:
    """자치구 이름 → 코드 변환"""
    codes = {
        "종로구": "11110", "중구": "11140", "용산구": "11170",
        "성동구": "11200", "광진구": "11215", "동대문구": "11230",
        "중랑구": "11260", "성북구": "11290", "강북구": "11305",
        "도봉구": "11320", "노원구": "11350", "은평구": "11380",
        "서대문구": "11410", "마포구": "11440", "양천구": "11470",
        "강서구": "11500", "구로구": "11530", "금천구": "11545",
        "영등포구": "11560", "동작구": "11590", "관악구": "11620",
        "서초구": "11650", "강남구": "11680", "송파구": "11710",
        "강동구": "11740"
    }
    return codes.get(district_name, "11140")


def search_similar_property(
    address: str,
    deposit: int
) -> Optional[Dict]:
    """
    주소와 보증금으로 유사 매물 검색 및 통계 계산
    
    Returns:
        매매가, 전세가, 통계 정보
    """
    
    # 자치구 추출
    district = None
    for name in ["종로구", "중구", "용산구", "성동구", "광진구",
                 "동대문구", "중랑구", "성북구", "강북구", "도봉구",
                 "노원구", "은평구", "서대문구", "마포구", "양천구",
                 "강서구", "구로구", "금천구", "영등포구", "동작구",
                 "관악구", "서초구", "강남구", "송파구", "강동구"]:
        if name in address:
            district = name
            break
    
    if not district:
        district = "중구"  # 기본값
    
    # 현재 연도
    current_year = str(datetime.now().year)
    
    # API 호출
    cgg_cd = get_district_code(district)
    data_list = call_seoul_rental_api(
        cgg_cd=cgg_cd,
        rcpt_yr=current_year,
        start_index=1,
        end_index=200  # 최대 200건
    )
    
    if not data_list or len(data_list) == 0:
        print("  ⚠️ API 데이터 없음, 더미 데이터 사용")
        return get_dummy_price_data(address, deposit)
    
    # 유사 매물 필터링 (±40% 범위)
    target = deposit
    similar = [d for d in data_list 
               if d['거래금액'] > 0 and 
               abs(d['거래금액'] - target) / max(target, 1) < 0.4]
    
    if not similar:
        similar = data_list  # 필터링 결과 없으면 전체 사용
    
    # 평균 전세가
    avg_jeonse = sum(d['거래금액'] for d in similar) / len(similar)
    
    # 매매가 추정 (전세가의 1.3~1.5배)
    estimated_매매가 = int(avg_jeonse * 1.4)
    
    # 통계 계산 (논문 기반)
    stats = calculate_market_stats(data_list, district)
    
    return {
        "매매가": estimated_매매가 * 10000,  # 만원 → 원
        "전세가": int(avg_jeonse) * 10000,
        "거래건수": len(data_list),
        "유사매물": len(similar),
        "자치구": district,
        "데이터출처": "서울시 Open API",
        **stats  # 통계 정보 추가
    }


def calculate_market_stats(data_list: List[Dict], district: str) -> Dict:
    """시장 통계 계산 (논문 기반)"""
    
    if not data_list:
        return {
            "평균거래가": 0,
            "거래량": 0,
            "시장과열도": "보통"
        }
    
    # 평균 거래가
    avg_price = sum(d['거래금액'] for d in data_list if d['거래금액'] > 0) / len(data_list)
    
    # 거래량 (최근 데이터 기준)
    recent_count = len([d for d in data_list if d['계약일'] and d['계약일'].startswith('2025')])
    
    # 시장 과열도 판단 (논문 기반)
    if recent_count > 100 and avg_price > 50000:
        market_heat = "과열"
    elif recent_count > 50:
        market_heat = "활성"
    else:
        market_heat = "보통"
    
    return {
        "평균거래가": int(avg_price),
        "거래량": recent_count,
        "시장과열도": market_heat
    }


def get_dummy_price_data(address: str, deposit: int) -> Dict:
    """API 실패 시 더미 데이터"""
    return {
        "매매가": int(deposit * 1.4 * 10000),
        "전세가": deposit * 10000,
        "거래건수": 0,
        "유사매물": 0,
        "자치구": "알 수 없음",
        "데이터출처": "추정값 (API 오류)",
        "평균거래가": deposit,
        "거래량": 0,
        "시장과열도": "알 수 없음"
    }


# ==========================================
# 테스트 코드
# ==========================================
if __name__ == "__main__":
    print("="*70)
    print("🧪 서울시 부동산 API 테스트")
    print("="*70 + "\n")
    
    # 테스트 1: API 직접 호출
    print("📍 테스트 1: API 직접 호출 (중구, 2025년)\n")
    result = call_seoul_rental_api(
        cgg_cd="11140",
        rcpt_yr="2025",
        start_index=1,
        end_index=10
    )
    
    if result:
        print(f"\n✅ {len(result)}건 조회 성공\n")
        print("📊 첫 3개 데이터:\n")
        for data in result[:3]:
            print(f"  • {data['자치구']} {data['법정동']} {data['건물명']}")
            print(f"    거래금액: {data['거래금액']:,}만원")
            print(f"    면적: {data['건물면적']}㎡")
            print(f"    용도: {data['건물용도']}\n")
    else:
        print("\n❌ API 호출 실패 (더미 데이터 모드)\n")
    
    # 테스트 2: 주소로 검색
    print("="*70)
    print("📍 테스트 2: 주소 기반 검색\n")
    print("="*70 + "\n")
    
    test_address = "서울 중구 신당동"
    test_deposit = 17000
    
    print(f"입력 주소: {test_address}")
    print(f"입력 보증금: {test_deposit:,}만원\n")
    
    result2 = search_similar_property(test_address, test_deposit)
    
    if result2:
        print("✅ 검색 성공\n")
        print("📊 분석 결과:")
        print(f"  • 추정 매매가: {result2['매매가']:,}원")
        print(f"  • 입력 보증금: {result2['전세가']:,}원")
        print(f"  • 전세가율: {(result2['전세가']/result2['매매가']*100):.1f}%")
        print(f"  • 거래 건수: {result2['거래건수']}건")
        print(f"  • 유사 매물: {result2['유사매물']}건")
        print(f"  • 자치구: {result2['자치구']}")
        print(f"  • 데이터 출처: {result2['데이터출처']}")
        
        if '시장과열도' in result2:
            print(f"  • 시장 상황: {result2['시장과열도']} (거래량: {result2['거래량']}건)")
    else:
        print("❌ 검색 실패")
    
    print("\n" + "="*70)
    print("✅ 테스트 완료")
    print("="*70)
