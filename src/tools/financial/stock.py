import requests
import json
import akshare as ak
import pandas as pd
import efinance as ef
from bs4 import BeautifulSoup

from ..base import Tool, ToolResult

# TODO: 后续可针对雪球不同市场（先区分上交所/深交所）使用更细致接口。
class StockBasicInfo(Tool):
    def __init__(self):
        super().__init__(
            name="股票公司简介",
            description="根据指定股票代码返回公司的基础简介信息。调用前请确认已判定交易所与市场。",
            parameters=[
                {"name": "stock_code", "type": "str", "description": "股票代码，如 000001", "required": True},
                {"name": "market", "type": "str", "description": "市场标识: A 为 A 股，HK 为港股", "required": True},
            ],
        )

    def prepare_params(self, task) -> dict:
        """
        根据任务对象构建工具调用参数。
        """
        if task.stock_code is None:
            # 上游应该已完成验证
            assert False, "股票代码不可为空"
        else:
            return {"stock_code": task.stock_code, "market": task.market}

    async def api_function(self, stock_code: str, market: str = "HK"):
        """
        调用上游接口，返回公司简介数据。
        """
        try:
            if market == "A":
                data = ak.stock_zyjs_ths(symbol=stock_code)
            elif market == "HK":
                data = ak.stock_hk_company_profile_em(symbol=stock_code)
            else:
                raise ValueError(f"不支持的市场标识: {market}，请使用 'HK' 或 'A'。")
        except Exception as e:
            print("获取股票基本信息失败", e)
            data = None
        return [
            ToolResult(
                name = f"{self.name}: {stock_code}",
                description = f"{stock_code} 的公司简介信息。",
                data = data,
                source="雪球: 股票公司基本信息 https://xueqiu.com/S"
            )
        ]


class ShareHoldingStructure(Tool):
    def __init__(self):
        super().__init__(
            name="股权结构",
            description="返回股票主要股东名称、持股数量、占比、股权类型等信息。",
            parameters=[
                {"name": "stock_code", "type": "str", "description": "股票代码，如 000001", "required": True},
                {"name": "market", "type": "str", "description": "市场标识: A 为 A 股，HK 为港股", "required": True},
            ],
        )

    def prepare_params(self, task) -> dict:
        """
        根据任务对象构建工具调用参数。
        """
        if task.stock_code is None:
            # 上游应该已完成验证
            assert False, "股票代码不可为空"
        else:
            return {"stock_code": task.stock_code, "market": task.market}

    async def api_function(self, stock_code: str, market: str = "HK"):
        """
        获取指定股票的股东结构信息（区分市场）。
        """
        try:
            if market == "A":
                data = ak.stock_main_stock_holder(stock=stock_code)
            elif market == "HK":
                # 从东方财富网抓取数据
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                output = requests.get(
                    f"https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_HKF10_EQUITYCHG_HOLDER&columns=SECURITY_CODE%2CSECUCODE%2CORG_CODE%2CNOTICE_DATE%2CREPORT_DATE%2CHOLDER_NAME%2CTOTAL_SHARES%2CTOTAL_SHARES_RATIO%2CDIRECT_SHARES%2CSHARES_CHG_RATIO%2CSHARES_TYPE%2CEQUITY_TYPE%2CHOLD_IDENTITY%2CIS_ZJ&quoteColumns=&filter=(SECUCODE%3D%22{stock_code}.HK%22)(REPORT_DATE%3D%272024-12-31%27)&pageNumber=1&pageSize=&sortTypes=-1%2C-1&sortColumns=EQUITY_TYPE%2CTOTAL_SHARES&source=F10&client=PC&v=032666133943694553",
                    headers = headers,
                )
                try:
                    html = output.text
                    output = json.loads(html)
                    data = output["result"]["data"]
                    data = pd.DataFrame(data)
                    data = data.rename(columns={
                        'HOLDER_NAME': 'holder_name',
                        'TOTAL_SHARES': 'shares',
                        'TOTAL_SHARES_RATIO': 'ownership_pct',
                        'DIRECT_SHARES': 'direct_shares',
                        'HOLD_IDENTITY': 'ownership_type',
                        'IS_ZJ': 'is_direct'
                    })
                    data = data.loc[:, ['holder_name', 'shares', 'ownership_pct', 'ownership_type', 'is_direct']]
                    data['is_direct'] = data['is_direct'].map({'1': '是', '0': '否'})
                    data.sort_values(by='ownership_pct', ascending=False, inplace=True)
                    data.reset_index(drop=True, inplace=True)
                except Exception as e:
                    print("解析港股股东结构失败", e)
                    data = None
            else:
                raise ValueError(f"不支持的市场标识: {market}，请使用 'HK' 或 'A'。")
        except Exception as e:
            print("获取股权结构失败", e)
            data = None
        return [
            ToolResult(
                name=f"{self.name} (股票代码: {stock_code})",
                description=self.description,
                data=data,
                source="新浪财经: 股东结构 https://vip.stock.finance.sina.com.cn/corp/go.php/vCI_StockHolder/stockid/600004.phtml"
            )
        ]

class StockBaseInfo(Tool):
    def __init__(self):
        super().__init__(
            name="股票估值指标",
            description="返回市盈率、市净率、净资产收益率（ROE）、毛利率等基本估值与盈利能力指标。",
            parameters=[
                {"name": "stock_code", "type": "str", "description": "股票代码，如 000001", "required": True},
            ],
        )

    def prepare_params(self, task) -> dict:
        return {"stock_code": task.stock_code}

    async def api_function(self, stock_code: str, market: str = "HK"):
        """
        获取指定股票的估值及盈利能力核心指标。
        """
        try:
            data = ef.stock.get_base_info(stock_code)
        except Exception as e:
            print("获取股票估值指标失败", e)
            data = None
        return [
            ToolResult(
                name=f"{self.name} (股票代码: {stock_code})",
                description=self.description,
                data=data,
                source="交易所公告: 股票估值与盈利指标"
            )
        ]


class StockPrice(Tool):
    def __init__(self):
        super().__init__(
            name="股票K线行情数据",
            description="返回股票每日K线行情，包括开收盘价、最高价、最低价、成交量、换手率等指标。",
            parameters=[
                {"name": "stock_code", "type": "str", "description": "股票代码（支持A股与港股），如 000001", "required": True},
            ],
        )

    def prepare_params(self, task) -> dict:
        return {"stock_code": task.stock_code}

    async def api_function(self, stock_code: str, market: str = "HK"):
        """
        获取指定股票的历史行情数据（日线K线）。
        """
        try:
            data = ef.stock.get_quote_history(stock_code)
        except Exception as e:
            print("获取股票历史行情失败", e)
            data = None
        return [
            ToolResult(
                name=f"{self.name} (股票代码: {stock_code})",
                description=self.description,
                data=data,
                source="交易所行情: 股票历史K线数据"
            )
        ]