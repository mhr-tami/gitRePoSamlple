import argparse
from pathlib import Path


def extract_pdf_text(pdf_path: Path) -> tuple[int, list[str]]:
    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    texts: list[str] = []
    for i, page in enumerate(doc, start=1):
        t = page.get_text("text") or ""
        t = t.strip("\n")
        texts.append(f"\n\n===== Page {i} / {doc.page_count} =====\n\n" + (t if t else "[NO_TEXT_EXTRACTED]"))
    return doc.page_count, texts


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract text from a PDF into a UTF-8 .txt file.")
    # NOTE: In some Windows terminal/codepage setups, passing Korean paths via argv can get
    # lossy-decoded into '?' characters, which then become invalid Windows paths (WinError 123).
    # To keep this tool usable in such environments, we allow args to be omitted and fall back
    # to known repo-relative defaults (Unicode literals in this UTF-8 source file).
    parser.add_argument("--pdf", required=False, help="Path to input PDF")
    parser.add_argument("--out", required=False, help="Path to output .txt file")
    args = parser.parse_args()

    default_pdf = Path("2_핵심예제 분석자료") / (
        "6_SaaS_형_온라인_비즈니스_컨설팅_시장의_고객_페르소나_스펙트럼_고객_여정지도_(Gemini_분석_기반).pdf"
    )
    default_out = Path("2_핵심예제 분석자료") / "GPT-ValueProPositionSheet" / "6_persona_cjm_extracted.txt"

    pdf_path = Path(args.pdf) if args.pdf else default_pdf
    out_path = Path(args.out) if args.out else default_out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pages, texts = extract_pdf_text(pdf_path)
    out_path.write_text("".join(texts), encoding="utf-8")

    print(f"pages={pages}")
    print(f"wrote={out_path}")


if __name__ == "__main__":
    main()


