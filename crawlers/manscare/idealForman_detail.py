from seleniumbase import SB
from bs4 import BeautifulSoup
from time import sleep
import datetime
import time
from pprint import pprint
import json
import os
data = []
# 상품 상세 주소 리스트화
def get_brand(brand_code) :
    url = f"https://www.oliveyoung.co.kr/store/display/getBrandShopDetail.do?onlBrndCd={brand_code}"
    collected_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with SB(uc=True, test=True, headless=True) as sb:
        sb.uc_open_with_reconnect(url, reconnect_time=20)
        time.sleep(2)

        page = 1
        while True:
            if page > 1:
                try:
                    # 페이지네이션 버튼 클릭 (페이지가 없으면 break)
                    sb.click(f"div.pageing a[data-page-no='{page}']")
                    time.sleep(2)  # ajax 로딩 대기
                except Exception as e:
                    print(f"{page}페이지 버튼 클릭 실패 또는 더 이상 페이지 없음: {e}")
                    break

            html = sb.driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            # 브랜드명 추출
            try:
                brand = soup.select_one("h2.title-detail-brand").text.strip()
            except Exception:
                brand = "아이디얼포맨"

            # 상품 목록 추출
            items = soup.select("ul.prod-list.goodsProd > li")
            if not items:
                print(f"{page}페이지에 상품이 없습니다.")
                break

            for item in items:
                is_pb = 1
                # 상품명
                try:
                    name = item.select_one("span.prod-name.double-line").text.strip()
                except Exception:
                    name = ""
                # 할인가
                try:
                    price_final = item.select_one("strong.total").text.strip().replace("원", "").replace(",", "").replace("~", "")
                except Exception:
                    price_final = ""
                # 정가
                try:
                    price_original = item.select_one("span.origin").text.strip().replace("원", "").replace(",", "")
                except Exception:
                    price_original = ""
                # 혜택
                try:
                    flag_spans = item.select("div.flags span.flag")
                    flag_list = [span.text.strip() for span in flag_spans if span.text.strip()]
                    flag_str = ",".join(flag_list) if flag_list else ""
                except Exception:
                    flag_str = ""
                # 품절여부
                try:
                    soldout_flag = item.select_one("span.status_flag.soldout")
                    is_soldout = bool(soldout_flag)
                except Exception:
                    is_soldout = False
                # 주소
                try:
                    link = item.select_one("a")["href"]
                except Exception:
                    link = ""
                data.append({
                    "brandName": brand,
                    "isPB": is_pb,
                    "goodsName": name,
                    "category" : "manscare",
                    "salePrice": price_final,
                    "originalPrice": price_original,
                    "flagList": flag_str,
                    "isSoldout": is_soldout,
                    "createdAt": collected_at,
                    "link": link
                })
            # 다음 페이지로
            page += 1

    return data

#상품 상세 정보 크롤링
def crawl_product_detail(data) :
    for item in data :
        goodsName = item['goodsName']
        url = item['link']
        review_detail = []
        with SB(uc=True, test=True, headless=True) as sb:
            sb.uc_open_with_reconnect(url, reconnect_time=60)

            html = sb.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # 구매정보 
            try:
                sb.click("a.goods_buyinfo")
                sleep(2)
                print("✅ 구매정보 탭 클릭 완료")

                # 전체 <dl> 리스트 가져오기
                dl_elements = sb.find_elements("css selector", "dl.detail_info_list")

                # 가져올 인덱스 (1, 2, 7번째 → 파이썬 기준: 0, 1, 6)
                target_indices = [1, 2, 7]
                target_fields = ['capacity', 'detail', 'ingredients']  # 원하는 이름으로 바꾸세요

                result = {}

                for idx, field in zip(target_indices, target_fields):
                    try:
                        dd = dl_elements[idx].find_element("css selector", "dd").text.strip()
                        result[field] = dd
                    except Exception as e:
                        result[field] = None  # 값이 없을 경우 None 처리

                print(result)
            except Exception as e:
                print("구매정보 탭 클릭 실패:", e)

            # 리뷰정보 
            try:
                sb.click("a.goods_reputation")
                sleep(2)
                print("✅ 리뷰 정보 탭 클릭 완료")
                # 리뷰정리
                totalComment = sb.get_text("div.grade_img em")
                # 리뷰갯수
                numOfReviews = sb.get_text("div.star_area em")
                # 리뷰 평점
                avgReview = sb.get_text("div.star_area strong")
                # 리뷰 점수 퍼센트
                percent_elements = sb.find_elements("css selector", "ul.graph_list span.per")
                percent_list = [el.text.strip() for el in percent_elements]
                pctOf5 = percent_list[0]
                pctOf4 = percent_list[1]
                pctOf3 = percent_list[2]
                pctOf2 = percent_list[3]
                pctOf1 = percent_list[4]
            except Exception as e:
                print("리뷰 정보 탭 클릭 완료:", e)
                
            # 리뷰 상세 정보
            polls = sb.find_elements("css selector", "dl.poll_type2.type3")
            for poll in polls:
                try:
                    # 설문 제목 (예: 피부타입)
                    title = poll.find_element("css selector", "span").text.strip()
                    # 하위 항목들 (li)
                    li_tags = poll.find_elements("css selector", "ul.list > li")
                    for li in li_tags:
                        label = li.find_element("css selector", "span.txt").text.strip()
                        percent = li.find_element("css selector", "em.per").text.strip()
                        review_detail.append({
                            "type": title,
                            "value": label,
                            "gauge": percent
                        })
                except Exception as e:
                    print("리뷰 정보 오류:", e)

            # 저장
            product_detail_info = {
                "totalcoment": totalComment,
                "numOfReviews": numOfReviews,
                "avgReview": avgReview,
                "pctOf5": pctOf5,
                "pctOf4": pctOf4,
                "pctOf3": pctOf3,
                "pctOf2": pctOf2,
                "pctOf1": pctOf1,
                "capacity": result['capacity'],
                "detail": result['detail'],
                "ingredients": result['ingredients'],
                "review_detail" : review_detail
            }
            # 업데이트
            item.update(product_detail_info)
            pprint(item)
            print("===============================================================")
    return
def save_s3(data,time):
    file_name = f"{time}_PB_아이디얼포맨.json"
    folder_path = "JSON"
    os.makedirs(folder_path, exist_ok=True)
    full_path = os.path.join(folder_path, file_name)
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 저장 완료: {full_path}")

    return

collected_at = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
print("시작시간 : ",  collected_at)
data = get_brand("A001643")
crawl_product_detail(data)
save_json(data ,collected_at)
collected_at = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
print("종료시간 : ",  collected_at)
