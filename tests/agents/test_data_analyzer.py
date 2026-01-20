import argparse
import os
import sys
import dill
from pathlib import Path
import asyncio
import logging
from dotenv import load_dotenv
load_dotenv()
root = str(Path(__file__).resolve().parents[2])
sys.path.append(root)


from src.config import Config
from src.agents import DataAnalyzer, DataCollector
from src.memory import Memory

if __name__ == "__main__":
    config = Config(
        config_file_path='my_config.yaml',
    )

    memory = Memory(config=config)
    memory.load()
    # print(memory.get_analysis_result()[0])
    # assert False

    agent = DataAnalyzer(
        config=config, 
        use_llm_name=os.getenv("DS_MODEL_NAME"), 
        use_vlm_name=os.getenv("VLM_MODEL_NAME"), 
        use_embedding_name=os.getenv("EMBEDDING_MODEL_NAME"),
        memory=memory
    )
    try:
        result = asyncio.run(agent.async_run(
            input_data={'task': '浪潮信息', 'analysis_task': '基于已有数据，绘制净利润趋势图'}, echo=True, max_iterations=10, enable_chart=True)
        )
    except Exception as e:
        print(f"Error executing agent: {e}")
        import traceback
        traceback.print_exc()
        result = {}
    
    # Check for generated charts
    chart_dir = os.path.join(config.working_dir, 'charts')
    if os.path.exists(chart_dir):
        print(f"\nGenerated charts in {chart_dir}:")
        for file in os.listdir(chart_dir):
            print(f"- {file}")
    else:
        print(f"\nNo charts directory found at {chart_dir}")
    print(result)
    print(result['final_result'][:100000])
    print(len(memory.data))