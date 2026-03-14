# 올리브영 메이크업 상품정보 크롤러

## 요청사항

아래 요청사항을 확인해서 개발되었습니다.

- Playwright를 활용해서 개발합니다.
- olive.html에서 구조를 확인합니다.
- 카테고리 > 메이크업에 등록된 모든 제품을 크롤링합니다.
- 왼쪽 네비게이션바에서 립메이크업, 베이스메이크업, 아이메이크업을 클릭하고 페이지를 이동합니다.
- 호출된 상품의 이미지나 상품명을 클릭하고 페이지를 이동합니다.
- 브랜드명, 상품명, 가격, 별점, 리뷰수를 추출합니다.
- 상품설명 탭에서 상품정보 제공고시 아코디언을 펼치고 아코디언 컨텐트에 포함된 모든 내용을 추출합니다.
- 추출된 모든 정보를 모아 데이터 스키마를 만들고 CSV 형태로 olive_downloads 폴더에 저장합니다.

## 사용 방법

### CLI 스크립트

```bash
cd api
python scripts/test_olive_makeup.py -n 3        # 카테고리당 3개 (기본)
python scripts/test_olive_makeup.py --full     # 전체 크롤링
```

### API

- `POST /crawl/olive-makeup/start` - 메이크업 크롤 백그라운드 시작
- `GET /crawl/olive-makeup/export/latest` - 최신 CSV 다운로드

### 출력

- `olive_downloads/olive_makeup_{timestamp}.csv`
