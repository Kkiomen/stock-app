"""
FastAPI server z poprawionym loggingiem
"""
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import subprocess
import logging
import asyncio
from typing import Optional
import os
import sys

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/analysis.log')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Stock Analysis API", version="1.0.0")

class AnalysisRequest(BaseModel):
    ticker: str
    trends: str
    start_date: str
    test_size_pct: float = 0.15
    forecast_days: int = 20

class AnalysisResponse(BaseModel):
    success: bool
    message: str
    task_id: Optional[str] = None

# Słownik do śledzenia aktywnych zadań
active_tasks = {}

@app.get("/")
async def root():
    return {"message": "Stock Analysis API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "stock-analysis"}

@app.post("/analyze", response_model=AnalysisResponse)
async def run_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Uruchom analizę giełdową w tle
    """
    try:
        # Walidacja parametrów
        if request.test_size_pct < 0.05 or request.test_size_pct > 0.5:
            raise HTTPException(
                status_code=400,
                detail="test_size_pct musi być między 0.05 a 0.5"
            )

        if request.forecast_days < 1 or request.forecast_days > 90:
            raise HTTPException(
                status_code=400,
                detail="forecast_days musi być między 1 a 90"
            )

        # Generuj ID zadania
        task_id = f"{request.ticker}_{int(asyncio.get_event_loop().time())}"

        logger.info(f"🚀 Tworzenie nowego zadania: {task_id}")
        logger.info(f"📊 Parametry: ticker={request.ticker}, start={request.start_date}, test_pct={request.test_size_pct}, forecast={request.forecast_days}")

        # Dodaj zadanie do śledzenia
        active_tasks[task_id] = {
            "status": "running",
            "parameters": request.dict(),
            "logs": []
        }

        # Uruchom analizę w tle
        background_tasks.add_task(
            run_analysis_task,
            task_id,
            request.ticker,
            request.trends,
            request.start_date,
            request.test_size_pct,
            request.forecast_days
        )

        return AnalysisResponse(
            success=True,
            message=f"Analiza dla {request.ticker} została uruchomiona w tle",
            task_id=task_id
        )

    except Exception as e:
        logger.error(f"❌ Błąd podczas uruchamiania analizy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyze/{task_id}")
async def get_analysis_status(task_id: str):
    """
    Sprawdź status zadania analizy
    """
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Zadanie nie znalezione")

    return active_tasks[task_id]

@app.get("/analyze/{task_id}/logs")
async def get_analysis_logs(task_id: str):
    """
    Pobierz logi zadania analizy
    """
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Zadanie nie znalezione")

    return {
        "task_id": task_id,
        "logs": active_tasks[task_id].get("logs", []),
        "status": active_tasks[task_id].get("status", "unknown")
    }

@app.post("/analyze/sync", response_model=AnalysisResponse)
async def run_analysis_sync(request: AnalysisRequest):
    """
    Uruchom analizę synchronicznie (może trwać długo)
    """
    try:
        logger.info(f"🔄 Synchroniczne uruchomienie analizy dla {request.ticker}")

        # Uruchom analizę bezpośrednio
        result = await run_analysis_subprocess(
            request.ticker,
            request.trends,
            request.start_date,
            request.test_size_pct,
            request.forecast_days
        )

        if result["success"]:
            logger.info(f"✅ Synchroniczna analiza zakończona pomyślnie dla {request.ticker}")
            return AnalysisResponse(
                success=True,
                message=f"Analiza dla {request.ticker} zakończona pomyślnie"
            )
        else:
            logger.error(f"❌ Synchroniczna analiza nieudana dla {request.ticker}: {result['error']}")
            raise HTTPException(
                status_code=500,
                detail=f"Błąd analizy: {result['error']}"
            )

    except Exception as e:
        logger.error(f"❌ Błąd podczas synchronicznej analizy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_analysis_task(task_id: str, ticker: str, trends: str, start_date: str, test_size_pct: float, forecast_days: int):
    """
    Zadanie w tle do uruchomienia analizy
    """
    try:
        logger.info(f"🎯 Rozpoczęcie analizy {task_id} dla {ticker}")

        # Aktualizuj status
        active_tasks[task_id]["status"] = "running"
        active_tasks[task_id]["start_time"] = asyncio.get_event_loop().time()
        active_tasks[task_id]["logs"].append(f"Rozpoczęcie analizy dla {ticker}")

        # Uruchom analizę
        result = await run_analysis_subprocess(ticker, trends, start_date, test_size_pct, forecast_days)

        # Aktualizuj status końcowy
        active_tasks[task_id]["status"] = "completed" if result["success"] else "failed"
        active_tasks[task_id]["end_time"] = asyncio.get_event_loop().time()
        active_tasks[task_id]["result"] = result

        # Dodaj logi z subprocess do zadania
        if "output" in result:
            active_tasks[task_id]["logs"].extend(result["output"].split('\n'))

        logger.info(f"🏁 Analiza {task_id} zakończona: {result['success']}")

    except Exception as e:
        logger.error(f"💥 Błąd w zadaniu {task_id}: {e}")
        active_tasks[task_id]["status"] = "failed"
        active_tasks[task_id]["error"] = str(e)
        active_tasks[task_id]["logs"].append(f"BŁĄD: {str(e)}")

async def run_analysis_subprocess(ticker: str, trends: str, start_date: str, test_size_pct: float, forecast_days: int):
    """
    Uruchom skrypt analizy jako subprocess z lepszym loggingiem
    """
    try:
        logger.info(f"🔧 Przygotowywanie subprocess dla {ticker}")

        # Przygotuj komendę
        cmd = [
            "python", "/app/stock_model.py",
            "--ticker", ticker,
            "--trends", trends,
            "--start_date", start_date,
            "--test_size_pct", str(test_size_pct),
            "--forecast_days", str(forecast_days)
        ]

        logger.info(f"📝 Komenda: {' '.join(cmd)}")

        # Uruchom subprocess z przekierowaniem stdout/stderr
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,  # Przekieruj stderr do stdout
            cwd="/app",
            env={**os.environ, "PYTHONUNBUFFERED": "1"}  # Wymuś unbuffered output
        )

        logger.info(f"🚀 Subprocess uruchomiony z PID: {process.pid}")

        # Czytaj output w czasie rzeczywistym
        output_lines = []
        while True:
            try:
                line = await asyncio.wait_for(process.stdout.readline(), timeout=1.0)
                if not line:
                    break

                line_str = line.decode().strip()
                if line_str:
                    output_lines.append(line_str)
                    logger.info(f"📄 [{ticker}] {line_str}")

            except asyncio.TimeoutError:
                # Sprawdź czy proces jeszcze działa
                if process.returncode is not None:
                    break
                continue

        # Czekaj na zakończenie procesu
        await process.wait()

        full_output = '\n'.join(output_lines)

        logger.info(f"🔚 Subprocess zakończony z kodem: {process.returncode}")

        # Sprawdź kod wyjścia
        if process.returncode == 0:
            logger.info(f"✅ Analiza {ticker} zakończona pomyślnie")
            return {
                "success": True,
                "output": full_output,
                "ticker": ticker,
                "return_code": process.returncode
            }
        else:
            logger.error(f"❌ Analiza {ticker} zakończona z błędem (kod: {process.returncode})")
            return {
                "success": False,
                "error": f"Process exited with code {process.returncode}",
                "output": full_output,
                "ticker": ticker,
                "return_code": process.returncode
            }

    except asyncio.TimeoutError:
        logger.error(f"⏰ Timeout analizy dla {ticker}")
        return {
            "success": False,
            "error": "Analiza przekroczyła limit czasu (10 minut)",
            "ticker": ticker
        }
    except Exception as e:
        logger.error(f"💥 Wyjątek podczas analizy {ticker}: {e}")
        return {
            "success": False,
            "error": str(e),
            "ticker": ticker
        }

if __name__ == "__main__":
    import uvicorn
    logger.info("🌟 Uruchamianie FastAPI server")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
