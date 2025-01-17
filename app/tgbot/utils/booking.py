from datetime import datetime, timedelta

async def get_available_dates(sheets_service):
    return await sheets_service.get_available_dates()

async def get_available_times(sheets_service, date, table_pref):
    return await sheets_service.get_available_times(date, table_pref)

async def get_available_end_times(sheets_service, date, start_time):
    return await sheets_service.get_available_end_times(date, start_time)
