import os
import re
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

def parse_rich_text(text):
    """마크다운 인라인 서식(링크, 코드, 굵게 등)을 노션 Rich Text로 변환"""
    rich_text = []
    # 정규식: 링크 > 코드 > 굵게 > 기울임 > 취소선
    pattern = re.compile(
        r'(?P<link>\[.*?\]\(.*?\))|'
        r'(?P<code>`[^`]+`)|'
        r'(?P<bold>\*\*.*?\*\*)|'
        r'(?P<italic>\*.*?\*)|'
        r'(?P<strikethrough>~~.*?~~)'
    )
    
    last_idx = 0
    for match in pattern.finditer(text):
        if match.start() > last_idx:
            rich_text.append({"text": {"content": text[last_idx:match.start()]}})
        
        group_type = match.lastgroup
        content = match.group()
        
        if group_type == 'link':
            m = re.match(r'\[(.*?)\]\((.*?)\)', content)
            if m:
                rich_text.append({"text": {"content": m.group(1), "link": {"url": m.group(2)}}})
        elif group_type == 'code':
            rich_text.append({"text": {"content": content[1:-1]}, "annotations": {"code": True}})
        elif group_type == 'bold':
            rich_text.append({"text": {"content": content[2:-2]}, "annotations": {"bold": True}})
        elif group_type == 'italic':
            rich_text.append({"text": {"content": content[1:-1]}, "annotations": {"italic": True}})
        elif group_type == 'strikethrough':
            rich_text.append({"text": {"content": content[2:-2]}, "annotations": {"strikethrough": True}})
            
        last_idx = match.end()
    
    if last_idx < len(text):
        rich_text.append({"text": {"content": text[last_idx:]}})
        
    return rich_text if rich_text else [{"text": {"content": ""}}]

def convert_to_blocks(markdown_text):
    """마크다운 전체 텍스트를 노션 블록 리스트로 변환"""
    lines = markdown_text.split('\n')
    blocks = []
    
    in_code_block = False
    code_content = []
    code_lang = "plain text"
    
    table_rows = []
    in_table = False

    for line in lines:
        raw_line = line.rstrip()
        stripped = raw_line.strip()

        # 1. 코드 블록 처리
        if stripped.startswith("```"):
            if in_code_block:
                blocks.append({
                    "object": "block", "type": "code",
                    "code": {"rich_text": [{"text": {"content": "\n".join(code_content)[:2000]}}], "language": code_lang}
                })
                in_code_block = False
                code_content = []
            else:
                in_code_block = True
                code_lang = stripped[3:].strip() or "plain text"
            continue
        
        if in_code_block:
            code_content.append(raw_line)
            continue

        if not stripped: continue

        # 2. 표 (Table) 처리
        if stripped.startswith("|"):
            # 구분선 체크 로직
            is_separator = True
            clean_chars = stripped.replace("|", "").replace(" ", "").replace("\t", "")
            if not clean_chars: 
                is_separator = False
            else:
                for char in clean_chars:
                    if char not in ['-', ':']:
                        is_separator = False
                        break
            
            if is_separator:
                continue

            row_content = stripped.strip("|")
            cells_text = row_content.split("|")
            cells = [parse_rich_text(c.strip()) for c in cells_text]
            table_rows.append(cells)
            in_table = True
            continue
        
        if in_table and not stripped.startswith("|"):
            _append_table_block(blocks, table_rows)
            table_rows = []
            in_table = False

        # 3. 구분선(Divider) 처리 
        if stripped == "---" or stripped == "***" or stripped == "___":
            blocks.append({"object": "block", "type": "divider", "divider": {}})
            continue

        # 4. 일반 블록들
        if stripped.startswith("# "): continue
        elif stripped.startswith("## "):
            blocks.append({"object": "block", "type": "heading_2", "heading_2": {"rich_text": parse_rich_text(stripped[3:])}})
        elif stripped.startswith("### "):
            blocks.append({"object": "block", "type": "heading_3", "heading_3": {"rich_text": parse_rich_text(stripped[4:])}})
        
        # 인용구 -> 콜아웃 변환
        elif stripped.startswith("> "):
            blocks.append({
                "object": "block", 
                "type": "callout", 
                "callout": {
                    "rich_text": parse_rich_text(stripped[2:]),
                    "icon": {"emoji": "💡"}
                }
            })
            
        elif stripped.startswith("- [ ] "):
            blocks.append({"object": "block", "type": "to_do", "to_do": {"rich_text": parse_rich_text(stripped[6:]), "checked": False}})
        elif stripped.startswith("- [x] "):
            blocks.append({"object": "block", "type": "to_do", "to_do": {"rich_text": parse_rich_text(stripped[6:]), "checked": True}})
        elif stripped.startswith("- ") or stripped.startswith("* "):
            blocks.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": parse_rich_text(stripped[2:])}})
        else:
            blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": parse_rich_text(stripped)}})
    
    if in_table and table_rows:
        _append_table_block(blocks, table_rows)
        
    return blocks

def _append_table_block(blocks, raw_rows):
    """표 행 길이 맞춤 및 블록 추가"""
    if not raw_rows: return
    
    max_cols = max(len(row) for row in raw_rows)
    
    final_rows = []
    for row in raw_rows:
        while len(row) < max_cols:
            row.append([{"text": {"content": ""}}])
        final_rows.append({"type": "table_row", "table_row": {"cells": row}})

    blocks.append({
        "object": "block", 
        "type": "table", 
        "table": {
            "table_width": max_cols, 
            "has_column_header": True, 
            "children": final_rows
        }
    })

def upload_page(page_title, markdown_content):
    token = os.getenv("NOTION_TOKEN")
    page_id = os.getenv("NOTION_PAGE_ID")
    
    if not token or not page_id:
        print("❌ Notion 토큰/페이지ID 설정 확인 필요")
        return

    notion = Client(auth=token)
    blocks = convert_to_blocks(markdown_content)

    print(f"노션 페이지 '{page_title}' 생성 중...")
    try:
        new_page = notion.pages.create(
            parent={"page_id": page_id},
            properties={"title": [{"text": {"content": page_title}}]}
        )
        
        for i in range(0, len(blocks), 100):
            notion.blocks.children.append(block_id=new_page["id"], children=blocks[i:i+100])
            print(f"   ... 블록 업로드 중 ({min(i+100, len(blocks))}/{len(blocks)})")
            
        print(f"✅ 업로드 완료! URL: {new_page['url']}")
    except Exception as e:
        print(f"❌ 노션 업로드 실패: {e}")
        