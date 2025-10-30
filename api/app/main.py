
from app.api import scrape
app.include_router(scrape.router, prefix="/api", tags=["scrape"])
