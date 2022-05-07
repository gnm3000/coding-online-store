from fastapi import FastAPI
from typing import Optional

app = FastAPI(root_path="/customers/")

@app.get("/customers")
async def root():
    return {"message": "Hello World"}

@app.post("/customers/new")
def read_item(full_name: str, wallet_usd: int):
    """ Create a new customer

    Args:
        full_name (str): _description_
        wallet_usd (int): _description_

    Returns:
        _json_: _description_
    """

    # here save to DB

    return {"full_name": full_name, "wallet_usd": wallet_usd}
