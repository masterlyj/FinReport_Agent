"""
【测试步骤 3】引用替换 - _add_reference

功能说明:
    ReportGenerator._add_reference 负责：
    1. 将报告中的 [Source: xxx] 占位符替换为数字引用
    2. 在报告末尾添加参考文献列表

测试目标:
    1. 理解引用占位符的格式
    2. 观察语义匹配数据源的过程
    3. 验证参考文献列表的生成

运行方式:
    python tests/basic_components/step3_test_reference_replacement.py
"""
import asyncio
import os
import sys
from pathlib import Path
import pandas as pd

root = str(Path(__file__).resolve().parents[2])
sys.path.append(root)

from src.config import Config
from src.memory import Memory
from src.agents.report_generator.report_generator import ReportGenerator
from src.agents.report_generator.report_class import Report, Section
from src.tools import ToolResult


def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def create_mock_data_sources(memory):
    """创建模拟的数据源"""
    print_section("准备 Mock 数据源")
    
    # Mock 数据源 1: 财务报表
    financial_data = pd.DataFrame({
        'Year': [2020, 2021, 2022, 2023],
        'Revenue': [100, 120, 150, 180],
        'Profit': [10, 12, 15, 20]
    })
    
    data_sources = [
        ToolResult(
            name="比亚迪 年度财务报表",
            description="2020-2023年关键财务指标，包含营收、利润等数据",
            data=financial_data,
            source="东方财富网"
        ),
        ToolResult(
            name="比亚迪 公司年报",
            description="2023年年度报告完整版，包含经营分析和财务数据",
            data="年报内容摘要...",
            source="公司官网 PDF"
        ),
        ToolResult(
            name="新能源汽车 行业数据",
            description="2023年新能源汽车行业整体市场规模和增长率数据",
            data={"market_size": 800, "growth_rate": 0.35},
            source="艾瑞咨询行业报告"
        ),
        ToolResult(
            name="比亚迪 股东结构",
            description="最新股东持股比例和变动情况",
            data="股东结构数据...",
            source="同花顺财经"
        )
    ]
    
    print("\n【创建】模拟数据源:")
    for i, ds in enumerate(data_sources, 1):
        memory.add_data(ds)
        print(f"  {i}. {ds.name}")
        print(f"     描述: {ds.description}")
        print(f"     来源: {ds.source}")
    
    print(f"\n【输出】Memory 中的数据源数量: {len(memory.data)}")
    
    return data_sources


def create_mock_report_with_citations():
    """创建带引用占位符的测试报告"""
    print_section("创建测试报告")
    
    content = """
## 财务状况分析

### 营收表现

公司在2023年实现营业收入180亿元[Source: 财务报表数据]，
相比2020年的100亿元实现大幅增长。年复合增长率达到21.7%[Source: 年报分析]。

### 盈利能力

净利润从2020年的10亿元增长至2023年的20亿元[Source: 财务指标]，
利润率保持稳定上升趋势。

### 行业地位

在新能源汽车行业中，市场规模达到800亿[Source: 行业报告]，
公司保持领先地位[Source: 股东结构分析]。
"""
    
    print("\n【输入】原始报告内容:")
    print("-" * 70)
    print(content)
    print("-" * 70)
    
    # 识别引用占位符
    import re
    citations = re.findall(r'\[Source:\s*(.*?)\]', content)
    
    print("\n【识别】找到的引用占位符:")
    for i, citation in enumerate(citations, 1):
        print(f"  {i}. [Source: {citation}]")
    
    # 创建 Report 对象
    report = Report("# 测试报告")
    section = Section("财务状况分析", content)
    section._content = [content]
    report.sections = [section]
    
    return report


async def test_reference_replacement():
    """主测试流程"""
    print("\n" + "🧪 " + "="*68)
    print("  引用替换测试")
    print("="*70)
    print("\n说明:")
    print("  _add_reference 的工作流程:")
    print("  1. 从 Memory 中获取所有数据源")
    print("  2. 为数据源的名称+描述构建语义索引")
    print("  3. 对报告中的每个 [Source: xxx] 占位符执行语义搜索")
    print("  4. 替换为数字引用（如 [1,2]）")
    print("  5. 在报告末尾添加参考文献列表")
    print("="*70)
    
    # 1. 准备配置和 Memory
    config = Config(config_file_path='tests/my_config.yaml')
    memory = Memory(config=config)
    
    # 2. 创建 Mock 数据源
    data_sources = create_mock_data_sources(memory)
    
    # 3. 创建测试报告
    report = create_mock_report_with_citations()
    
    # 4. 创建 ReportGenerator
    print_section("执行引用替换")
    
    generator = ReportGenerator(
        config=config,
        memory=memory,
        use_llm_name=os.getenv('DS_MODEL_NAME', 'deepseek-chat'),
        use_embedding_name=os.getenv('EMBEDDING_MODEL_NAME', 'qwen3-embedding:0.6b')
    )
    
    print("\n【处理中】调用 _add_reference...")
    print("  - 构建数据源索引")
    print("  - 执行语义搜索")
    print("  - 替换占位符")
    print("  - 生成参考文献")
    
    # 执行替换
    result_report = await generator._add_reference(report)
    
    # 5. 查看结果
    print_section("替换结果")
    
    final_content = result_report.content
    
    print("\n【输出】替换后的完整报告:")
    print("-" * 70)
    print(final_content)
    print("-" * 70)
    
    # 6. 验证
    print_section("验证结果")
    
    import re
    
    # 检查占位符
    remaining_citations = re.findall(r'\[Source:\s*(.*?)\]', final_content)
    
    # 检查数字引用
    numeric_refs = re.findall(r'\[(\d+(?:,\d+)*)\]', final_content)
    
    # 检查参考文献部分
    has_reference_section = "Reference Data Sources" in final_content or "参考数据来源" in final_content
    
    print("\n【检查】引用替换情况:")
    print(f"  - 剩余占位符 [Source: xxx]: {len(remaining_citations)} 个")
    if remaining_citations:
        for citation in remaining_citations:
            print(f"    ⚠️  未替换: [Source: {citation}]")
    
    print(f"\n  - 数字引用: {len(numeric_refs)} 个")
    for i, ref in enumerate(numeric_refs[:5], 1):  # 只显示前5个
        print(f"    {i}. [{ref}]")
    
    print(f"\n  - 参考文献部分: {'✓ 已添加' if has_reference_section else '✗ 未找到'}")
    
    if has_reference_section:
        # 提取参考文献列表
        ref_section_match = re.search(r'##\s*Reference Data Sources(.*?)(?=##|$)', final_content, re.DOTALL)
        if ref_section_match:
            ref_content = ref_section_match.group(1).strip()
            ref_items = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|\n*$)', ref_content, re.DOTALL)
            
            print(f"\n  参考文献列表 ({len(ref_items)} 条):")
            for item in ref_items:
                print(f"    • {item.strip()[:60]}...")
    
    # 总结
    print("\n" + "="*70)
    if len(remaining_citations) == 0 and has_reference_section:
        print("  ✅ 所有引用已成功替换，参考文献已添加！")
    else:
        print("  ⚠️  存在问题:")
        if len(remaining_citations) > 0:
            print("     - 部分引用未被替换")
        if not has_reference_section:
            print("     - 参考文献部分未添加")
    print("="*70 + "\n")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(test_reference_replacement())
