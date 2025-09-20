#!/usr/bin/env python3
"""
AI驱动的每日新闻汇总器
使用OpenAI + MCP Fetch + Python差异检测的智能内容聚合系统
"""

import os
import sys
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

# 添加脚本目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from ai_content_extractor import AIContentExtractor
from utils.content_differ import ContentDiffer
from utils.digest_generator import DigestGenerator


class SmartDailyAggregator:
    """智能每日内容聚合器"""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()

        # 初始化组件
        ai_config = self.config.get('ai_config', {})
        self.ai_extractor = AIContentExtractor(ai_config)
        self.content_differ = ContentDiffer()
        self.digest_generator = DigestGenerator()

        # 初始化HTTP会话
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            sys.exit(1)


    def _build_url(self, source_config: Dict[str, Any]) -> str:
        """
        根据配置动态构建URL

        支持的模式变量：
        - {year}: 年份 (如: 2025)
        - {month}: 月份 (如: 9)
        - {month:02d}: 补零的月份 (如: 09)
        """
        base_url = source_config.get('base_url', '')
        url_pattern = source_config.get('url_pattern', '')

        if not url_pattern:
            # 如果没有模式，直接返回base_url（兼容旧配置）
            return source_config.get('url', base_url)

        # 获取当前日期
        now = datetime.now(timezone.utc)

        # 构建URL
        try:
            path = url_pattern.format(
                year=now.year,
                month=now.month
            )
            full_url = base_url + path
            print(f"动态生成URL: {full_url}")
            return full_url
        except Exception as e:
            print(f"URL构建失败: {e}")
            # 降级到base_url
            return base_url

    def _fetch_content_with_requests(self, url: str) -> str:
        """
        使用requests库获取网页内容
        """
        try:
            print(f"正在获取网页内容: {url}")

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # 检查内容类型
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                print(f"⚠️ 网页内容类型不是HTML: {content_type}")
                return ""

            # 获取编码
            encoding = response.encoding or 'utf-8'
            html_content = response.content.decode(encoding, errors='ignore')

            print(f"✅ 成功获取网页内容，长度: {len(html_content)} 字符")
            return html_content

        except requests.exceptions.RequestException as e:
            print(f"❌ 获取网页内容失败: {e}")
            return ""
        except Exception as e:
            print(f"❌ 处理网页内容时出错: {e}")
            return ""


    def process_source(self, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个数据源"""
        source_name = source_config['name']

        print(f"\n🔍 处理数据源: {source_config['display_name']}")

        try:
            # 1. 动态构建URL
            source_url = self._build_url(source_config)

            # 2. 获取网页内容 (使用requests)
            html_content = self._fetch_content_with_requests(source_url)
            if not html_content:
                print(f"  ⚠️ 无法获取 {source_name} 的网页内容")
                return {
                    'source': source_config,
                    'new_recommendations': [],
                    'status': 'fetch_failed'
                }

            # 3. AI提取今日内容
            print(f"  🤖 使用AI提取内容...")
            current_data = self.ai_extractor.extract_recommendations(
                html_content,
                source_config
            )

            # 直接使用今日提取的推荐内容
            recommendations = current_data.get('recommendations', [])
            print(f"  ✅ 完成，找到 {len(recommendations)} 个今日推荐")

            return {
                'source': source_config,
                'new_recommendations': recommendations,
                'total_extracted': len(recommendations),
                'status': 'success'
            }

        except Exception as e:
            print(f"  ❌ 处理 {source_name} 时出错: {e}")
            return {
                'source': source_config,
                'new_recommendations': [],
                'status': 'error',
                'error': str(e)
            }

    def run(self) -> bool:
        """运行智能聚合任务"""
        print("🚀 开始执行AI驱动的每日内容聚合...")
        print(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        sources_data = {}
        total_new_items = 0

        # 处理每个启用的数据源
        enabled_sources = [
            source for source in self.config['sources']
            if source.get('enabled', True)
        ]

        print(f"📋 将处理 {len(enabled_sources)} 个数据源")

        for source_config in enabled_sources:
            result = self.process_source(source_config)

            source_name = source_config['name']
            sources_data[source_name] = {
                'config': source_config,
                'new_articles': result['new_recommendations']  # 保持与原接口兼容
            }

            total_new_items += len(result['new_recommendations'])

        # 生成每日汇总
        if total_new_items > 0:
            print(f"\n📝 生成每日汇总 (共 {total_new_items} 个新项目)...")

            output_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'data', 'daily-digest'
            )
            output_file = self.digest_generator.get_output_filename(output_dir)

            success = self.digest_generator.generate_daily_digest(sources_data, output_file)

            if success:
                print(f"✅ 每日汇总生成成功: {os.path.basename(output_file)}")
                print(f"📍 文件位置: {output_file}")
                return True
            else:
                print("❌ 每日汇总生成失败")
                return False
        else:
            print("\n📭 今日没有发现新增内容")
            return False

    def add_new_source(self, name: str, base_url: str, url_pattern: str, display_name: str, icon: str = "🔗") -> bool:
        """动态添加新数据源"""
        new_source = {
            "name": name,
            "display_name": display_name,
            "base_url": base_url,
            "url_pattern": url_pattern,
            "icon": icon,
            "enabled": True
        }

        self.config['sources'].append(new_source)

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            print(f"✅ 新数据源 '{display_name}' 添加成功")
            return True
        except Exception as e:
            print(f"❌ 添加新数据源失败: {e}")
            return False


def main():
    """主函数"""
    print("=" * 60)
    print("🤖 AI驱动的每日新闻汇总器")
    print("=" * 60)

    # 获取配置文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, '..', 'config', 'sources.json')

    # 创建并运行聚合器
    try:
        aggregator = SmartDailyAggregator(config_path)
        success = aggregator.run()

        print("\n" + "=" * 60)
        if success:
            print("🎉 任务执行成功！")
        else:
            print("⚠️  任务完成，但没有新内容")
        print("=" * 60)

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⏹️  任务被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 任务执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()