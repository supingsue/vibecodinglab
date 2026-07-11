#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf2pptx.py — 將 PDF 轉換為 PPTX 的命令列工具

轉換策略：每一頁 PDF 渲染成一張高解析度圖片，貼滿一張投影片；
頁面上的文字另外抽取出來，放進該張投影片的「演講者備忘稿」。
"""

import argparse
import io
import sys
from pathlib import Path

import fitz  # PyMuPDF：負責 PDF 解析與頁面渲染
from pptx import Presentation
from pptx.util import Emu

# 預設渲染解析度（DPI）
DEFAULT_DPI = 200

# 1 英吋 = 914400 EMU（python-pptx 的內部長度單位）
EMU_PER_INCH = 914400

# 投影片尺寸（英吋）：長寬比 >= 1.6 用 16:9，否則用 4:3
SIZE_16_9 = (13.333, 7.5)   # 13.33 × 7.5 英吋
SIZE_4_3 = (10.0, 7.5)      # 10 × 7.5 英吋
ASPECT_THRESHOLD = 1.6


class ChineseArgumentParser(argparse.ArgumentParser):
    """自訂的參數解析器：錯誤訊息改為繁體中文，並在錯誤時顯示用法。"""

    def error(self, message):
        # 參數錯誤時：先印出用法，再以結束碼 1 離開
        self.print_usage(sys.stderr)
        # 將 argparse 常見的英文錯誤訊息翻成繁體中文
        if "the following arguments are required" in message:
            missing = message.split(":", 1)[1].strip()
            message = f"缺少必要參數：{missing}"
        elif "unrecognized arguments" in message:
            extra = message.split(":", 1)[1].strip()
            message = f"無法辨識的參數：{extra}"
        elif "invalid int value" in message:
            message = "--dpi 必須是整數"
        sys.stderr.write(f"參數錯誤：{message}\n")
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    """建立命令列參數解析器（所有說明文字皆為繁體中文）。"""
    parser = ChineseArgumentParser(
        prog="pdf2pptx.py",
        description="將 PDF 檔案轉換為 PPTX 簡報：每頁渲染成圖片貼入投影片，"
                    "頁面文字寫入演講者備忘稿。",
        epilog="範例：python pdf2pptx.py 講義.pdf -o 簡報.pptx --pages 5-12 --dpi 300",
        add_help=False,  # 停用內建 -h，改用中文說明
    )
    parser.add_argument(
        "-h", "--help",
        action="help",
        help="顯示本說明訊息後結束",
    )
    parser.add_argument(
        "input_pdf",
        metavar="輸入.pdf",
        help="要轉換的 PDF 檔案路徑",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="輸出.pptx",
        default=None,
        help="輸出的 PPTX 檔案路徑（預設：與輸入檔同目錄、同檔名，副檔名改為 .pptx）",
    )
    parser.add_argument(
        "--pages",
        metavar="起始-結束",
        default=None,
        help="要轉換的頁數範圍，從 1 起算，例如 5-12 或單頁 7（預設：全部頁面）",
    )
    parser.add_argument(
        "--dpi",
        metavar="數值",
        type=int,
        default=DEFAULT_DPI,
        help=f"渲染解析度 DPI（預設：{DEFAULT_DPI}）",
    )
    return parser


def default_output_path(input_pdf: str) -> str:
    """未指定 -o 時：與輸入檔同目錄、同檔名，副檔名改為 .pptx。"""
    return str(Path(input_pdf).with_suffix(".pptx"))


def choose_slide_size(first_page: "fitz.Page") -> tuple[float, float]:
    """依 PDF 第一頁的長寬比決定投影片尺寸（英吋）。"""
    rect = first_page.rect
    aspect = rect.width / rect.height
    return SIZE_16_9 if aspect >= ASPECT_THRESHOLD else SIZE_4_3


def place_page_image(slide, png_bytes: bytes, img_w: int, img_h: int,
                     slide_w_in: float, slide_h_in: float) -> None:
    """將頁面圖片等比縮放、置中貼入投影片（完整顯示不裁切，允許留白）。"""
    img_aspect = img_w / img_h
    slide_aspect = slide_w_in / slide_h_in
    if img_aspect >= slide_aspect:
        # 圖片比投影片寬：以寬度貼滿，上下留白
        draw_w = slide_w_in
        draw_h = slide_w_in / img_aspect
    else:
        # 圖片比投影片高：以高度貼滿，左右留白
        draw_h = slide_h_in
        draw_w = slide_h_in * img_aspect
    left = Emu(int((slide_w_in - draw_w) / 2 * EMU_PER_INCH))
    top = Emu(int((slide_h_in - draw_h) / 2 * EMU_PER_INCH))
    slide.shapes.add_picture(
        io.BytesIO(png_bytes), left, top,
        width=Emu(int(draw_w * EMU_PER_INCH)),
        height=Emu(int(draw_h * EMU_PER_INCH)),
    )


def convert(input_pdf: str, output_pptx: str, dpi: int) -> int:
    """核心轉換：逐頁渲染成 PNG 貼入投影片，回傳轉換的頁數。"""
    doc = fitz.open(input_pdf)
    try:
        slide_w_in, slide_h_in = choose_slide_size(doc[0])

        prs = Presentation()
        prs.slide_width = Emu(int(slide_w_in * EMU_PER_INCH))
        prs.slide_height = Emu(int(slide_h_in * EMU_PER_INCH))
        blank_layout = prs.slide_layouts[6]  # 空白版面

        for page in doc:
            # 將該頁渲染為 PNG 圖片
            pix = page.get_pixmap(dpi=dpi)
            png_bytes = pix.tobytes("png")
            slide = prs.slides.add_slide(blank_layout)
            place_page_image(slide, png_bytes, pix.width, pix.height,
                             slide_w_in, slide_h_in)

            # 抽取該頁文字（保留段落換行）寫入演講者備忘稿；無文字時留空
            text = page.get_text("text").rstrip()
            if text:
                slide.notes_slide.notes_text_frame.text = text

        prs.save(output_pptx)
        return doc.page_count
    finally:
        doc.close()


def main(argv=None) -> int:
    """程式進入點：解析參數後執行轉換。"""
    parser = build_parser()
    args = parser.parse_args(argv)

    output_pptx = args.output or default_output_path(args.input_pdf)
    total = convert(args.input_pdf, output_pptx, args.dpi)
    print(f"完成！輸出檔：{output_pptx}（共 {total} 頁）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
