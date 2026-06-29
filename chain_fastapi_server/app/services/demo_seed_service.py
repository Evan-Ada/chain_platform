"""Demo 数据种子：SSR 订阅、推送偏好、热点样例。"""

from __future__ import annotations

import hashlib

from loguru import logger
from sqlmodel import Session, select

from app.models import (
    ContentRecord,
    DataSourceConfig,
    PushPreference,
    Subscription,
    User,
)
from app.services.scheduler_v2 import ScheduledTaskService
from app.services.tag_service import TagService

KR36_SSR_CONFIG: dict = {
    "list_urls": [
        "https://36kr.com/information/web_news/latest",
        "https://36kr.com/information/technology/latest",
        "https://36kr.com/information/business/latest",
    ],
    "max_items_per_url": 20,
    "tag_categories": ["topic", "industry"],
    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "timeout_seconds": 25,
    "retry_times": 2,
}

DEMO_CONTENT_SAMPLES: list[dict] = [
    {
        "title": "OpenAI 发布新模型，人工智能赛道再升温",
        "content": "大模型能力持续提升，AI 应用落地加速。",
        "source_url": "https://36kr.com/p/demo-1",
        "keywords_matched": ["人工智能"],
    },
    {
        "title": "英伟达 H200 量产，半导体供应链紧张",
        "content": "高端芯片需求旺盛，半导体产业链关注度高。",
        "source_url": "https://36kr.com/p/demo-2",
        "keywords_matched": ["半导体"],
    },
    {
        "title": "央行降准释放流动性，宏观经济预期改善",
        "content": "财经政策面向实体经济倾斜，市场信心回升。",
        "source_url": "https://36kr.com/p/demo-3",
        "keywords_matched": ["宏观经济", "财经"],
    },
    {
        "title": "头部互联网公司组织调整引关注",
        "content": "互联网板块人事与业务线变动频繁。",
        "source_url": "https://36kr.com/p/demo-4",
        "keywords_matched": ["互联网"],
    },
    {
        "title": "加密货币监管新规征求意见稿发布",
        "content": "数字资产合规框架逐步完善。",
        "source_url": "https://36kr.com/p/demo-5",
        "keywords_matched": ["加密货币"],
    },
    {
        "title": "网络安全攻防演练揭示新风险",
        "content": "企业级安全投入持续增加。",
        "source_url": "https://36kr.com/p/demo-6",
        "keywords_matched": ["网络安全"],
    },
]


def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


class DemoSeedService:
    """幂等写入演示/初始业务数据。"""

    @staticmethod
    def seed_all(db: Session) -> None:
        TagService.seed_default_tags(db)
        user = DemoSeedService._get_first_user(db)
        if not user:
            logger.warning("无用户，跳过 demo seed")
            return
        DemoSeedService._seed_datasource(db)
        sub = DemoSeedService._seed_subscription(db, user.id)
        DemoSeedService._seed_push_preference(db, user.id)
        if sub:
            DemoSeedService._seed_demo_content(db, sub.id)

    @staticmethod
    def _get_first_user(db: Session) -> User | None:
        from app.core.config import settings

        admin = db.exec(
            select(User).where(User.username == settings.FIRST_SUPERUSER)
        ).first()
        if admin:
            return admin
        return db.exec(select(User).order_by(User.id)).first()

    @staticmethod
    def _seed_datasource(db: Session) -> None:
        existing = db.exec(
            select(DataSourceConfig).where(DataSourceConfig.source_type == "ssr")
        ).first()
        if existing:
            logger.info("DataSourceConfig(ssr) 已存在，跳过")
            return
        db.add(
            DataSourceConfig(
                name="36kr-ssr",
                source_type="ssr",
                enabled=True,
                config=KR36_SSR_CONFIG,
            )
        )
        db.commit()
        logger.info("已 seed DataSourceConfig(ssr)")

    @staticmethod
    def _seed_subscription(db: Session, user_id: int) -> Subscription | None:
        existing = db.exec(select(Subscription)).first()
        if existing:
            logger.info("Subscription 已存在，跳过")
            return existing
        sub = Subscription(
            name="36kr-标签订阅",
            user_id=user_id,
            keywords=[],
            sources=["ssr"],
            schedule_type="daily",
            schedule_cron="0 8 * * *",
            enabled=True,
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        ScheduledTaskService.upsert_from_subscription(sub)
        logger.info(f"已 seed Subscription id={sub.id}")
        return sub

    @staticmethod
    def _seed_push_preference(db: Session, user_id: int) -> None:
        existing = db.get(PushPreference, user_id)
        if existing:
            logger.info("PushPreference 已存在，跳过")
            return
        db.add(
            PushPreference(
                id=user_id,
                channels={"email": False, "app": True},
                push_time="08:30:00",
                timezone="Asia/Shanghai",
                daily_digest=True,
                importance_filter=["high", "medium"],
            )
        )
        db.commit()
        logger.info(f"已 seed PushPreference user_id={user_id}")

    @staticmethod
    def _seed_demo_content(db: Session, subscription_id: int) -> None:
        existing = db.exec(select(ContentRecord)).first()
        if existing:
            logger.info("ContentRecord 已有数据，跳过样例")
            return
        for sample in DEMO_CONTENT_SAMPLES:
            url = sample["source_url"]
            db.add(
                ContentRecord(
                    subscription_id=subscription_id,
                    title=sample["title"],
                    content=sample["content"],
                    source_url=url,
                    source_name="36kr",
                    url_hash=_url_hash(url),
                    keywords_matched=sample["keywords_matched"],
                    llm_status="pending",
                )
            )
        db.commit()
        logger.info(f"已 seed {len(DEMO_CONTENT_SAMPLES)} 条 ContentRecord 样例")
