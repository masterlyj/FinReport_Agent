import asyncio
from openai import OpenAI, AsyncOpenAI
from typing import List, Dict, Optional, Union, Any
from .retry import retry, async_retry, RetryError
from .logger import get_logger

logger = get_logger()

class LLM:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model_name: str,
        generation_params: dict = None
    ):
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        self.model_name = model_name
        self.generation_params = generation_params or {}
    
    @retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(Exception,))
    def generate_embeddings(
        self, input_texts: List[str],
    ):
        """生成文本嵌入向量，带重试机制"""
        try:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=input_texts
            )
            return [embedding_data.embedding for embedding_data in response.data]
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {str(e)}")
            raise


    def generate(
        self,
        messages: List[Dict[str, str]],
        **params
    ) -> Union[str, Any]:
        """
        生成对话补全

        Args:
            messages: 对话消息列表
            **params: 额外的生成参数

        Returns:
            生成的文本内容

        Raises:
            NotImplementedError: 客户端不支持
            RetryError: 重试失败
        """
        if not (self.client and hasattr(self.client, 'chat') and hasattr(self.client.chat, 'completions')):
            raise NotImplementedError("客户端不支持 chat completions")

        return self._generate_with_retry(messages, **params)

    @retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(Exception,))
    def _generate_with_retry(
        self,
        messages: List[Dict[str, str]],
        **params
    ) -> Union[str, Any]:
        """内部生成方法，带重试机制"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **{**self.generation_params, **params}
            )

            if hasattr(response, 'choices') and response.choices:
                return response.choices[0].message.content
            return response

        except Exception as e:
            error_msg = str(e)

            # 处理上下文长度超限
            if "Error code: 400" in error_msg:
                logger.warning(f"上下文长度超限，尝试移除早期消息。当前消息数: {len(messages)}")

                # 查找并移除第一条 assistant 消息
                first_assistant_idx = None
                for i, message in enumerate(messages):
                    if message["role"] == "assistant":
                        first_assistant_idx = i
                        break

                if first_assistant_idx is not None:
                    messages.pop(first_assistant_idx)
                    logger.info(f"已移除第 {first_assistant_idx} 条消息")
                    return self._generate_with_retry(messages, **params)

            logger.error(f"API 调用失败: {error_msg}")
            raise Exception(f"API 调用失败: {error_msg}")


class AsyncLLM:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model_name: Union[str, List[str]],
        generation_params: dict = None
    ):
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key
        )
        self.generation_params = generation_params or {}
        self.model_name = model_name
    
    @async_retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(Exception,))
    async def generate_embeddings(
        self, input_texts: List[str],
    ):
        """异步生成文本嵌入向量，带重试机制"""
        try:
            response = await self.client.embeddings.create(
                model=self.model_name,
                input=input_texts
            )
            return [embedding_data.embedding for embedding_data in response.data]
        except Exception as e:
            logger.error(f"异步生成嵌入向量失败: {str(e)}")
            raise

    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_retries_per_model: int = 5,
        include_stop_string: bool = True,
        **params
    ) -> Union[str, Any]:
        """
        异步生成对话补全，带智能重试和错误恢复

        Args:
            messages: 对话消息列表
            max_retries_per_model: 最大重试次数
            include_stop_string: 是否包含停止原因字符串
            **params: 额外的生成参数

        Returns:
            生成的文本内容

        Raises:
            NotImplementedError: 客户端不支持
            RetryError: 重试失败
        """
        if not (self.client and hasattr(self.client, 'chat') and hasattr(self.client.chat, 'completions')):
            raise NotImplementedError("异步客户端不支持 chat completions")

        last_exception = None

        for attempt in range(1, max_retries_per_model + 1):
            try:
                response = await self._call_api(messages, params)
                return self._extract_output(response, include_stop_string)

            except Exception as e:
                last_exception = e
                logger.warning(f"AsyncLLM.generate 第 {attempt}/{max_retries_per_model} 次尝试失败: {str(e)}")

                # 尝试从错误中恢复
                should_continue = await self._handle_generation_error(e, messages, params, attempt, max_retries_per_model)

                if not should_continue:
                    break

                await asyncio.sleep(2)

        error_msg = f"所有 {max_retries_per_model} 次尝试均失败。最后错误: {last_exception}"
        logger.error(error_msg)
        raise RetryError(error_msg, last_exception=last_exception)

    async def _call_api(self, messages: List[Dict[str, str]], params: dict) -> Any:
        """调用 API 生成响应"""
        return await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            **{**self.generation_params, **params}
        )

    def _extract_output(self, response: Any, include_stop_string: bool) -> str:
        """从响应中提取输出内容"""
        if hasattr(response, 'choices') and response.choices:
            output = response.choices[0].message.content
        else:
            output = response

        # 尝试获取停止原因
        if include_stop_string:
            try:
                stop_reason = response.choices[0].provider_specific_fields.get('stop_reason')
                if stop_reason:
                    output += stop_reason
            except (AttributeError, KeyError, IndexError):
                pass

        return output

    async def _handle_generation_error(
        self,
        error: Exception,
        messages: List[Dict[str, str]],
        params: dict,
        attempt: int = 0,
        max_attempts: int = 0
    ) -> bool:
        """
        处理生成过程中的错误，尝试恢复

        Returns:
            bool: True 表示应该继续重试，False 表示应该停止
        """
        error_msg = str(error)

        # 处理 400 错误
        if "Error code: 400" not in error_msg:
            return True  # 其他错误继续重试

        # JSON 验证失败
        if "json_validate_failed" in error_msg or "Failed to generate JSON" in error_msg:
            logger.warning("检测到 JSON 验证错误，移除 response_format 并添加提示")
            params.pop('response_format', None)
            if messages:
                messages[-1]["content"] += (
                    "\n\nIMPORTANT: Your previous response failed JSON validation. "
                    "Please ensure your response is a valid JSON object if requested, "
                    "or plain text with the required XML tags. "
                    "DO NOT include any conversational filler or markdown code blocks if a JSON is requested."
                )
            return True

        # 工具选择错误
        if "Tool choice is none" in error_msg:
            logger.warning("检测到工具选择错误，添加提示避免原生工具调用")
            if messages:
                messages[-1]["content"] += (
                    "\n\nIMPORTANT: Please respond with plain text and use the required XML tags "
                    "(e.g., <execute> or <final_result>) for tool calls. "
                    "DO NOT use the model's native function calling feature."
                )
            return True

        # 上下文长度超限
        logger.warning("上下文长度超限，尝试移除早期消息")
        return self._remove_early_message(messages)

    def _remove_early_message(self, messages: List[Dict[str, str]]) -> bool:
        """
        移除早期消息以缩短上下文

        Returns:
            bool: True 表示成功移除消息，False 表示无法移除
        """
        # 查找第一条非系统消息的 user 消息（跳过第一条）
        for i in range(1, len(messages)):
            if messages[i]["role"] == "user":
                removed = messages.pop(i)
                logger.info(f"已移除第 {i} 条消息（角色: {removed['role']}）")
                return True

        logger.warning("没有可移除的消息，停止重试")
        return False
