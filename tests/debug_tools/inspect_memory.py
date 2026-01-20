"""
Memory 状态检查工具
用于快速查看 Memory 的内容，辅助调试
"""
import dill
import sys
import os
from pathlib import Path

root = str(Path(__file__).resolve().parents[2])
sys.path.append(root)


def inspect_memory(memory_path='outputs/my-research/memory/memory.pkl'):
    """打印 Memory 的详细信息"""
    if not os.path.exists(memory_path):
        print(f"❌ 文件不存在: {memory_path}")
        print("\n提示: 使用方式:")
        print("  python tests/debug_tools/inspect_memory.py <memory_path>")
        return
    
    print("\n" + "="*70)
    print(" Memory State Inspector".center(70))
    print("="*70)
    print(f"文件路径: {memory_path}")
    print(f"文件大小: {os.path.getsize(memory_path) / 1024:.2f} KB")
    
    try:
        with open(memory_path, 'rb') as f:
            state = dill.load(f)
    except Exception as e:
        print(f"\n❌ 无法加载文件: {e}")
        return
    
    # 数据项统计
    print("\n" + "-"*70)
    print("📊 数据项 (Data Items)")
    print("-"*70)
    print(f"总数: {len(state.get('data', []))}")
    
    data_types = {}
    for item in state.get('data', []):
        type_name = type(item).__name__
        data_types[type_name] = data_types.get(type_name, 0) + 1
    
    print("\n按类型分组:")
    for type_name, count in sorted(data_types.items(), key=lambda x: -x[1]):
        print(f"  • {type_name}: {count}")
    
    print("\n前 5 个数据项:")
    for i, item in enumerate(state.get('data', [])[:5]):
        type_name = type(item).__name__
        name = getattr(item, 'name', 'N/A')
        print(f"  [{i}] {type_name}: {name}")
    
    # 任务映射
    print("\n" + "-"*70)
    print("📋 任务映射 (Task Mapping)")
    print("-"*70)
    task_mapping = state.get('task_mapping', [])
    print(f"总数: {len(task_mapping)}\n")
    
    for i, task in enumerate(task_mapping):
        agent_class = task.get('agent_class_name', 'N/A')
        agent_id = task.get('agent_id', 'N/A')
        priority = task.get('priority', 0)
        task_key = task.get('task_key', 'N/A')
        
        print(f"  [{i}] {agent_class} (优先级: {priority})")
        print(f"      Agent ID: {agent_id}")
        print(f"      Task Key: {task_key[:50]}..." if len(task_key) > 50 else f"      Task Key: {task_key}")
    
    # 向量索引
    print("\n" + "-"*70)
    print("🔢 向量索引 (Embeddings)")
    print("-"*70)
    embeddings = state.get('data2embedding', {})
    print(f"缓存的 Embedding 数量: {len(embeddings)}")
    
    if embeddings:
        print("\n示例键值:")
        for key in list(embeddings.keys())[:3]:
            print(f"  • {key[:60]}...")
    
    # 生成的任务
    print("\n" + "-"*70)
    print("📝 LLM 生成的任务")
    print("-"*70)
    collect_tasks = state.get('generated_collect_tasks', [])
    analysis_tasks = state.get('generated_analysis_tasks', [])
    
    print(f"采集任务 (Collect): {len(collect_tasks)}")
    for i, task in enumerate(collect_tasks):
        print(f"  {i+1}. {task}")
    
    print(f"\n分析任务 (Analysis): {len(analysis_tasks)}")
    for i, task in enumerate(analysis_tasks):
        print(f"  {i+1}. {task}")
    
    # 依赖关系
    print("\n" + "-"*70)
    print("🔗 依赖关系 (Dependencies)")
    print("-"*70)
    dependencies = state.get('dependency', {})
    print(f"依赖关系数量: {len(dependencies)}\n")
    
    for parent, children in list(dependencies.items())[:5]:
        print(f"  {parent[:40]}...")
        for child in children[:3]:
            print(f"    └─ {child[:40]}...")
    
    # 日志
    print("\n" + "-"*70)
    print("📜 日志 (Logs)")
    print("-"*70)
    logs = state.get('log', [])
    print(f"日志条目数: {len(logs)}")
    
    if logs:
        print("\n最近 3 条日志:")
        for log in logs[-3:]:
            timestamp = log.get('timestamp', 'N/A')
            log_type = log.get('type', 'N/A')
            error = log.get('error', False)
            status = "❌" if error else "✅"
            print(f"  {status} [{timestamp}] {log_type}")
    
    print("\n" + "="*70)
    print(" 检查完成".center(70))
    print("="*70 + "\n")


def compare_memories(path1, path2):
    """比较两个 Memory 状态的差异"""
    print("\n" + "="*70)
    print(" Memory Comparison".center(70))
    print("="*70)
    
    with open(path1, 'rb') as f:
        state1 = dill.load(f)
    with open(path2, 'rb') as f:
        state2 = dill.load(f)
    
    print(f"\nMemory 1: {path1}")
    print(f"Memory 2: {path2}")
    
    print("\n" + "-"*70)
    print("差异对比:")
    print("-"*70)
    
    # 数据项差异
    data1_count = len(state1.get('data', []))
    data2_count = len(state2.get('data', []))
    print(f"📊 数据项: {data1_count} → {data2_count} (delta: {data2_count - data1_count:+d})")
    
    # 任务差异
    task1_count = len(state1.get('task_mapping', []))
    task2_count = len(state2.get('task_mapping', []))
    print(f"📋 任务: {task1_count} → {task2_count} (delta: {task2_count - task1_count:+d})")
    
    # Embedding 差异
    emb1_count = len(state1.get('data2embedding', {}))
    emb2_count = len(state2.get('data2embedding', {}))
    print(f"🔢 Embeddings: {emb1_count} → {emb2_count} (delta: {emb2_count - emb1_count:+d})")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        inspect_memory(sys.argv[1])
    elif len(sys.argv) == 3:
        compare_memories(sys.argv[1], sys.argv[2])
    else:
        print("使用方式:")
        print("  查看单个 Memory:")
        print("    python tests/debug_tools/inspect_memory.py <memory_path>")
        print("\n  比较两个 Memory:")
        print("    python tests/debug_tools/inspect_memory.py <memory1> <memory2>")
        print("\n示例:")
        print("    python tests/debug_tools/inspect_memory.py outputs/my-research/memory/memory.pkl")
