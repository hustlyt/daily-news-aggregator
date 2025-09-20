import json
import hashlib
from typing import List, Dict, Set, Any
from datetime import datetime


class ContentDiffer:
    """基于Python的智能内容差异检测器"""

    def __init__(self):
        pass

    def generate_content_hash(self, recommendation: Dict) -> str:
        """为推荐项目生成唯一hash"""
        # 使用标题和URL生成hash，忽略描述的细微变化
        content = f"{recommendation.get('title', '')}{recommendation.get('url', '')}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def detect_new_recommendations(self, current_data: Dict, previous_data: Dict) -> List[Dict]:
        """
        检测新增的推荐项目

        Args:
            current_data: 当前提取的数据
            previous_data: 上次提取的数据

        Returns:
            新增的推荐项目列表
        """
        current_recs = current_data.get('recommendations', [])
        previous_recs = previous_data.get('recommendations', [])

        # 构建之前内容的hash集合
        previous_hashes = {
            self.generate_content_hash(rec) for rec in previous_recs
        }

        # 找出新增的项目
        new_recommendations = []
        for rec in current_recs:
            rec_hash = self.generate_content_hash(rec)
            if rec_hash not in previous_hashes:
                rec['is_new'] = True
                rec['content_hash'] = rec_hash
                new_recommendations.append(rec)

        return new_recommendations

    def detect_changes_summary(self, current_data: Dict, previous_data: Dict) -> Dict[str, Any]:
        """
        生成变化摘要

        Returns:
            变化摘要信息
        """
        current_recs = current_data.get('recommendations', [])
        previous_recs = previous_data.get('recommendations', [])

        current_hashes = {self.generate_content_hash(rec) for rec in current_recs}
        previous_hashes = {self.generate_content_hash(rec) for rec in previous_recs}

        new_items = current_hashes - previous_hashes
        removed_items = previous_hashes - current_hashes
        unchanged_items = current_hashes & previous_hashes

        return {
            'total_current': len(current_recs),
            'total_previous': len(previous_recs),
            'new_count': len(new_items),
            'removed_count': len(removed_items),
            'unchanged_count': len(unchanged_items),
            'has_changes': len(new_items) > 0 or len(removed_items) > 0,
            'change_timestamp': datetime.now().isoformat()
        }

    def filter_by_confidence(self, recommendations: List[Dict], min_confidence: float = 0.7) -> List[Dict]:
        """根据置信度过滤推荐项目"""
        return [
            rec for rec in recommendations
            if rec.get('confidence', 0) >= min_confidence
        ]

    def filter_by_date_relevance(self, recommendations: List[Dict], target_date: str = None) -> List[Dict]:
        """
        根据日期相关性过滤

        Args:
            recommendations: 推荐项目列表
            target_date: 目标日期，格式 YYYY-MM-DD，默认为今天
        """
        if target_date is None:
            target_date = datetime.now().strftime('%Y-%m-%d')

        relevant_recs = []
        today = datetime.now()

        for rec in recommendations:
            # 如果有明确的日期信息
            rec_date = rec.get('date')
            if rec_date and rec_date == target_date:
                relevant_recs.append(rec)
                continue

            # 如果有日期段信息，尝试解析
            date_section = rec.get('source_date_section', '')
            if self._is_recent_date_section(date_section, today):
                relevant_recs.append(rec)
                continue

            # 如果都没有，但是是新增项目，也认为是相关的
            if rec.get('is_new', False):
                relevant_recs.append(rec)

        return relevant_recs

    def _is_recent_date_section(self, date_section: str, reference_date: datetime) -> bool:
        """判断日期段是否是最近的"""
        if not date_section:
            return False

        # 简单的日期匹配逻辑
        # 可以根据实际需要扩展更复杂的日期解析
        import re

        # 匹配 "X月Y日" 格式
        match = re.search(r'(\d+)月(\d+)日', date_section)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))

            # 判断是否是当前月份的近期日期
            if month == reference_date.month:
                day_diff = abs(reference_date.day - day)
                return day_diff <= 3  # 3天内认为是最近的

        return False

    def merge_recommendations(self, *recommendation_lists: List[Dict]) -> List[Dict]:
        """合并多个推荐列表，去重"""
        seen_hashes = set()
        merged = []

        for rec_list in recommendation_lists:
            for rec in rec_list:
                rec_hash = self.generate_content_hash(rec)
                if rec_hash not in seen_hashes:
                    seen_hashes.add(rec_hash)
                    merged.append(rec)

        return merged