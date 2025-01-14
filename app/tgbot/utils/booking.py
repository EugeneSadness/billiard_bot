from datetime import datetime, timedelta

async def get_available_dates(sheets_service):
    return await sheets_service.get_available_dates()

async def get_available_times(sheets_service, date):
    return await sheets_service.get_available_times(date)
