import os
import json
import openai
from typing import Dict, List, Any, Optional
from datetime import datetime


class AIContentExtractor:
    """AI内容提取器"""

    def __init__(self, ai_config: Dict[str, Any] = None):
        # 初始化OpenAI客户端
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        # 获取base URL（可选）
        base_url = os.getenv('OPENAI_BASE_URL')

        # 初始化客户端
        if base_url:
            self.client = openai.Client(api_key=api_key, base_url=base_url)
            print(f"使用自定义OpenAI Base URL: {base_url}")
        else:
            self.client = openai.Client(api_key=api_key)
            print("使用默认OpenAI API")
        self.model = os.getenv('MODEL_NAME')
        
        # 从配置中获取模型参数，使用默认值作为后备
        self.ai_config = ai_config or {}
        self.max_tokens = self.ai_config.get('max_tokens', 3000)
        self.temperature = self.ai_config.get('temperature', 0.1)

        print(f"AI配置: 模型={self.model}, 最大token={self.max_tokens}, 温度={self.temperature}")

        # 加载prompt模板
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """加载prompt模板"""
        template_path = os.path.join(
            os.path.dirname(__file__),
            'prompt_templates',
            'content_extraction.txt'
        )
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # 如果文件不存在，使用内置模板
            return self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        """如果模板文件不存在时的错误处理"""
        raise FileNotFoundError("Prompt template file not found and no default available")

    def extract_recommendations(self, html_content: str, source_info: Dict = None) -> Dict[str, Any]:
        """
        从HTML内容中提取推荐项目

        Args:
            html_content: 网页HTML内容
            source_info: 数据源信息（可选）

        Returns:
            提取结果的字典
        """
        try:
            # 构建prompt
            prompt = self.prompt_template.format(html_content=html_content)

            print(f"开始AI内容提取...")

            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的网页内容分析师，擅长从HTML中提取推荐内容。请严格按照JSON格式回复。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            # 解析返回结果
            result_text = response.choices[0].message.content
            print(f"AI返回原始内容: {repr(result_text)}")
            result = json.loads(result_text)

            print(f"AI提取完成，找到 {len(result.get('recommendations', []))} 个推荐项目")

            # 验证和清理结果
            return self._validate_and_clean_result(result)

        except json.JSONDecodeError as e:
            print(f"AI返回结果JSON解析失败: {e}")
            return self._get_empty_result()
        except Exception as e:
            print(f"AI内容提取失败: {e}")
            return self._get_empty_result()

    def _validate_and_clean_result(self, result: Dict) -> Dict[str, Any]:
        """验证和清理AI提取结果"""
        if not isinstance(result, dict):
            return self._get_empty_result()

        recommendations = result.get('recommendations', [])
        valid_recommendations = []

        for rec in recommendations:
            # 验证必需字段
            if not isinstance(rec, dict):
                continue

            title = rec.get('title', '').strip()
            url = rec.get('url', '').strip()

            if not title or not url:
                continue

            # 确保URL是有效的
            if not (url.startswith('http://') or url.startswith('https://')):
                if url.startswith('//'):
                    url = 'https:' + url
                elif url.startswith('/'):
                    continue  # 相对路径，跳过
                else:
                    url = 'https://' + url

            # 清理并标准化数据
            cleaned_rec = {
                'title': title,
                'url': url,
                'description': rec.get('description', '').strip(),
                'date': rec.get('date'),
                'source_date_section': rec.get('source_date_section', ''),
                'confidence': min(max(rec.get('confidence', 0.8), 0), 1),
                'extracted_at': datetime.now().isoformat()
            }

            valid_recommendations.append(cleaned_rec)

        return {
            'recommendations': valid_recommendations,
            'page_info': result.get('page_info', {
                'total_found': len(valid_recommendations),
                'extraction_confidence': 0.8,
                'page_type': 'unknown'
            }),
            'extraction_timestamp': datetime.now().isoformat()
        }

    def _get_empty_result(self) -> Dict[str, Any]:
        """返回空结果"""
        return {
            'recommendations': [],
            'page_info': {
                'total_found': 0,
                'extraction_confidence': 0,
                'page_type': 'unknown'
            },
            'extraction_timestamp': datetime.now().isoformat()
        }