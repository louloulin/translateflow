import hashlib
from ModuleFolders.Base.Base import Base
from ModuleFolders.Infrastructure.LLMRequester.LLMClientFactory import LLMClientFactory


# 接口请求器
class OpenaiRequester(Base):
    def __init__(self) -> None:
        pass

    def _get_api_cache_key(self, api_url: str, model_name: str) -> str:
        """生成API缓存键，基于URL和模型名"""
        key_str = f"{api_url}:{model_name}"
        return hashlib.md5(key_str.encode()).hexdigest()[:16]

    def _get_stream_support_status(self, api_url: str, model_name: str) -> bool | None:
        """获取API的流式支持状态，None表示未知"""
        config = self.load_config()
        cache = config.get("stream_api_cache", {})
        cache_key = self._get_api_cache_key(api_url, model_name)
        return cache.get(cache_key)

    def _set_stream_support_status(self, api_url: str, model_name: str, supports_stream: bool) -> None:
        """设置API的流式支持状态"""
        config = self.load_config()
        cache = config.get("stream_api_cache", {})
        cache_key = self._get_api_cache_key(api_url, model_name)
        cache[cache_key] = supports_stream
        config["stream_api_cache"] = cache
        self.save_config(config)

    def _parse_sse_response(self, raw_text: str) -> tuple[str, str, int, int]:
        """解析SSE格式响应"""
        import json
        full_content = ""
        full_think = ""
        usage = {"prompt_tokens": 0, "completion_tokens": 0}
        lines = raw_text.split("\n")
        for line in lines:
            if line.startswith("data:"):
                json_str = line.replace("data:", "").strip()
                if json_str == "[DONE]":
                    break
                try:
                    res_json = json.loads(json_str)
                    if isinstance(res_json, dict) and "choices" in res_json:
                        choice = res_json["choices"][0]
                        delta = choice.get("delta", {})
                        c = delta.get("content", "")
                        if c:
                            full_content += c
                        t = delta.get("reasoning_content", "")
                        if t:
                            full_think += t
                    if isinstance(res_json, dict) and "usage" in res_json and res_json["usage"]:
                        usage["prompt_tokens"] = res_json["usage"].get("prompt_tokens", 0)
                        usage["completion_tokens"] = res_json["usage"].get("completion_tokens", 0)
                except:
                    continue
        return full_think, full_content, int(usage["prompt_tokens"]), int(usage["completion_tokens"])

    def _parse_json_response(self, response_json: dict) -> tuple[str, str, int, int]:
        """解析JSON格式响应"""
        message = response_json["choices"][0]["message"]
        content = message.get("content", "")

        # 自适应提取推理过程
        response_think = ""
        response_content = content
        if content and "</think>" in content:
            splited = content.split("</think>")
            response_think = splited[0].removeprefix("<think>").replace("\n\n", "\n")
            response_content = splited[-1]
        else:
            response_think = message.get("reasoning_content", "")

        prompt_tokens = response_json.get("usage", {}).get("prompt_tokens", 0)
        completion_tokens = response_json.get("usage", {}).get("completion_tokens", 0)

        return response_think, response_content, int(prompt_tokens), int(completion_tokens)

    def _do_request(self, api_url: str, api_key: str, request_body: dict,
                    request_timeout: int, use_stream: bool) -> tuple[bool, str, str, int, int]:
        """执行实际的HTTP请求"""
        import httpx

        request_body["stream"] = use_stream
        if use_stream:
            request_body["stream_options"] = {"include_usage": True}

        auth_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        with httpx.Client(timeout=request_timeout) as http_client:
            resp = http_client.post(api_url, json=request_body, headers=auth_headers)

            if resp.status_code != 200:
                raise Exception(f"HTTP {resp.status_code}: {resp.text}")

            raw_text = resp.text.strip()

            # 处理 SSE 格式或普通 JSON 格式
            if raw_text.startswith("data:"):
                think, content, pt, ct = self._parse_sse_response(raw_text)
                return False, think, content, pt, ct
            else:
                response_json = resp.json()
                think, content, pt, ct = self._parse_json_response(response_json)
                return False, think, content, pt, ct

    # 发起请求
    def request_openai(self, messages, system_prompt, platform_config) -> tuple[bool, str, str, int, int]:
        try:
            # 获取具体配置
            model_name = platform_config.get("model_name")
            request_timeout = platform_config.get("request_timeout", 60)
            temperature = platform_config.get("temperature", 1.0)
            top_p = platform_config.get("top_p", 1.0)
            presence_penalty = platform_config.get("presence_penalty", 0)
            frequency_penalty = platform_config.get("frequency_penalty", 0)
            extra_body = platform_config.get("extra_body", {})
            think_switch = platform_config.get("think_switch")
            think_depth = platform_config.get("think_depth")
            enable_stream = platform_config.get("enable_stream_api", True)

            # 插入系统消息
            if system_prompt:
                messages.insert(0, {"role": "system", "content": system_prompt})

            # 从工厂获取客户端
            client = LLMClientFactory().get_openai_client(platform_config)

            # 针对ds模型的特殊处理
            if model_name and 'deepseek' in model_name.lower():
                if messages and isinstance(messages[-1], dict) and messages[-1].get('role') != 'user':
                    messages = messages[:-1]

            # 构建请求体
            request_body = {
                "model": model_name,
                "messages": messages,
            }

            if extra_body and isinstance(extra_body, dict):
                request_body.update(extra_body)

            if temperature != 1:
                request_body["temperature"] = temperature
            if top_p != 1:
                request_body["top_p"] = top_p
            if presence_penalty != 0:
                request_body["presence_penalty"] = presence_penalty
            if frequency_penalty != 0:
                request_body["frequency_penalty"] = frequency_penalty
            if think_switch:
                request_body["reasoning_effort"] = think_depth

            # 处理API URL
            api_url = platform_config.get("api_url").rstrip('/')
            if platform_config.get("auto_complete", False) and not api_url.endswith('/chat/completions'):
                api_url = f"{api_url}/chat/completions"
            api_key = platform_config.get("api_key")

            # 智能流式判断逻辑
            if enable_stream:
                stream_status = self._get_stream_support_status(api_url, model_name)

                if stream_status is True:
                    # 已知支持流式，直接使用流式
                    return self._do_request(api_url, api_key, request_body, request_timeout, True)
                elif stream_status is False:
                    # 已知不支持流式，直接使用非流式
                    return self._do_request(api_url, api_key, request_body, request_timeout, False)
                else:
                    # 未知状态，尝试流式请求
                    try:
                        result = self._do_request(api_url, api_key, request_body.copy(), request_timeout, True)
                        # 流式请求成功，标记为支持流式
                        self._set_stream_support_status(api_url, model_name, True)
                        return result
                    except Exception as stream_error:
                        # 流式请求失败，尝试非流式
                        error_str = str(stream_error).lower()
                        # 检查是否是流式不支持的错误
                        stream_error_keywords = ["stream", "unsupported", "not supported", "invalid"]
                        if any(k in error_str for k in stream_error_keywords):
                            try:
                                result = self._do_request(api_url, api_key, request_body.copy(), request_timeout, False)
                                # 非流式请求成功，标记为不支持流式
                                self._set_stream_support_status(api_url, model_name, False)
                                self.debug(f"API不支持流式，已标记并切换到非流式模式: {api_url}")
                                return result
                            except Exception as non_stream_error:
                                raise non_stream_error
                        else:
                            # 不是流式相关错误，直接抛出
                            raise stream_error
            else:
                # 流式功能关闭，直接使用非流式
                return self._do_request(api_url, api_key, request_body, request_timeout, False)

        except Exception as e:
            error_str = str(e).lower()
            error_type = "GENERIC_FAIL"

            api_error_keywords = [
                "429", "500", "502", "503", "timeout", "connection",
                "rate limit", "service unavailable", "bad gateway",
                "api_key", "insufficient_quota"
            ]

            if any(k in error_str for k in api_error_keywords):
                error_type = "API_FAIL"

            if Base.work_status != Base.STATUS.STOPING:
                api_url = platform_config.get("api_url", "Unknown URL")
                model_name = platform_config.get("model_name", "Unknown Model")
                self.error(f"请求任务错误 ({error_type}) [URL: {api_url}, Model: {model_name}] ... {e}",
                          e if self.is_debug() else None)
            else:
                self.print(f"[dim]Request aborted due to stop signal: {e}[/dim]")

            return True, error_type, str(e), 0, 0
