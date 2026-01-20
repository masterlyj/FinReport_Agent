"""
【测试步骤 1】IndexBuilder - 语义检索核心组件

功能说明:
    IndexBuilder 负责将文本（如图片标题、数据描述）转换为向量，
    并提供语义搜索功能，用于匹配报告中的占位符。

测试目标:
    1. 验证 Embedding 生成是否正常
    2. 测试 Top-K 语义检索的准确性
    3. 观察相似度分数的分布

运行方式:
    python tests/basic_components/step1_test_indexbuilder.py
"""
import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
root = str(Path(__file__).resolve().parents[2])
sys.path.append(root)

from src.config import Config
from src.utils.index_builder import IndexBuilder


def print_section(title):
    """打印分隔线"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


async def test_basic_embedding():
    """测试 1: 基础 Embedding 生成"""
    print_section("测试 1: Embedding 生成")
    
    # 准备配置
    config = Config(config_file_path='tests/my_config.yaml')
    
    # 创建 IndexBuilder 实例
    index = IndexBuilder(
        config=config,
        embedding_model=os.getenv('EMBEDDING_MODEL_NAME', 'qwen3-embedding-0.6b'),
        working_dir='./test_output'
    )
    
    # 准备测试文本（模拟图片标题）
    test_texts = [
        "Revenue Growth Trend Chart 2020-2024",
        "Profit Margin Analysis Bar Chart",
        "Market Share Distribution Pie Chart"
    ]
    
    print("\n【输入】待索引的文本列表:")
    for i, text in enumerate(test_texts, 1):
        print(f"  {i}. {text}")
    
    # 构建索引
    print("\n【处理中】调用 Embedding API 生成向量...")
    await index._build_index(test_texts)
    
    print("\n【输出】Embedding 结果:")
    print(f"  - 生成的向量数量: {len(index.embeddings)}")
    if index.embeddings:
        print(f"  - 向量维度: {len(index.embeddings[0])}")
        print(f"  - 第一个向量的前 5 个值: {index.embeddings[0][:5]}")
    
    print("\n✅ Embedding 生成成功！")
    return index, test_texts


async def test_semantic_search(index, test_texts):
    """测试 2: 语义搜索"""
    print_section("测试 2: 语义搜索 (Top-K)")
    
    # 测试查询（中文，模拟 LLM 生成的占位符）
    test_queries = [
        "@import \"营收趋势图\"",
        "@import \"利润率分析图表\"",
        "@import \"市场份额饼图\""
    ]
    
    print("\n【输入】查询列表:")
    for i, query in enumerate(test_queries, 1):
        print(f"  {i}. {query}")
    
    print("\n【处理中】执行语义检索...")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- 查询 {i}: {query} ---")
        
        # 执行搜索
        results = await index.search(query, top_k=3)
        
        print(f"\n【输出】Top-3 匹配结果:")
        for rank, result in enumerate(results, 1):
            matched_idx = result['id']
            score = result['score']
            matched_text = test_texts[matched_idx]
            
            # 用颜色标记最佳匹配
            marker = "🎯" if rank == 1 else "  "
            print(f"  {marker} [{rank}] 相似度: {score:.4f}")
            print(f"       匹配文本: {matched_text}")
    
    print("\n✅ 语义搜索测试完成！")


async def test_index_rebuild():
    """测试 3: 动态索引重建（避免重复使用）"""
    print_section("测试 3: 动态索引重建机制")
    
    config = Config(config_file_path='tests/my_config.yaml')
    index = IndexBuilder(
        config=config,
        embedding_model=os.getenv('EMBEDDING_MODEL_NAME', 'qwen3-embedding-0.6b'),
        working_dir='./test_output'
    )
    
    # 初始图片列表
    img_captions = [
        "Revenue Chart A",
        "Revenue Chart B", 
        "Profit Chart"
    ]
    
    print("\n【初始状态】图片列表:")
    for i, caption in enumerate(img_captions):
        print(f"  [{i}] {caption}")
    
    # 构建初始索引
    await index._build_index(img_captions)
    
    # 第一次查询
    query = "营收图表"
    print(f"\n【查询 1】'{query}'")
    results = await index.search(query, top_k=1)
    matched_idx = results[0]['id']
    matched_caption = img_captions[matched_idx]
    
    print(f"  🎯 匹配结果: [{matched_idx}] {matched_caption}")
    print(f"     相似度: {results[0]['score']:.4f}")
    
    # 模拟使用后删除
    print(f"\n【操作】删除已使用的图片 [{matched_idx}] {matched_caption}")
    del img_captions[matched_idx]
    
    print("\n【更新后】剩余图片:")
    for i, caption in enumerate(img_captions):
        print(f"  [{i}] {caption}")
    
    # 重建索引
    print("\n【处理中】重建索引...")
    await index._build_index(img_captions)
    
    # 第二次查询
    print(f"\n【查询 2】'{query}' (再次查询)")
    results2 = await index.search(query, top_k=1)
    matched_idx2 = results2[0]['id']
    matched_caption2 = img_captions[matched_idx2]
    
    print(f"  🎯 匹配结果: [{matched_idx2}] {matched_caption2}")
    print(f"     相似度: {results2[0]['score']:.4f}")
    
    print("\n【验证】两次匹配是否为不同图片:")
    print(f"  第一次: {matched_caption}")
    print(f"  第二次: {matched_caption2}")
    
    if matched_caption != matched_caption2:
        print("  ✅ 成功避免重复使用！")
    else:
        print("  ⚠️  匹配到相同图片（可能因为剩余选项少）")


async def main():
    """主测试流程"""
    print("\n" + "🧪 " + "="*68)
    print("  IndexBuilder 组件测试")
    print("="*70)
    print("\n说明:")
    print("  IndexBuilder 是生成式检索的核心，负责:")
    print("  1. 将文本转换为向量 (Embedding)")
    print("  2. 基于余弦相似度进行语义搜索")
    print("  3. 返回最相关的 Top-K 结果")
    print("\n" + "="*70)
    
    try:
        # 测试 1: Embedding 生成
        index, test_texts = await test_basic_embedding()
        
        # 测试 2: 语义搜索
        await test_semantic_search(index, test_texts)
        
        # 测试 3: 动态重建
        await test_index_rebuild()
        
        print("\n" + "="*70)
        print("  ✅ 所有测试通过！")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 加载环境变量
    from dotenv import load_dotenv
    load_dotenv()
    
    # 运行测试
    asyncio.run(main())
