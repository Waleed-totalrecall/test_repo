from fastapi import FastAPI,Depends
from typing import Optional

app = FastAPI()

@app.get("/")
def index():
    return'Hello world'

@app.get("/items/{item_id}")
async def index(item_id: int):
    return {"item_id": item_id}


@app.get("/items/")
def index(q:int=0,m:Optional[int]=10):
    return {"product_id": q,"Op":m}

@app.post("/items")
def index():
    return "Hello world"



# fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


# @app.get("/items/")
# async def read_item(skip: int = 0, limit: int = 10):
#     return fake_items_db[skip : skip + limit]



# @app.get("/users/{user_id}/items/{item_id}")
# async def read_user_item(
#     user_id: int, item_id: str, q: str | None = None, short: bool = False
# ):
#     item = {"item_id": item_id, "owner_id": user_id}
#     if q:
#         item.update({"q": q})
#     if not short:
#         item.update(
#             {"description": "This is an amazing item that has a long description"}
#         )
#     return item


# from pydantic import BaseModel


# class Item(BaseModel):
#     name: str
#     description: str | None = None
#     price: float
#     tax: float | None = None




# @app.post("/items/")
# async def create_item(item: item):
#     item_dict = item.dict()
#     if item.tax:
#         price_with_tax = item.price + item.tax
#         item_dict.update({"price_with_tax": price_with_tax})
#     return item_dict


class CommonParam:
    def __init__(self,q:Optional[str]=2,skip:int=0,limit:int=0):
        self.q=q
        self.skip=skip
        self.limit=limit

@app.get("/")
async def read_item(commons:CommonParam=Depends(CommonParam)):
    res = {}
    return commons.q+commons.skip+commons.limit
    


# async def common_param(q:Optional[str]=None,skip:int=0,limit:int=0):
#     return{"q":q,'skip':skip,'limit':limit}

# @app.get("/items")
# async def read_items(commons:dict=Depends(common_param)):
#     return commons

# @app.get("/users")
# async def get_users(commons:dict=Depends(common_param)):
    return commons
             
             
