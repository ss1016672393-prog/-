#!/usr/bin/env python3
"""
CFH 设计中心 - 多通道数据同步脚本
====================================
从 Figma REST API 拉取多个 Project 的文件，
按职能分类输出为多通道 data.js 格式（供 index.html 多 Tab 使用）。

用法：
  python sync.py
"""

import json
import os
import re
import sys
import io
import argparse
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ============================================================
# 配置区
# ============================================================
FIGMA_TOKEN = "figd_nRfRUF2FUW4t9swD8KqmvIFJg-uuZvPbuhbLQ0JB"
TEAM_ID = "1359372906387435078"   # CFH 团队 ID
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "data.js")
CST = timezone(timedelta(hours=8))

# ============================================================
# 职能通道定义 — 每个 channel 对应一个 Tab
# ============================================================
CHANNELS = {
    "ixd": {
        "title": "CFH交互稿索引",
        "subtitle": "Figma 交互设计文档",
        # 交互稿的 Project IDs
        "project_ids": ["231182587"],
        # 分类规则（和原来一样）
        "keywords": {
            # ===== A. 通用 =====
            "CFH": ("规范", "A01"),
            "组结套": ("规范", "A01"),
            "四合一模板": ("规范", "A01"),
            "通用规范": ("规范", "A01"),
            "通用界面": ("规范", "A01"),
            "控件": ("规范", "A01"),
            "模板": ("规范", "A01"),
            "版本验收": ("版本跟进", "A02"),
            "验收比照": ("版本跟进", "A02"),
            "专项验收": ("版本跟进", "A02"),
            "版本进展": ("版本跟进", "A02"),
            "版本": ("版本跟进", "A02"),
            "索引": ("组内相关", "A03"),
            "UI PV": ("组内相关", "A03"),
            "PV设计": ("组内相关", "A03"),
            "世界观": ("世界观相关", "A04"),
            # ===== B. 局外 =====
            "登录流程": ("主流程", "B01"), "登录": ("主流程", "B01"),
            "新手引导": ("主流程", "B01"), "Loading": ("主流程", "B01"),
            "大厅": ("主流程", "B01"), "匹配": ("主流程", "B01"),
            "升级": ("主流程", "B01"), "开局流程": ("主流程", "B01"),
            "结算": ("主流程", "B01"), "模式选择": ("主流程", "B01"),
            "自定义房间": ("主流程", "B01"), "设置": ("主流程", "B01"),
            "角色系统": ("角色", "B02"), "角色招募": ("角色", "B02"),
            "资料卡": ("角色", "B02"), "个人主页": ("角色", "B02"),
            "玩家资料卡": ("角色", "B02"),
            "怪物HUD": ("怪物/宠物", "B04"), "怪物扮演": ("怪物/宠物", "B04"),
            "社交系统": ("社交", "B05"), "社交邀请": ("社交", "B05"),
            "聊天系统": ("社交", "B05"), "半屏好友": ("社交", "B05"),
            "好友列表": ("社交", "B05"), "小队": ("社交", "B05"),
            "通讯系统": ("社交", "B05"), "邮件系统": ("社交", "B05"),
            "图鉴系统": ("通用系统", "B06"), "理智值系统": ("通用系统", "B06"),
            "标记系统": ("通用系统", "B06"), "公告": ("通用系统", "B06"),
            "字幕": ("通用系统", "B06"), "系统说明": ("通用系统", "B06"),
            "排位系统": ("通用系统", "B06"), "赛季等级": ("通用系统", "B06"),
            "任务（神秘少女": ("玩法相关", "B07"),
            "活动系统": ("玩法相关", "B07"), "活跃系统": ("玩法相关", "B07"),
            "派遣": ("玩法相关", "B07"),
            "商城": ("商业化", "B08"), "商业化": ("商业化", "B08"),
            "商人": ("商业化", "B08"), "交易行": ("商业化", "B08"),
            "crafting": ("商业化", "B08"),
            # ===== C. 局内 =====
            "局内玩法规则": ("主要玩法", "C01"), "局内聊天": ("主要玩法", "C01"),
            "局内靶场": ("主要玩法", "C01"), "局内死亡倒地": ("主要玩法", "C01"),
            "局内倒地观战": ("主要玩法", "C01"), "局内角色掠夺": ("主要玩法", "C01"),
            "BOSS召唤": ("主要玩法", "C01"), "BOSS讨伐": ("主要玩法", "C01"),
            "地图": ("主要玩法", "C01"), "线索": ("主要玩法", "C01"),
            "人类HUD": ("人类HUD", "C02"),
            "人类HUD-准星": ("人类HUD", "C02"), "人类HUD-命中": ("人类HUD", "C02"),
            "人类HUD-屏幕效果": ("人类HUD", "C02"),
            "人类HUD-技能装备栏": ("人类HUD", "C02"),
            "人类HUD-血条": ("人类HUD", "C02"), "人类HUD-轮盘": ("人类HUD", "C02"),
            "人类HUD-通用提示": ("人类HUD", "C02"),
            "人类HUD-队友状态": ("人类HUD", "C02"), "人类HUD-局内": ("人类HUD", "C02"),
            "轮盘": ("通用小部件", "C04"),
            "局内商店": ("局内系统", "C05"), "局内外背包": ("局内系统", "C05"),
            "局内背包": ("局内系统", "C05"), "背包配装": ("局内系统", "C05"),
            "仓库": ("局内系统", "C05"), "局内技能教学": ("局内系统", "C05"),
            "局内HUD-主机适配": ("特殊HUD", "C06"),
            # ===== D. 主机相关 =====
            "主机适配": ("局内适配", "D01"), "主机": ("局内适配", "D01"),
            "底层规则": ("底层规则", "D02"),
        },
        "section_map": {
            "A": {"name": "通用", "order": 0},
            "B": {"name": "局外", "order": 1},
            "C": {"name": "局内", "order": 2},
            "D": {"name": "主机相关", "order": 3},
        },
    },

    "refactor": {
        "title": "CFH重构落地",
        "subtitle": "重构与落地跟踪",
        "project_ids": ["243822260"],
        "keywords": {
            "性能": ("性能优化", "R01"), "优化": ("性能优化", "R01"),
            "双帧": ("性能优化", "R01"),
            "UMG": ("工具/流程", "R02"), "工具": ("工具/流程", "R02"),
            "周报": ("周报/汇报", "R03"), "汇报": ("周报/汇报", "R03"),
            "排期": ("周报/汇报", "R03"), "资源": ("资源整理", "R04"),
        },
        "section_map": {
            "R": {"name": "重构跟踪", "order": 1},
        },
    },

    "weekly": {
        "title": "CFH概念推导 & 周报",
        "subtitle": "概念推导、周报与汇报材料",
        "project_ids": ["222913532", "222913092"],  # CFBH概念推导 + CFH设计周报
        "keywords": {
            "概念": ("概念推导", "W01"),
            "推导": ("概念推导", "W01"),
            "KOTO": ("概念推导", "W01"),
            "PARKI": ("概念推导", "W01"),
            "PC主机": ("概念推导", "W01"),
            "视觉BCD": ("视觉推导", "W02"),
            "HUD专题": ("视觉推导", "W02"),
            "周报": ("周报", "W03"),
            "月报": ("周报", "W03"),
            "例会": ("周报", "W03"),
        },
        "section_map": {
            "W": {"name": "推导&周报", "order": 1},
        },
    },
}

DEFAULT_CATEGORY = "未分类"
DEFAULT_KEY = "Z99"


def classify_file(file_name, keywords):
    """按关键词分类"""
    name_lower = file_name.lower()
    for kw, (cat_name, cat_key) in keywords.items():
        if kw.lower() in name_lower or kw in file_name:
            return cat_name, cat_key
    return DEFAULT_CATEGORY, DEFAULT_KEY


def get_section(key, section_map):
    """从排序 key 提取板块信息"""
    prefix = key[0] if key else "Z"
    return section_map.get(prefix, {"name": "其他", "order": 9})


def api_get(url):
    req = Request(url)
    req.add_header("X-Figma-Token", FIGMA_TOKEN)
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        print(f"  API 错误 {e.code}: {url}")
        raise


def get_project_files(project_id):
    """拉取一个项目的所有文件（支持分页）"""
    url = f"https://api.figma.com/v1/projects/{project_id}/files"
    result = api_get(url)
    files = list(result.get("files", []))
    while result.get("cursor"):
        result = api_get(f"{url}?cursor={result['cursor']}")
        files.extend(result.get("files", []))
    return files


def guess_status(last_modified_str):
    try:
        dt = datetime.fromisoformat(last_modified_str.replace("Z", "+00:00"))
        delta = (datetime.now(CST) - dt.astimezone(CST)).days
        return "active" if delta <= 7 else "review" if delta <= 30 else "stable"
    except Exception:
        return "unknown"


def build_channel(channel_key, channel_config):
    """构建单个通道的数据"""
    keywords = channel_config["keywords"]
    section_map = channel_config["section_map"]
    all_docs = []

    for proj_id in channel_config["project_ids"]:
        try:
            files = get_project_files(proj_id)
        except Exception as e:
            print(f"  ⚠️ 项目 {proj_id} 拉取失败: {e}")
            continue

        for i, f in enumerate(files):
            name = f.get("name", "未命名")
            category, category_key = classify_file(name, keywords)
            section_info = get_section(category_key, section_map)

            doc = {
                "name": name,
                "url": f"https://www.figma.com/file/{f.get('key', '')}",
                "category": category,
                "categoryKey": category_key,
                "section": section_info["name"],
                "sectionOrder": section_info["order"],
                "status": guess_status(f.get("last_modified", "")),
                "lastModified": f.get("last_modified", ""),
            }
            all_docs.append(doc)

    # 排序
    all_docs.sort(key=lambda x: (x["sectionOrder"], x["categoryKey"], x["name"]))

    # 统计
    category_stats = {}
    section_stats = {}
    for d in all_docs:
        cat = d["category"]
        sec = d["section"]
        category_stats[cat] = category_stats.get(cat, 0) + 1
        if sec not in section_stats:
            section_stats[sec] = {}
        section_stats[sec][cat] = section_stats[sec].get(cat, 0) + 1

    # 构建有序 sections
    sections_ordered = []
    for prefix in sorted(section_map.keys(), key=lambda k: section_map[k]["order"]):
        sec_name = section_map[prefix]["name"]
        if sec_name in section_stats:
            sections_ordered.append({
                "name": sec_name,
                "categories": [
                    {"name": c, "count": count}
                    for c, count in sorted(section_stats[sec_name].items())
                ],
            })

    return {
        "title": channel_config["title"],
        "subtitle": channel_config["subtitle"],
        "updatedAt": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S"),
        "totalDocuments": len(all_docs),
        "sections": sections_ordered,
        "categories": [{"name": k, "count": v} for k, v in sorted(category_stats.items())],
        "documents": all_docs,
    }


def sync():
    print("=" * 55)
    print("  CFH 设计中心 - 多通道数据同步")
    print("=" * 55)
    print(f"Team ID: {TEAM_ID}")
    print(f"Channels: {', '.join(CHANNELS.keys())}\n")

    output_channels = {}

    for ch_key, ch_config in CHANNELS.items():
        print(f"[{ch_key.upper()}] {ch_config['title']}")
        print(f"  Projects: {ch_config['project_ids']}")

        ch_data = build_channel(ch_key, ch_config)
        output_channels[ch_key] = ch_data

        print(f"  ✅ {ch_data['totalDocuments']} 个文件")
        for sec in ch_data["sections"]:
            cats_str = ", ".join([f"{c['name']}({c['count']})" for c in sec["categories"]])
            print(f"     [{sec['name']}] {cats_str}")
        print()

    # 写入 data.js
    now = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S")
    total_all = sum(c["totalDocuments"] for c in output_channels.values())

    js_content = (
        "// CFH 设计中心索引数据 | 多职能通道格式\n"
        f"// 更新时间: {now}\n"
        f"// 总计: {total_all} 个文件 | {len(output_channels)} 个通道\n\n"
        "var DOC_DATA = {\n"
        '  "channels": {\n'
    )

    for idx, (ch_key, ch_data) in enumerate(output_channels.items()):
        comma = "," if idx < len(output_channels) - 1 else ""
        js_content += f'    "{ch_key}": {json.dumps(ch_data, ensure_ascii=False, indent=6)}{comma}\n'

    js_content += "  }\n};\n"

    with open(OUTPUT_FILE, "w", encoding="utf-8") as fp:
        fp.write(js_content)

    # 结果摘要
    print("=" * 55)
    print("  同步完成!")
    print(f"  总文件数: {total_all}")
    for ch_key, ch_data in output_channels.items():
        print(f"  • [{ch_key}] {ch_data['title']}: {ch_data['totalDocuments']} 文件")
    print(f"  输出文件: {OUTPUT_FILE}")
    print("=" * 55)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CFH 设计中心多通道数据同步")
    parser.add_argument("--token", default=FIGMA_TOKEN)
    parser.add_argument("--team", default=TEAM_ID)
    args = parser.parse_args()

    FIGMA_TOKEN = args.token
    TEAM_ID = args.team

    sync()
