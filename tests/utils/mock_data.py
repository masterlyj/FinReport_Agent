"""
Mock 数据生成工具
用于测试时避免依赖真实的 LLM 调用和数据采集
"""
import os
import pandas as pd
from src.memory import Memory
from src.tools import ToolResult
from src.agents.data_analyzer.data_analyzer import AnalysisResult


def create_minimal_mock_memory(config):
    """
    创建包含最小测试数据的 Mock Memory
    适用于快速单元测试
    """
    memory = Memory(config=config)
    
    # Mock 1: 财务数据
    mock_financial_data = pd.DataFrame({
        'Year': [2020, 2021, 2022, 2023],
        'Revenue': [100, 120, 150, 180],
        'Profit': [10, 12, 15, 20]
    })
    
    memory.add_data(ToolResult(
        name="比亚迪 财务数据",
        description="2020-2023年关键财务指标",
        data=mock_financial_data,
        source="Mock Data Source"
    ))
    
    # Mock 2: 分析结果
    analysis_content = """
## 财务分析

营业收入从2020年的100亿增长到2023年的180亿，年复合增长率21.7%。

@import "Revenue Growth Trend Chart"

净利润率保持稳定上升趋势[Source: 财务数据]。
"""
    
    analysis_result = AnalysisResult(
        title="财务指标分析",
        content=analysis_content,
        image_save_dir=os.path.join(config.working_dir, "mock_images"),
        chart_name_mapping={
            "Revenue Growth Trend Chart": "revenue_trend.png"
        },
        chart_name_description_mapping={
            "Revenue Growth Trend Chart": "展示2020-2023年营收增长趋势"
        }
    )
    
    os.makedirs(analysis_result.image_save_dir, exist_ok=True)
    
    memory.add_data(analysis_result)
    
    return memory


def create_full_mock_memory(config):
    """
    创建包含完整测试数据的 Mock Memory
    适用于集成测试
    """
    memory = create_minimal_mock_memory(config)
    
    # 添加更多数据源
    memory.add_data(ToolResult(
        name="比亚迪 年度报告",
        description="2023年年度报告摘要",
        data="公司主要从事新能源汽车及相关产品的研发、生产和销售...",
        source="公司官网 PDF"
    ))
    
    memory.add_data(ToolResult(
        name="行业数据",
        description="新能源汽车市场分析",
        data={"market_size": 800, "growth_rate": 0.35},
        source="行业报告"
    ))
    
    # 添加第二个分析结果
    analysis_result_2 = AnalysisResult(
        title="竞争格局分析",
        content="市场份额分析...\n@import \"Market Share Pie Chart\"",
        image_save_dir=os.path.join(config.working_dir, "mock_images"),
        chart_name_mapping={
            "Market Share Pie Chart": "market_share.png"
        },
        chart_name_description_mapping={
            "Market Share Pie Chart": "新能源汽车市场份额分布"
        }
    )
    
    memory.add_data(analysis_result_2)
    
    return memory


def save_mock_memory(memory, checkpoint_name='mock_memory.pkl'):
    """保存 Mock Memory 到文件"""
    memory.save(checkpoint_name=checkpoint_name)
    print(f"✅ Mock Memory 已保存到: {os.path.join(memory.save_dir, checkpoint_name)}")


def load_mock_memory(config, checkpoint_name='mock_memory.pkl'):
    """从文件加载 Mock Memory"""
    memory = Memory(config=config)
    success = memory.load(checkpoint_name=checkpoint_name)
    if success:
        print(f"✅ Mock Memory 已加载: {checkpoint_name}")
    else:
        print(f"⚠️  未找到 {checkpoint_name}，创建新的 Mock Memory")
        memory = create_minimal_mock_memory(config)
    return memory


if __name__ == "__main__":
    """生成并保存 Mock 数据"""
    import sys
    from pathlib import Path
    
    root = str(Path(__file__).resolve().parents[2])
    sys.path.append(root)
    
    from src.config import Config
    
    config = Config(config_file_path='tests/my_config.yaml')
    
    # 创建完整的 Mock Memory
    print("创建 Mock Memory...")
    memory = create_full_mock_memory(config)
    
    print(f"  - 数据项: {len(memory.data)}")
    print(f"  - 任务映射: {len(memory.task_mapping)}")
    
    # 保存
    save_mock_memory(memory, 'mock_memory_full.pkl')
    
    print("\n可以在测试中使用:")
    print("  from tests.utils.mock_data import load_mock_memory")
    print("  memory = load_mock_memory(config, 'mock_memory_full.pkl')")
