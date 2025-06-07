from fastapi import APIRouter, UploadFile, Depends, HTTPException, status

from core.io.recording import save_temp
from worker.tasks import celery_app, recognize_audio_task
from celery.result import AsyncResult

router = APIRouter(prefix="/recognize", tags=["recognition"])

@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def start_recognition(file: UploadFile):
    """
    Accepts an audio file and starts the recognition process in the background.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    tmp_dir = "tmp"
    path = save_temp(file, dir=tmp_dir)

    # Dispatch the task to the Celery worker
    task = recognize_audio_task.delay(path)

    return {"task_id": task.id}


@router.get("/result/{task_id}")
def get_recognition_result(task_id: str):
    """
    Fetches the result of a recognition task.
    """
    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.state == 'PENDING':
        return {"status": "PENDING"}
    elif task_result.state == 'FAILURE':
        return {"status": "FAILURE", "error": str(task_result.info)}

    # Task is ready, return the result
    result = task_result.get()

    if result.get("status") == "NO_MATCH":
        raise HTTPException(status_code=404, detail="No match found.")

    return result
