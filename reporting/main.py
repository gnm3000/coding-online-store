
from fastapi import FastAPI
from typing import Optional, List
from fastapi.responses import FileResponse
from background_generate_report import ReportGenerator

app = FastAPI(root_path="/", docs_url='/api/docs')


@app.get("/reporting/json")
async def hello():
    reporting = ReportGenerator()
    stats, summary = reporting.run()

    return {"stats": stats.reset_index().to_dict(orient="records"),
            "summary": summary.reset_index().to_dict(orient="records")}


@app.get("/reporting/csv-summary")
async def hello():
    reporting = ReportGenerator()
    stats, summary = reporting.run()
    summary.to_csv("summary.csv")
    return FileResponse(path="summary.csv", filename="summary.csv")


@app.get("/reporting/csv-stats-by-customer")
async def hello():
    reporting = ReportGenerator()
    stats, summary = reporting.run()
    summary.to_csv("stats-by-customer.csv")

    return FileResponse(path="stats-by-customer.csv",
                        filename="stats-by-customer.csv")
