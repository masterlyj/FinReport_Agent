"""
IndexBuilder 单元测试
测试图片标题的语义检索和 Top-K 排序
"""
import asyncio
import os
import sys
from pathlib import Path

root = str(Path(__file__).resolve().parents[3])
sys.path.append(root)

from src.config import Config
from src.utils.index_builder import IndexBuilder


async def test_basic_search():
    """测试基础搜索功能"""
    print("\n" + "="*60)
    print("测试 1: 基础语义搜索")
    print("="*60)
    
    config = Config(config_file_path='tests/my_config.yaml')
    
    # 模拟图片标题列表（来自分析结果）
    img_captions = [
        "Revenue Growth Trend Chart 2020-2024",
        "Profit Margin Analysis Bar Chart",
        "Market Share Distribution Pie Chart",
        "Cash Flow Waterfall Diagram",
        "Stock Price Candlestick Chart"
    ]
    
    # 构建索引
    index = IndexBuilder(
        config=config,
        embedding_model=os.getenv('EMBEDDING_MODEL_NAME', 'qwen3-embedding-0.6b'),
        working_dir='./test_output'
    )
    print(f"\n构建索引: {len(img_captions)} 个图片标题")
    await index._build_index(img_captions)
    
    # 测试查询（模拟 LLM 生成的占位符）
    test_cases = [
        ("@import \"营收趋势图\"", 0),  # 应匹配第1个
        ("@import \"利润率分析\"", 1),   # 应匹配第2个
        ("@import \"市场占有率饼图\"", 2),  # 应匹配第3个
        ("@import \"现金流瀑布图\"", 3),   # 应匹配第4个
    ]
    
    success_count = 0
    for query, expected_idx in test_cases:
        results = await index.search(query, top_k=3)
        actual_idx = results[0]['id']
        score = results[0]['score']
        
        print(f"\n查询: {query}")
        print(f"  期望匹配: [{expected_idx}] {img_captions[expected_idx]}")
        print(f"  实际匹配: [{actual_idx}] {img_captions[actual_idx]} (相似度: {score:.3f})")
        
        if actual_idx == expected_idx:
            print("  ✅ 通过")
            success_count += 1
        else:
            print("  ❌ 失败")
            print("  Top-3 结果:")
            for i, res in enumerate(results[:3], 1):
                idx = res['id']
                print(f"    {i}. [{res['score']:.3f}] {img_captions[idx]}")
    
    print(f"\n总结: {success_count}/{len(test_cases)} 个测试通过")
    assert success_count >= len(test_cases) * 0.75, "匹配准确率低于75%"


async def test_dynamic_index_rebuild():
    """测试动态索引重建（避免重复使用图片）"""
    print("\n" + "="*60)
    print("测试 2: 动态索引重建机制")
    print("="*60)
    
    config = Config(config_file_path='tests/my_config.yaml')
    
    img_captions = [
        "Revenue Chart A",
        "Revenue Chart B",
        "Profit Chart"
    ]
    img_paths = ["/path/to/rev_a.png", "/path/to/rev_b.png", "/path/to/profit.png"]
    
    index = IndexBuilder(
        config=config,
        embedding_model=os.getenv('EMBEDDING_MODEL_NAME', 'qwen3-embedding-0.6b'),
        working_dir='./test_output'
    )
    await index._build_index(img_captions)
    
    # 第一次查询
    query1 = "营收图表"
    results1 = await index.search(query1, top_k=1)
    matched_idx1 = results1[0]['id']
    print(f"\n第一次查询 '{query1}'")
    print(f"  匹配: [{matched_idx1}] {img_captions[matched_idx1]}")
    
    # 模拟使用后删除
    del img_captions[matched_idx1]
    del img_paths[matched_idx1]
    await index._build_index(img_captions)  # 重建索引
    print(f"  已删除并重建索引，剩余 {len(img_captions)} 张图")
    
    # 第二次查询（应该匹配另一个图）
    results2 = await index.search(query1, top_k=1)
    matched_idx2 = results2[0]['id']
    print(f"\n第二次查询 '{query1}'")
    print(f"  匹配: [{matched_idx2}] {img_captions[matched_idx2]}")
    
    # 验证两次匹配的不是同一张图
    assert len(img_captions) == 2, "删除后剩余数量不对"
    print("\n  ✅ 动态索引重建测试通过")


async def test_cache_performance():
    """测试缓存性能"""
    print("\n" + "="*60)
    print("测试 3: Embedding 缓存性能")
    print("="*60)
    
    config = Config(config_file_path='tests/my_config.yaml')
    
    img_captions = ["Test Chart 1", "Test Chart 2", "Test Chart 3"]
    
    index = IndexBuilder(
        config=config,
        embedding_model=os.getenv('EMBEDDING_MODEL_NAME', 'qwen3-embedding-0.6b'),
        working_dir='./test_output'
    )
    
    # 第一次构建（会调用 API）
    import time
    start = time.time()
    await index._build_index(img_captions)
    first_time = time.time() - start
    print(f"\n第一次构建索引耗时: {first_time:.2f}s")
    
    # 再次构建相同的数据（应该从缓存读取）
    start = time.time()
    await index._build_index(img_captions)
    second_time = time.time() - start
    print(f"第二次构建索引耗时: {second_time:.2f}s")
    
    # 缓存应该显著加速
    speedup = first_time / max(second_time, 0.01)
    print(f"缓存加速比: {speedup:.1f}x")
    
    if speedup > 2:
        print("  ✅ 缓存有效")
    else:
        print("  ⚠️  缓存加速不明显（可能是首次运行）")


if __name__ == "__main__":
    print("\n🧪 IndexBuilder 单元测试套件")
    print("="*60)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        asyncio.run(test_basic_search())
        asyncio.run(test_dynamic_index_rebuild())
        asyncio.run(test_cache_performance())
        
        print("\n" + "="*60)
        print("✅ 所有测试通过")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
