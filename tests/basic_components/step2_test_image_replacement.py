"""
【测试步骤 2】Report 图片替换 - _replace_image_path

功能说明:
    ReportGenerator._replace_image_path 负责将报告中的图片占位符
    （如 @import "营收趋势图"）替换为实际的 Markdown 图片引用。

测试目标:
    1. 理解占位符的格式
    2. 观察语义匹配过程
    3. 验证替换后的 Markdown 格式

运行方式:
    python tests/basic_components/step2_test_image_replacement.py
"""
import asyncio
import os
import sys
from pathlib import Path

root = str(Path(__file__).resolve().parents[2])
sys.path.append(root)

from src.config import Config
from src.memory import Memory
from src.agents.report_generator.report_generator import ReportGenerator
from src.agents.report_generator.report_class import Report, Section
from src.agents.data_analyzer.data_analyzer import AnalysisResult


def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def create_mock_analysis_results(config):
    """创建模拟的分析结果"""
    print_section("准备 Mock 数据")
    
    # 创建临时图片目录
    image_dir = os.path.join(config.working_dir, "mock_images")
    os.makedirs(image_dir, exist_ok=True)
    
    # 创建占位图片文件（1x1 像素的 PNG）
    png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    
    mock_images = {
        "revenue_trend.png": "Revenue Growth Trend Chart 2020-2024",
        "profit_margin.png": "Profit Margin Analysis Bar Chart",
        "market_share.png": "Market Share Distribution Pie Chart"
    }
    
    print("\n【创建】模拟图片文件:")
    for filename, description in mock_images.items():
        filepath = os.path.join(image_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(png_header)
        print(f"  ✓ {filename}")
        print(f"    描述: {description}")
    
    # 创建 AnalysisResult
    analysis_result = AnalysisResult(
        title="财务分析",
        content="分析内容...",
        image_save_dir=image_dir,
        chart_name_mapping={
            desc: filename for filename, desc in mock_images.items()
        },
        chart_name_description_mapping={
            desc: desc for desc in mock_images.values()
        }
    )
    
    print(f"\n【输出】AnalysisResult 对象:")
    print(f"  - image_save_dir: {analysis_result.image_save_dir}")
    print(f"  - chart_name_mapping: {len(analysis_result.chart_name_mapping)} 个图表")
    
    return [analysis_result]


def create_mock_report():
    """创建带占位符的测试报告"""
    print_section("创建测试报告")
    
    # 报告内容（包含占位符）
    content = """
## 财务表现分析

公司在过去五年实现了稳健增长。

@import "营收趋势图表"

从上图可以看出，营业收入呈现逐年上升趋势。同时，盈利能力也在持续改善。

@import "利润率分析"

市场份额方面，公司在细分领域保持领先地位。

@import "市场占有率饼图"

综上所述，公司财务状况良好。
"""
    
    print("\n【输入】原始报告内容:")
    print("-" * 70)
    print(content)
    print("-" * 70)
    
    # 创建 Report 对象
    report = Report("# 测试报告\n## 财务表现分析")
    
    # 模拟填充内容
    report.sections[0]._content = [content]
    
    print("\n【识别】找到的占位符:")
    import re
    placeholders = re.findall(r'@import\s*".*?"', content)
    for i, placeholder in enumerate(placeholders, 1):
        print(f"  {i}. {placeholder}")
    
    return report


async def test_image_replacement():
    """主测试流程"""
    print("\n" + "🧪 " + "="*68)
    print("  图片占位符替换测试")
    print("="*70)
    print("\n说明:")
    print("  _replace_image_path 的工作流程:")
    print("  1. 从 AnalysisResult 中提取图片标题和路径")
    print("  2. 为所有图片标题构建语义索引")
    print("  3. 对报告中的每个 @import 占位符执行语义搜索")
    print("  4. 将占位符替换为 Markdown 图片引用")
    print("="*70)
    
    # 1. 准备配置和 Memory
    config = Config(config_file_path='tests/my_config.yaml')
    memory = Memory(config=config)
    
    # 2. 创建 Mock 数据
    analysis_results = create_mock_analysis_results(config)
    for result in analysis_results:
        memory.add_data(result)
    
    # 3. 创建测试报告
    report = create_mock_report()
    
    # 4. 创建 ReportGenerator
    print_section("执行图片替换")
    
    generator = ReportGenerator(
        config=config,
        memory=memory,
        use_llm_name=os.getenv('DS_MODEL_NAME', 'deepseek-chat'),
        use_embedding_name=os.getenv('EMBEDDING_MODEL_NAME', 'qwen3-embedding:0.6b')
    )
    
    print("\n【处理中】调用 _replace_image_path...")
    
    # 执行替换
    result_report = await generator._replace_image_path(report)
    
    # 5. 查看结果
    print_section("替换结果")
    
    final_content = result_report.sections[0]._content[0]
    
    print("\n【输出】替换后的报告内容:")
    print("-" * 70)
    print(final_content)
    print("-" * 70)
    
    # 6. 验证
    print_section("验证结果")
    
    import re
    remaining_placeholders = re.findall(r'@import\s*".*?"', final_content)
    markdown_images = re.findall(r'!\[.*?\]\(.*?\)', final_content)
    
    print("\n【检查】占位符替换情况:")
    print(f"  - 剩余占位符: {len(remaining_placeholders)} 个")
    if remaining_placeholders:
        for placeholder in remaining_placeholders:
            print(f"    ⚠️  未替换: {placeholder}")
    
    print(f"\n  - 生成的图片引用: {len(markdown_images)} 个")
    for i, img_ref in enumerate(markdown_images, 1):
        print(f"    {i}. {img_ref}")
    
    if len(remaining_placeholders) == 0 and len(markdown_images) > 0:
        print("\n  ✅ 所有占位符已成功替换为图片引用！")
    else:
        print("\n  ⚠️  部分占位符未被替换")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(test_image_replacement())
