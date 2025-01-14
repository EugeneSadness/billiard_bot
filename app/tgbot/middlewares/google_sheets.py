from aiogram import BaseMiddleware
from app.infrastructure.google.sheets_service import GoogleSheetsService

class GoogleSheetsMiddleware(BaseMiddleware):
    def __init__(self, sheets_service: GoogleSheetsService):
        self.sheets_service = sheets_service
        super().__init__()

    async def __call__(self, handler, event, data):
        data['sheets_service'] = self.sheets_service
        return await handler(event, data) 