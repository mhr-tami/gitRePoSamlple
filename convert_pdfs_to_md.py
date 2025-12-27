import os
from pathlib import Path
from typing import List

try:
    import pdfplumber
except ImportError:
    print("pdfplumber가 설치되어 있지 않습니다. 먼저 'pip install pdfplumber'를 실행해주세요.")
    raise SystemExit(1)


# 변환할 폴더 경로 (사용자 워크스페이스 기준)
BASE_DIR = Path(r"C:\Users\moonh\Documents\workspace\BA-to-SW-Dev_1\1_ 시장 및 비즈니스 분석 방법론")


def _extract_page_text_all_chars(page) -> str:
    """
    pdfplumber의 chars 정보를 이용해, 페이지에 존재하는 모든 문자 객체를
    가능한 한 그대로 이어붙입니다.
    (레이아웃은 다소 깨질 수 있지만, '문자 누락 최소화'에 초점을 둡니다.)
    """
    chars = page.chars
    if not chars:
        # chars 정보가 없으면 기본 extract_text()에 의존
        return page.extract_text() or ""

    # 위->아래(top 내림차순), 왼쪽->오른쪽(x0 오름차순)으로 정렬
    chars_sorted = sorted(chars, key=lambda c: (-c.get("top", 0), c.get("x0", 0)))

    lines: List[str] = []
    current_line: List[str] = []
    last_top = None
    line_height_threshold = 2  # y좌표 차이가 이 값보다 크면 줄바꿈으로 간주

    for ch in chars_sorted:
        text = ch.get("text", "")
        top = ch.get("top", 0)

        if last_top is None:
            last_top = top

        # 새로운 줄로 판단
        if abs(top - last_top) > line_height_threshold:
            if current_line:
                lines.append("".join(current_line))
                current_line = []
            last_top = top

        current_line.append(text)

    if current_line:
        lines.append("".join(current_line))

    return "\n".join(lines)


def _extract_page_text(page) -> str:
    """
    1순위: pdfplumber의 기본 extract_text() 사용 (레이아웃/띄어쓰기 보존에 유리)
    2순위: extract_text()가 실패하거나 내용이 거의 없는 경우, chars 기반 전체 문자 추출로 보완
    """
    try:
        text = page.extract_text() or ""
    except Exception:
        text = ""

    # extract_text 결과가 너무 짧으면(예: 공백 수준) chars 기반으로 재시도
    if not text.strip():
        text = _extract_page_text_all_chars(page)

    return text


def _extract_tables_markdown(page) -> str:
    """
    페이지 내 표를 가능한 한 많이 추출하여 Markdown 테이블 형태로 변환합니다.
    (표의 선/색 등 시각 요소는 살리지 못하지만, 셀 안의 '글자'는 최대한 보존합니다.)
    """
    try:
        tables = page.extract_tables()
    except Exception:
        tables = None

    if not tables:
        return ""

    md_parts: List[str] = []

    def fmt_row(row: List[str], col_count: int) -> str:
        cells = [(cell or "").replace("\n", " ").strip() for cell in row]
        if len(cells) < col_count:
            cells += [""] * (col_count - len(cells))
        elif len(cells) > col_count:
            cells = cells[:col_count]
        return "| " + " | ".join(cells) + " |"

    for idx, table in enumerate(tables, start=1):
        if not table or not any(table):
            continue

        header = table[0]
        col_count = len(header)

        md_parts.append(f"\n[표 {idx}]\n")
        # 헤더
        md_parts.append(fmt_row(header, col_count))
        # 구분선
        md_parts.append("| " + " | ".join(["---"] * col_count) + " |")
        # 데이터 행
        for row in table[1:]:
            md_parts.append(fmt_row(row, col_count))

    return "\n".join(md_parts)


def pdf_to_md(pdf_path: Path) -> None:
    """
    주어진 PDF 파일을 같은 폴더, 같은 파일명(.md 확장자)으로 저장합니다.
    가능한 한 페이지 단위로 모든 텍스트를 누락 없이 추출하려고 시도합니다.
    """
    md_path = pdf_path.with_suffix(".md")
    # 콘솔 인코딩(cp949) 문제를 피하기 위해 파일명은 출력하지 않음
    print("Converting one PDF file to Markdown...")

    page_texts: List[str] = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            try:
                # 1) 일반 텍스트 (extract_text로 우선 시도, 부족하면 chars 기반 보완)
                text_body = _extract_page_text(page)
                # 2) 표 텍스트를 Markdown 테이블로 별도 추출
                tables_md = _extract_tables_markdown(page)

                # Markdown 렌더링을 방해하지 않도록 페이지 구분은 HTML 주석으로 처리
                header = f"<!-- 페이지 {idx} -->\n\n"
                page_section = f"{header}{text_body}"
                if tables_md:
                    page_section = f"{page_section}\n\n{tables_md}"

            except Exception as exc:  # 개별 페이지에서 에러가 나도 전체 변환은 계속 진행
                header = f"<!-- 페이지 {idx} -->\n\n"
                page_section = f"{header}[페이지 {idx} 텍스트/표 추출 실패: {exc}]"

            page_texts.append(page_section)

    full_text = "\n\n\n".join(page_texts)

    # 동일한 폴더, 동일한 파일명에 .md 확장자로 저장 (기존 파일은 덮어씀)
    md_path.write_text(full_text, encoding="utf-8")


def main() -> None:
    if not BASE_DIR.exists():
        print(f"폴더를 찾을 수 없습니다: {BASE_DIR}")
        return

    for entry in BASE_DIR.iterdir():
        if entry.is_file() and entry.suffix.lower() == ".pdf":
            pdf_to_md(entry)

    print("모든 PDF -> MD 변환이 완료되었습니다.")


if __name__ == "__main__":
    main()


