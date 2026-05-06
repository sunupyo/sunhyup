from typing import Dict, Optional

from ..models import Platform
from .base import BaseCrawler
from .demo import DemoCrawler
from .xgolf import XgolfCrawler


_REGISTRY: Dict[str, BaseCrawler] = {
    Platform.DEMO.value: DemoCrawler(),
    Platform.XGOLF.value: XgolfCrawler(),
    # Phase 2 에서 추가:
    # Platform.KGOLF.value: KgolfCrawler(),
    # Platform.GOLFZON.value: GolfzonCrawler(),
}


def get_crawler(platform: str) -> Optional[BaseCrawler]:
    return _REGISTRY.get(platform)
