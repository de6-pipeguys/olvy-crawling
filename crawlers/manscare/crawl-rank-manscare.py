from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from seleniumbase import SB
from bs4 import BeautifulSoup
from time import sleep
import datetime
import time
import pprint
# 상품 상세 주소 리스트화
def crawl_product_info() :
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(service=Service(), options=options)

    url = "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000010004&pageIdx=1&rowsPerPage=8&t_page=%EB%9E%AD%ED%82%B9&t_click=%ED%8C%90%EB%A7%A4%EB%9E%AD%ED%82%B9_%ED%97%A4%EC%96%B4%EC%BC%80%EC%96%B4"
    driver.get(url)
    time.sleep(3)  # 로딩 대기

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    collected_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = []

    product_blocks = soup.select("div.prd_name")
    start_num = 0
    for prd_name in product_blocks:
        # 상품 이름
        try:
            name = prd_name.select_one("a").text.strip()
            print(name)
        except:
            name = ""
            print("이름 오류")
        # 링크
        try:
            link = prd_name.select_one("a")["href"]
        except:
            link = ""

        # 브랜드명
        try:
            brand = prd_name.select_one("span.tx_brand").text.strip()
        except:
            brand = ""
        parent = prd_name.find_parent()  # 가격 정보가 같은 부모 하위에 있을 가능성 높음
        # 할인가
        try:
            price_final = parent.select_one("span.tx_cur span.tx_num").text.strip().replace(",", "")
        except:
            price_final = ""
        # 정가
        try:
            price_original = parent.select_one("span.tx_org span.tx_num").text.strip().replace(",", "")
        except:
            price_original = ""
        # 혜택 정보
        try:
            flag_spans = parent.select("p.prd_flag span.icon_flag")
            flag_list = [span.text.strip() for span in flag_spans if span.text.strip()]
            flag_str = ",".join(flag_list) if flag_list else ""
        except:
            flag_str = ""
        pb_brands = [
            "바이오힐 보",
            "브링그린",
            "웨이크메이크",
            "컬러그램",
            "필리밀리",
            "아이디얼포맨",
            "라운드어라운드",
            "식물나라",
            "케어플러스",
            "탄탄",
            "딜라이트 프로젝트",
        ]
        # Pb 상품 여부
        is_pb = 1 if brand in pb_brands else 0
        start_num = start_num + 1
        data.append({
            "rank": start_num,
            "brandName": brand,
            "isPB": is_pb,
            "goodsName": name,
            "salePrice": price_final,
            "originalPrice": price_original,
            "flagList": flag_str,
            "isSoldout": 1,
            "createdAt": collected_at,
            "link": link
        })

    return data

#상품 상세 정보 크롤링
def crawl_product_detail(list) :
    product_data = []
    for url in list :
        print(url)
        with SB(uc=True, test=True) as sb:
            sb.uc_open_with_reconnect(url, reconnect_time=60)

            html = sb.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            try:
                # 브랜드 명
                brand_name = sb.get_text("#moveBrandShop")

                # 제품명
                product_name = sb.get_text("p.prd_name")

                # 할인가
                discount_price = sb.get_text("span.price-2 strong")

                # 정가
                if sb.is_element_present("span.price-1 strike"):
                    origin_price = sb.get_text("span.price-1 strike")
                else:
                    origin_price = discount_price

                # 세일플래그
                flags = []
                span_elements = sb.find_elements("css selector", "p#icon_area span")
                for span in span_elements:
                    flags.append(span.text.strip())
                print("기본 정보 수집 성공")
            except Exception as e:
                print("기본 정보 수집 실패:", e)

            # 구매정보 클릭
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

            # 리뷰정보 클릭 및 수집
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
                # 리뷰 정보
                polls = sb.find_elements("css selector", "dl.poll_type2.type3")
                review_detail = []
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
            product_info = {
                "brand": brand_name,  # 브랜드명
                "product": product_name,  # 상품이름
                "discountPrice": discount_price,  # 할인가
                "originPrice": origin_price,  # 정가
                "category": "manscare",
                "isPB": 1,  # Pb여부
                "flag": flags,  # 혜택
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
                "ingredients": result['ingredients']
            }
            product_data.append(product_info)
        from pprint import pprint
        pprint(product_data)
    return product_data
def jsonSave():
    return
product_links = crawl_product_info()
crawl_product_detail(product_links)
