import asyncio
from contextlib import asynccontextmanager
from typing import Annotated
from uvicorn import run as asgi_run
from fastapi import (
    FastAPI,
    Request,
    Response,
    APIRouter,
    BackgroundTasks,
    UploadFile,
    File,
)
from queue import Queue, Empty


task_queue = asyncio.Queue()


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(process_task_queue())
    yield


async def process_task_queue():
    while True:
        try:

            # task = await task_queue.get(block=False, timeout=5000)  # , timeout=5000
            task = await task_queue.get()
            await task
            print(task)
            task_queue.task_done()
        except Empty as e:
            # print(e)
            break
        else:
            pass


app = FastAPI(lifespan=lifespan)


async def example_task(number: int):
    await asyncio.sleep(2)
    print(f"Завдання {number} виконано")


@app.post("/add-task/")
async def add_task(
    background_tasks: BackgroundTasks,
    number: int,
):
    task = example_task(number)
    await task_queue.put(task)
    return {"message": f"Завдання {number} додано до черги"}


async def process_file(filename: str, filecontent: Annotated[bytes, File()]):
    await asyncio.sleep(5)

    with open(f"{filename}", "wb") as save_file:
        save_file.write(filecontent)

    print(f"Файл {filename} оброблено")


async def send_email(email: str):
    await asyncio.sleep(2)
    print(f"Email sent to {email}")


@app.post("/upload-file/")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    background_tasks.add_task(
        process_file,
        filename=file.filename,
        filecontent=file.file.read(),
    )
    return {"message": f"Файл {file.filename} завантажується та обробляється у фоні"}


@app.post("/send-email/")
async def send_email_endpoint(background_tasks: BackgroundTasks, email: str):
    background_tasks.add_task(send_email, email)

    return {"message": "Email sending in the background"}


@app.get("/")
async def read_root():
    return {"message": "Welcome to FastAPI with async tasks"}


if __name__ == "__main__":
    asgi_run(app=app)
