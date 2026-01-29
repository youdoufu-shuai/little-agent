
import os
import sys
from core.doc_generator import DocumentGenerator

# Ensure we can import core
sys.path.append(os.getcwd())

def main():
    print("Starting updated PDF generation task...")
    
    anime_list = [
        {
            "title": "1. 我独自升级 (Solo Leveling) 第三季",
            "text": "类型：奇幻、动作 | 制作：A-1 Pictures。程肖宇的成神之路进入高潮，暗影军团的规模将再次突破观众的想象。",
            "image_url": "https://myanimelist.net/anime/58564/Solo_Leveling_Season_2__Arise_from_the_Shadow"
        },
        {
            "title": "2. 葬送的芙莉莲 (Frieren) 第二季",
            "text": "类型：剧情、奇幻 | 制作：Madhouse。在结束了一级魔法使考试后，芙莉莲一行人将深入北方大地，继续寻找灵魂栖息之地。",
            "image_url": "https://myanimelist.net/anime/56666/Sousou_no_Frieren_Season_2"
        },
        {
            "title": "3. 链锯人 (Chainsaw Man) 第二季：蕾洁篇/校园篇",
            "text": "类型：动作、黑暗奇幻 | 制作：MAPPA。电次的生活在遇到蕾洁后发生了翻天覆地的变化，电影级的制作水准将延续其暴力美学。",
            "image_url": "https://myanimelist.net/anime/57662/Chainsaw_Man_Movie__Reze-hen"
        },
        {
            "title": "4. 【我推的孩子】 (Oshi no Ko) 第三季",
            "text": "类型：偶像、悬疑 | 制作：动画工房。复仇计划进入收官阶段，演艺圈的黑暗面将彻底暴露在阳光下。",
            "image_url": "https://myanimelist.net/anime/59232/Oshi_no_Ko_3rd_Season"
        },
        {
            "title": "5. 怪兽8号 (Kaiju No. 8) 第二季",
            "text": "类型：科幻、战斗 | 制作：Production I.G。日比野卡夫卡与防卫队的命运交织，新的类人怪兽带来前所未有的生存危机。",
            "image_url": "https://myanimelist.net/anime/59247/Kaijuu_8-gou_2nd_Season"
        }
    ]

    anime_list_part2 = [
        {
            "title": "6. 极乐街 (Gokurakugai)",
            "text": "类型：动作、奇幻 | 期待指数：★★★★★。这部备受期待的漫画改编作，将以其独特的画风重塑充满魅力的华丽战斗世界。",
            "image_url": "https://static.wikia.nocookie.net/gokurakugai/images/7/77/JP_Volume_1.png/revision/latest/scale-to-width-down/1200?cb=20230527161730"
        },
        {
            "title": "7. 神乐钵 (Kagurabachi)",
            "text": "类型：少年漫画、复仇 | 制作：期待中。作为《周刊少年Jump》的新贵，这部融合了日本刀与复仇元素的动画将成为年度黑马。",
            "image_url": "https://myanimelist.net/manga/162479/Kagurabachi"
        },
        {
            "title": "8. 药师少女的独语 第二季",
            "text": "类型：宫廷、推理 | 制作：OLM/TOHO。猫猫在后宫的解谜日常还在继续，更多复杂的阴谋与人物关系将浮出水面。",
            "image_url": "https://myanimelist.net/anime/58563/Kusuriya_no_Hitorigoto_Season_2"
        }
    ]

    content = []
    
    # Title
    content.append({"type": "heading", "level": 1, "text": "2026年1月新番导视推荐表"})
    content.append({"type": "paragraph", "text": " "}) # Spacer
    
    # Part 1
    for anime in anime_list:
        content.append({"type": "heading", "level": 2, "text": anime["title"]})
        if anime["image_url"]:
            content.append({"type": "image", "path": anime["image_url"], "width": 400})
        content.append({"type": "paragraph", "text": anime["text"]})
        content.append({"type": "paragraph", "text": " "})
    
    # Part 2
    for anime in anime_list_part2:
        content.append({"type": "heading", "level": 2, "text": anime["title"]})
        if anime["image_url"]:
            content.append({"type": "image", "path": anime["image_url"], "width": 400})
        content.append({"type": "paragraph", "text": anime["text"]})
        content.append({"type": "paragraph", "text": " "})

    print("Generating PDF...")
    try:
        # Generate PDF
        result_message = DocumentGenerator.generate("2026_Winter_Anime_List_v2", "pdf", content)
        print(result_message)
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
