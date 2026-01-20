"""
【测试步骤 4】Memory 持久化 - 断点续传机制

功能说明:
    Memory 系统负责保存和恢复整个系统的状态，包括：
    - 采集的数据
    - 分析结果
    - 任务映射
    - Embedding 缓存

测试目标:
    1. 理解 Memory 的内部结构
    2. 测试保存和加载机制
    3. 验证断点续传的完整性

运行方式:
    python tests/basic_components/step4_test_memory_persistence.py
"""
import os
import sys
from pathlib import Path
import pandas as pd

root = str(Path(__file__).resolve().parents[2])
sys.path.append(root)

from src.config import Config
from src.memory import Memory
from src.tools import ToolResult
from src.agents.data_analyzer.data_analyzer import AnalysisResult


def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def create_test_memory(config):
    """创建包含测试数据的 Memory"""
    print_section("创建测试 Memory")
    
    memory = Memory(config=config)
    
    # 添加数据源
    print("\n【步骤 1】添加数据源:")
    
    data1 = ToolResult(
        name="测试数据 1",
        description="财务数据",
        data=pd.DataFrame({'年份': [2023], '营收': [100]}),
        source="测试来源"
    )
    memory.add_data(data1)
    print(f"  ✓ 添加: {data1.name}")
    
    data2 = ToolResult(
        name="测试数据 2",
        description="行业数据",
        data={"key": "value"},
        source="测试来源"
    )
    memory.add_data(data2)
    print(f"  ✓ 添加: {data2.name}")
    
    # 添加分析结果
    print("\n【步骤 2】添加分析结果:")
    
    temp_dir = os.path.join(config.working_dir, "test_images")
    os.makedirs(temp_dir, exist_ok=True)
    
    analysis1 = AnalysisResult(
        title="财务分析",
        content="分析内容...",
        image_save_dir=temp_dir,
        chart_name_mapping={"图表1": "chart1.png"},
        chart_name_description_mapping={"图表1": "测试图表"}
    )
    memory.add_data(analysis1)
    print(f"  ✓ 添加: {analysis1.title}")
    
    # 模拟任务映射
    print("\n【步骤 3】添加任务映射:")
    
    task_info = {
        'task_key': '测试任务',
        'agent_class_name': 'test_agent',
        'task_input': {'task': '测试'},
        'agent_id': 'agent_test_123',
        'agent_kwargs': {},
        'priority': 1
    }
    memory.task_mapping.append(task_info)
    print(f"  ✓ 添加任务: {task_info['task_key']}")
    
    # 添加生成的任务
    print("\n【步骤 4】添加生成的任务:")
    
    memory.generated_collect_tasks = ['采集任务1', '采集任务2']
    memory.generated_analysis_tasks = ['分析任务1', '分析任务2']
    print(f"  ✓ 采集任务: {len(memory.generated_collect_tasks)} 个")
    print(f"  ✓ 分析任务: {len(memory.generated_analysis_tasks)} 个")
    
    return memory


def inspect_memory(memory, title="Memory 状态"):
    """检查 Memory 的内容"""
    print_section(title)
    
    print("\n【数据统计】:")
    print(f"  - 数据项总数: {len(memory.data)}")
    
    # 按类型分组
    type_counts = {}
    for item in memory.data:
        type_name = type(item).__name__
        type_counts[type_name] = type_counts.get(type_name, 0) + 1
    
    print(f"\n  按类型分组:")
    for type_name, count in type_counts.items():
        print(f"    • {type_name}: {count}")
    
    print(f"\n【任务映射】:")
    print(f"  - 任务数量: {len(memory.task_mapping)}")
    for i, task in enumerate(memory.task_mapping, 1):
        print(f"    {i}. {task['agent_class_name']} - {task['task_key']}")
    
    print(f"\n【生成的任务】:")
    print(f"  - 采集任务: {len(memory.generated_collect_tasks)}")
    for i, task in enumerate(memory.generated_collect_tasks, 1):
        print(f"    {i}. {task}")
    
    print(f"  - 分析任务: {len(memory.generated_analysis_tasks)}")
    for i, task in enumerate(memory.generated_analysis_tasks, 1):
        print(f"    {i}. {task}")
    
    print(f"\n【Embedding 缓存】:")
    print(f"  - 缓存项数: {len(memory.data2embedding)}")
    
    print(f"\n【日志】:")
    print(f"  - 日志条目: {len(memory.log)}")


def test_save_and_load():
    """测试保存和加载"""
    print("\n" + "🧪 " + "="*68)
    print("  Memory 持久化测试")
    print("="*70)
    print("\n说明:")
    print("  Memory 使用 dill 序列化保存状态，支持:")
    print("  1. 完整的数据结构（包括 pandas DataFrame）")
    print("  2. 任务映射（用于恢复 Agent）")
    print("  3. Embedding 缓存（避免重复计算）")
    print("  4. 操作日志（用于审计和调试）")
    print("="*70)
    
    # 1. 创建测试配置
    config = Config(config_file_path='tests/my_config.yaml')
    
    # 2. 创建包含数据的 Memory
    memory1 = create_test_memory(config)
    
    # 3. 查看初始状态
    inspect_memory(memory1, "保存前的 Memory 状态")
    
    # 4. 保存
    print_section("保存 Memory")
    
    checkpoint_name = 'test_memory_checkpoint.pkl'
    checkpoint_path = os.path.join(memory1.save_dir, checkpoint_name)
    
    print(f"\n【操作】保存到: {checkpoint_path}")
    memory1.save(checkpoint_name=checkpoint_name)
    
    # 检查文件
    if os.path.exists(checkpoint_path):
        file_size = os.path.getsize(checkpoint_path)
        print(f"  ✓ 文件已创建")
        print(f"  ✓ 文件大小: {file_size / 1024:.2f} KB")
    else:
        print(f"  ✗ 文件未创建！")
        return
    
    # 5. 创建新的 Memory 并加载
    print_section("加载 Memory")
    
    memory2 = Memory(config=config)
    
    print(f"\n【操作】从检查点加载...")
    success = memory2.load(checkpoint_name=checkpoint_name)
    
    if success:
        print(f"  ✓ 加载成功")
    else:
        print(f"  ✗ 加载失败！")
        return
    
    # 6. 验证加载的内容
    inspect_memory(memory2, "加载后的 Memory 状态")
    
    # 7. 对比验证
    print_section("对比验证")
    
    checks = []
    
    # 检查数据项数量
    data_match = len(memory1.data) == len(memory2.data)
    checks.append(("数据项数量", data_match))
    print(f"\n  数据项数量: {len(memory1.data)} → {len(memory2.data)}")
    print(f"    {'✓' if data_match else '✗'} {'匹配' if data_match else '不匹配'}")
    
    # 检查任务映射
    task_match = len(memory1.task_mapping) == len(memory2.task_mapping)
    checks.append(("任务映射", task_match))
    print(f"\n  任务映射: {len(memory1.task_mapping)} → {len(memory2.task_mapping)}")
    print(f"    {'✓' if task_match else '✗'} {'匹配' if task_match else '不匹配'}")
    
    # 检查生成的任务
    collect_match = memory1.generated_collect_tasks == memory2.generated_collect_tasks
    analysis_match = memory1.generated_analysis_tasks == memory2.generated_analysis_tasks
    checks.append(("生成的任务", collect_match and analysis_match))
    print(f"\n  生成的任务:")
    print(f"    采集: {collect_match} ({'✓' if collect_match else '✗'})")
    print(f"    分析: {analysis_match} ({'✓' if analysis_match else '✗'})")
    
    # 检查 Embedding 缓存
    embedding_match = len(memory1.data2embedding) == len(memory2.data2embedding)
    checks.append(("Embedding 缓存", embedding_match))
    print(f"\n  Embedding 缓存: {len(memory1.data2embedding)} → {len(memory2.data2embedding)}")
    print(f"    {'✓' if embedding_match else '✗'} {'匹配' if embedding_match else '不匹配'}")
    
    # 总结
    print("\n" + "="*70)
    all_passed = all(result for _, result in checks)
    
    if all_passed:
        print("  ✅ 所有检查通过！Memory 持久化工作正常")
    else:
        print("  ⚠️  部分检查失败:")
        for name, result in checks:
            if not result:
                print(f"    ✗ {name}")
    
    print("="*70)
    
    # 清理
    print("\n【清理】删除测试文件...")
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)
        print(f"  ✓ 已删除: {checkpoint_path}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    test_save_and_load()
