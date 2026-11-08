"""Server-rendered HTML pages. These will be replaced by the new web frontend."""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.routers.papers import get_paper_or_404
from app.security import DbSession

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)

router = APIRouter(include_in_schema=False, default_response_class=HTMLResponse)

SIMPLE_PAGES = {
    "/": "index.html",
    "/home": "homepage.html",
    "/content": "content_page.html",
    "/login": "login.html",
    "/register": "register.html",
    "/profile": "profile.html",
    "/upload": "upload_paper.html",
}


def _simple_page(template: str):
    def page(request: Request):
        return templates.TemplateResponse(request, template)

    return page


for path, template in SIMPLE_PAGES.items():
    router.add_api_route(path, _simple_page(template), methods=["GET"], name=template.removesuffix(".html"))


@router.get("/papers/{paper_id}")
def paper_page(request: Request, paper_id: str, db: DbSession):
    paper = get_paper_or_404(db, paper_id)
    return templates.TemplateResponse(request, "paper_view.html", {"paper": paper})
