"""
TBX (TermBase eXchange) 格式转换器

支持 TBX Basic 格式的导入导出，这是术语库交换的国际标准格式 (ISO 30042)
"""

import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Optional


class TBXConverter:
    """TBX 格式转换器"""

    # TBX 命名空间
    TBX_NS = "urn:iso:std:iso:30042:ed-2"
    TBX_PREFIX = "tbx"

    # 内部术语格式
    # {
    #     "src": "源语言术语",
    #     "dst": "目标语言术语",
    #     "info": "备注/类型"
    # }

    @staticmethod
    def export_to_tbx(terms: List[Dict], output_path: str, source_lang: str = "en", target_lang: str = "zh", 
                      collection_name: str = "AiNiee Glossary") -> bool:
        """
        将内部术语格式导出为 TBX XML 格式

        Args:
            terms: 术语列表 [{"src": "...", "dst": "...", "info": "..."}]
            output_path: 输出文件路径
            source_lang: 源语言代码 (如 "en")
            target_lang: 目标语言代码 (如 "zh")
            collection_name: 术语库名称

        Returns:
            bool: 是否成功导出
        """
        if not terms:
            return False

        try:
            # 创建根元素
            root = ET.Element("martif")
            root.set("type", "TBX-Basic")
            root.set("{http://www.w3.org/XML/1998/namespace}lang", source_lang)

            # 添加 XML 声明
            # 注意: ElementTree 不直接支持声明，需要在写入时添加

            # martifHeader
            martif_header = ET.SubElement(root, "martifHeader")
            file_desc = ET.SubElement(martif_header, "fileDesc")
            title_stmt = ET.SubElement(file_desc, "titleStmt")
            title = ET.SubElement(title_stmt, "title")
            title.text = collection_name

            revision_desc = ET.SubElement(file_desc, "revisionDesc")
            change = ET.SubElement(revision_desc, "change")
            change.set("changeType", "Created")
            change_date = ET.SubElement(change, "date")
            change_date.set("{http://www.w3.org/XML/1998/namespace}lang", "en")
            change_date.text = datetime.now().strftime("%Y-%m-%d")

            # text/body
            text_elem = ET.SubElement(root, "text")
            body = ET.SubElement(text_elem, "body")

            # 添加术语条目
            for idx, term in enumerate(terms):
                src = term.get("src", "")
                dst = term.get("dst", "")
                info = term.get("info", "")

                if not src:
                    continue

                term_entry = ET.SubElement(body, "termEntry")
                term_entry.set("id", f"term-{idx + 1:04d}")

                # 添加描述（类型信息）
                if info:
                    descrip = ET.SubElement(term_entry, "descrip")
                    descrip.set("type", "subjectField")
                    descrip.text = info

                # 源语言
                lang_set_src = ET.SubElement(term_entry, "langSet")
                lang_set_src.set("{http://www.w3.org/XML/1998/namespace}lang", source_lang)

                tig_src = ET.SubElement(lang_set_src, "tig")
                term_src = ET.SubElement(tig_src, "term")
                term_src.text = src

                # 目标语言
                if dst:
                    lang_set_dst = ET.SubElement(term_entry, "langSet")
                    lang_set_dst.set("{http://www.w3.org/XML/1998/namespace}lang", target_lang)

                    tig_dst = ET.SubElement(lang_set_dst, "tig")
                    term_dst = ET.SubElement(tig_dst, "term")
                    term_dst.text = dst

                    # 添加术语类型
                    term_note = ET.SubElement(tig_dst, "termNote")
                    term_note.set("type", "termType")
                    term_note.text = "translatedTerm"

            # 写入文件
            tree = ET.ElementTree(root)
            
            # 格式化输出
            indent_xml(root)
            
            # 添加 XML 声明和 DOCTYPE
            with open(output_path, "w", encoding="utf-8") as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<!DOCTYPE martif SYSTEM "TBXBasiccoreStructV02.dtd">\n')
                tree.write(f, encoding="unicode", xml_declaration=False)

            return True

        except Exception as e:
            print(f"导出 TBX 失败: {e}")
            return False

    @staticmethod
    def import_from_tbx(tbx_path: str) -> Optional[List[Dict]]:
        """
        从 TBX XML 文件导入术语

        Args:
            tbx_path: TBX 文件路径

        Returns:
            List[Dict]: 术语列表 [{"src": "...", "dst": "...", "info": "..."}] 或 None
        """
        if not os.path.exists(tbx_path):
            return None

        try:
            tree = ET.parse(tbx_path)
            root = tree.getroot()

            terms = []

            # 处理命名空间
            namespace = {"tbx": "urn:iso:std:iso:30042:ed-2"}

            # 查找所有 termEntry
            for term_entry in root.iter():
                if term_entry.tag.endswith("termEntry"):
                    term_id = term_entry.get("id", "")
                    
                    # 收集语言条目
                    lang_terms = {}
                    term_info = ""

                    for child in term_entry:
                        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

                        if tag == "descrip":
                            term_info = child.text or ""

                        elif tag == "langSet":
                            lang = child.get("{http://www.w3.org/XML/1998/namespace}lang", "")
                            
                            # 查找术语
                            for tig in child:
                                tig_tag = tig.tag.split("}")[-1] if "}" in tig.tag else tig.tag
                                
                                if tig_tag == "tig":
                                    term_text = ""
                                    term_type = ""
                                    
                                    for term_child in tig:
                                        term_child_tag = term_child.tag.split("}")[-1] if "}" in term_child.tag else term_child.tag
                                        
                                        if term_child_tag == "term":
                                            term_text = term_child.text or ""
                                        elif term_child_tag == "termNote" and term_child.get("type") == "termType":
                                            term_type = term_child.text or ""
                                    
                                    if term_text:
                                        lang_terms[lang] = {
                                            "term": term_text,
                                            "type": term_type
                                        }

                    # 解析源语言和目标语言
                    if lang_terms:
                        # 尝试确定源语言和目标语言
                        # 假设第一个语言是源语言，第二个是目标语言
                        lang_codes = list(lang_terms.keys())
                        
                        if len(lang_codes) >= 2:
                            src_lang = lang_codes[0]
                            dst_lang = lang_codes[1]
                            
                            src_term = lang_terms[src_lang]["term"]
                            dst_term = lang_terms[dst_lang]["term"]
                            
                            terms.append({
                                "src": src_term,
                                "dst": dst_term,
                                "info": term_info
                            })
                        elif len(lang_codes) == 1:
                            # 只有一种语言，尝试判断是源还是目标
                            single_lang = lang_codes[0]
                            single_term = lang_terms[single_lang]["term"]
                            
                            # 默认作为源语言
                            terms.append({
                                "src": single_term,
                                "dst": "",
                                "info": term_info
                            })

            return terms if terms else None

        except Exception as e:
            print(f"导入 TBX 失败: {e}")
            return None

    @staticmethod
    def detect_language_code(lang_name: str) -> str:
        """将语言名称转换为 ISO 639-1 代码"""
        lang_map = {
            "中文": "zh-CN",
            "chinese": "zh-CN",
            "英语": "en",
            "english": "en",
            "日语": "ja",
            "japanese": "ja",
            "韩语": "ko",
            "korean": "ko",
            "法语": "fr",
            "french": "fr",
            "德语": "de",
            "german": "de",
            "西班牙语": "es",
            "spanish": "es",
            "俄语": "ru",
            "russian": "ru",
            "葡萄牙语": "pt",
            "portuguese": "pt",
            "意大利语": "it",
            "italian": "it",
            "阿拉伯语": "ar",
            "arabic": "ar",
        }
        
        return lang_map.get(lang_name.lower(), lang_name)


def indent_xml(elem, level=0):
    """格式化 XML 缩进"""
    indent = "\n" + "  " * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
        for child in elem:
            indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent


def convert_json_to_tbx(input_json: str, output_tbx: str, source_lang: str = "en", 
                        target_lang: str = "zh") -> bool:
    """
    便捷函数：将 JSON 术语文件转换为 TBX 格式

    Args:
        input_json: 输入 JSON 文件路径
        output_tbx: 输出 TBX 文件路径
        source_lang: 源语言代码
        target_lang: 目标语言代码

    Returns:
        bool: 是否转换成功
    """
    try:
        with open(input_json, 'r', encoding='utf-8') as f:
            terms = json.load(f)
        
        return TBXConverter.export_to_tbx(terms, output_tbx, source_lang, target_lang)
    except Exception as e:
        print(f"转换失败: {e}")
        return False


def convert_tbx_to_json(input_tbx: str, output_json: str) -> bool:
    """
    便捷函数：将 TBX 术语文件转换为 JSON 格式

    Args:
        input_tbx: 输入 TBX 文件路径
        output_json: 输出 JSON 文件路径

    Returns:
        bool: 是否转换成功
    """
    try:
        terms = TBXConverter.import_from_tbx(input_tbx)
        
        if terms is None:
            return False
        
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(terms, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"转换失败: {e}")
        return False


if __name__ == "__main__":
    # 测试代码
    print("TBX 转换器测试")
    print("=" * 50)
    
    # 测试导出
    test_terms = [
        {"src": "software", "dst": "软件", "info": "计算机"},
        {"src": "hardware", "dst": "硬件", "info": "计算机"},
        {"src": "AI", "dst": "人工智能", "info": "技术"},
    ]
    
    test_tbx_path = "/tmp/test_glossary.tbx"
    test_json_path = "/tmp/test_glossary.json"
    
    # 导出测试
    success = TBXConverter.export_to_tbx(test_terms, test_tbx_path, "en", "zh", "Test Glossary")
    print(f"导出测试: {'成功' if success else '失败'}")
    
    if success:
        # 读取并显示导出的内容
        with open(test_tbx_path, 'r', encoding='utf-8') as f:
            print("\n导出的 TBX 内容:")
            print(f.read()[:500])
    
    # 导入测试
    imported_terms = TBXConverter.import_from_tbx(test_tbx_path)
    print(f"\n导入测试: {'成功' if imported_terms else '失败'}")
    if imported_terms:
        print(f"导入的术语数量: {len(imported_terms)}")
        print(f"导入的术语: {imported_terms}")
