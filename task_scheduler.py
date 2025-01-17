import logging
from contextlib import suppress
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.repositories.booking_repository import BookingRepository

from taskiq import TaskiqScheduler, TaskiqEvents, TaskiqState, Context, TaskiqDepends
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_nats import NatsBroker

from app.tgbot.tgbot import create_db_session

broker = NatsBroker("nats://localhost:4222", queue="notifying")
scheduler = TaskiqScheduler(broker, [LabelScheduleSource(broker)])


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)-8s [%(asctime)s] :: %(name)s : %(message)s"
    )
    logger = logging.getLogger(__name__)
    logger.warning("Starting scheduler...")

    state.logger = logger


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(state: TaskiqState) -> None:
    state.logger.warning("Scheduler stopped")


@broker.task(task_name="notify", schedule=[{"cron": "* * * * *"}])
async def notify(context: Context = TaskiqDepends()) -> None:
    print("Оповещение!")


@broker.task(task_name="update_past_bookings", schedule=[{"cron": "0 3 * * *"}]) 
async def update_past_bookings(context: Context = TaskiqDepends()) -> None:
    try:
        # Create database session
        async_session = await create_db_session()
        async with async_session() as session:
            booking_repository = BookingRepository(session)
            updated_count = await booking_repository.update_past_bookings_status()
            logger = context.state.logger
            logger.info(f"Updated {updated_count} past bookings to completed status")
    except Exception as e:
        logger.error(f"Error updating past bookings: {e}")