from fastapi.responses import JSONResponse


def success(data=None, message: str = "Operation successful", status_code: int = 200):
    return JSONResponse(
        status_code=status_code,
        content={"success": True, "message": message, "data": data},
    )


def error(message: str = "Something went wrong", status_code: int = 400, data=None):
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "message": message, "data": data},
    )
