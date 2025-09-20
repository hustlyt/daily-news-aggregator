#!/usr/bin/env python3
"""
测试脚本：演示完整的GitHub Actions工作流程
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from daily_aggregator import SmartDailyAggregator


def test_with_real_website():
    """测试真实网站的完整流程"""
    print("🧪 测试完整的AI内容聚合流程")
    print("=" * 50)

    # 获取配置文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, '..', 'config', 'sources.json')

    try:
        # 创建聚合器
        aggregator = SmartDailyAggregator(config_path)

        # 获取启用的数据源
        enabled_sources = aggregator.get_enabled_sources()
        print(f"📋 找到 {len(enabled_sources)} 个启用的数据源")

        for source in enabled_sources:
            print(f"  - {source['display_name']}: {source['url']}")

        # 运行聚合
        print(f"\n🚀 开始运行聚合...")
        success = aggregator.run()

        if success:
            print("\n✅ 测试成功！查看 data/daily-digest/ 目录中的生成文件")
        else:
            print("\n📭 测试完成，但没有发现新内容")

        return success

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_with_real_website()