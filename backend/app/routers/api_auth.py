from fastapi import APIRouter
router = APIRouter()

@router.get("/me")
async def me():
    # заглушка авторизации
    return {"user": None}
