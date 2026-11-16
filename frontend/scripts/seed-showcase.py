"""Populate the fresh local Docker database without modifying backend sources.

Run from the repository root: python frontend/scripts/seed-showcase.py
Only works on an empty catalog. Keeps existing accounts and makes a temporary
database backup before population. No email/Telegram notification is sent.
"""
import ast
import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tempfile


if "--inside" not in sys.argv:
    backup = Path(tempfile.gettempdir()) / ("api-rope-shop-before-showcase-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".sql")
    result = subprocess.run(
        ["docker", "exec", "postgres_rope_shopo", "pg_dump", "-U", "postgres", "-d", "api_rope_shop"],
        check=True, capture_output=True,
    )
    backup.write_bytes(result.stdout)
    print(f"Database backup: {backup}", flush=True)
    subprocess.run(
        ["docker", "exec", "-i", "backend_rope_shopo", "python", "-", "--inside", *sys.argv[1:]],
        input=Path(__file__).read_bytes(), check=True,
    )
    sys.exit(0)


class ShowcaseSource(ast.NodeTransformer):
    """Adapt literal seed content in memory; the original source stays intact."""

    def visit_Constant(self, node):
        value = node.value
        if not isinstance(value, str):
            return node
        if value.startswith("/assets/"):
            if "/charity/" in value:
                value = "/img/charity/seniors-help.optimized.webp"
            elif "soft_shackle" in value:
                value = "/img/hero/soft-shackle-blue.mobile.webp"
            elif "eye" in value or "aug_splice" in value or "pilotauge" in value:
                value = "/img/hero/rope-eye-blue.optimized.webp"
            elif "cruising" in value or "dyneema" in value:
                value = "/img/works/rope-blue.optimized.webp"
            elif "sk99" in value or "dinghy" in value:
                value = "/img/works/rope-red.optimized.webp"
            elif "oceanflex" in value or "squareline" in value:
                value = "/img/catalog/magic-race.optimized.webp"
            else:
                value = "/img/works/photo1.optimized.webp"
        if re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            value = value.split("@")[0] + "@example.com"
        value = value.replace("Nordic Rigging & Rope Works", "Rope-Pro-Line")
        value = value.replace("https://nordic-ropes.com", "http://localhost")
        value = value.replace("Mainsheet test order - cancelled by customer due to regatta postpone", "Mainsheet order cancelled following a change in the regatta schedule")
        return ast.copy_location(ast.Constant(value=value), node)

    def visit_Await(self, node):
        # Do not delete users or their sessions when preparing the fresh database.
        if ast.unparse(node) in (
            "await session.execute(delete(User))",
            "await session.execute(delete(RefreshToken))",
        ):
            return ast.copy_location(ast.Constant(value=None), node)
        return self.generic_visit(node)

    def visit_keyword(self, node):
        if node.arg in ("telegram_notifications_enabled", "email_notifications_enabled", "manager_email_notifications_enabled"):
            node.value = ast.Constant(value=False)
        elif node.arg == "telegram_chat_id":
            node.value = ast.Constant(value="")
        elif node.arg == "password":
            node.value = ast.Constant(value=secrets.token_urlsafe(24))
        return self.generic_visit(node)


source_path = Path("/app/src/tools/create_test_data.py")
tree = ShowcaseSource().visit(ast.parse(source_path.read_text(encoding="utf-8")))
ast.fix_missing_locations(tree)
seed = {"__file__": str(source_path), "__name__": "showcase_seed"}
exec(compile(tree, str(source_path), "exec"), seed)

from sqlalchemy import select, func, text
from sqlalchemy.orm import selectinload

original_create_user = seed["create_user_factory"]


async def keep_accounts(session, crypto_context, new_user):
    existing = await session.scalar(select(seed["User"]).where(seed["User"].username == new_user.username))
    if existing:
        return existing
    return await original_create_user(session, crypto_context, new_user)


seed["create_user_factory"] = keep_accounts


async def main():
    conf = seed["Config"]()
    if "--finalize" not in sys.argv:
        async with conf.db_connection.session_local() as session:
            for name in ("Product", "QuoteRequest", "Review", "Category", "ContentBlock"):
                if await session.scalar(select(func.count()).select_from(seed[name])):
                    raise RuntimeError("Catalog/content is already populated; refusing to overwrite it.")
        await seed["clear_database"](conf)
        await seed["fill_data"](conf)
    async with conf.db_connection.session_local() as session:
        Quote = seed["QuoteRequest"]
        quotes = (await session.scalars(select(Quote).options(
            selectinload(Quote.rope_items), selectinload(Quote.service_items), selectinload(Quote.extra_items),
        ).order_by(Quote.id))).all()
        now = datetime.now(timezone.utc)
        money = lambda value: Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        for index, quote in enumerate(quotes):
            costs = [money(item.total_cost) for item in quote.rope_items + quote.service_items + quote.extra_items]
            quote.subtotal = sum(costs, Decimal("0.00"))
            quote.total_price = money((quote.subtotal + quote.urgent_surcharge) * (1 + quote.vat_rate / 100))
            quote.created_at = now - timedelta(days=index * 3, hours=index + 1)
            quote.updated_at = quote.created_at + timedelta(minutes=30)
        # Continue numbering after the six prefilled requests.
        if await session.scalar(text("SELECT to_regclass('quote_request_number_seq')")):
            await session.execute(text("SELECT setval('quote_request_number_seq', :number, true)"), {"number": len(quotes)})
        else:
            print("Backend issue: quote_request_number_seq missing; schema left unchanged.")
        for index, review in enumerate((await session.scalars(select(seed["Review"]).order_by(seed["Review"].id))).all()):
            review.created_at = now - timedelta(days=8 + index * 9)
        await session.commit()
        for name in ("Product", "ProductVariant", "Category", "Color", "MaterialGroup", "Material", "SpliceMaterial", "SpliceType", "SplicePriceRule", "ConfiguratorExtra", "ProductApplication", "ProductSpecification", "ProductImage", "QuoteRequest", "Review", "WorkPhoto", "CharityPhoto", "ContentBlock", "ContactRequest", "User"):
            count = await session.scalar(select(func.count()).select_from(seed[name]))
            print(f"{name}: {count}")
    await conf.db_connection.engine.dispose()


asyncio.run(main())
