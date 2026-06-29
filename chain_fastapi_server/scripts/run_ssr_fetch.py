"""手动触发 SSR 抓取并打印终端推送（联调脚本）。"""

import asyncio

from sqlmodel import Session, select

from app.core.db import engine
from app.models import Subscription
from app.services.content_fetch import ContentFetchService


async def main() -> None:
    with Session(engine) as db:
        sub = db.exec(select(Subscription).order_by(Subscription.id)).first()
        if not sub:
            print("无 Subscription，请先运行: uv run python app/initial_data.py")
            return
        print(f"触发抓取 subscription_id={sub.id} name={sub.name}")
        service = ContentFetchService()
        new_count = await service.fetch_and_save(sub, db)
        print(f"完成，新增 {new_count} 条（终端应已打印 [PUSH] 摘要）")


if __name__ == "__main__":
    asyncio.run(main())
