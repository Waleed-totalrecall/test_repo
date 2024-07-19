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



# fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


# @app.get("/items/")
# async def read_item(skip: int = 0, limit: int = 10):
#     return fake_items_db[skip : skip + limit]



@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(
    user_id: int, item_id: str, q: str | None = None, short: bool = False
):
    item = {"item_id": item_id, "owner_id": user_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item


# from pydantic import BaseModel


# class Item(BaseModel):
#     name: str
#     description: str | None = None
#     price: float
#     tax: float | None = None




@app.post("/items/")
async def create_item(item: item):
    item_dict = item.dict()
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict


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

@app.get("/items")
async def read_items(commons:dict=Depends(common_param)):
    return commons

# @app.get("/users")
# async def get_users(commons:dict=Depends(common_param)):
    return commons
             
             
s to be removed. – 
Bahman Eslami
 CommentedSep 27, 2020 at 11:54
project was moved to github, but then archived by its author – 
Alleo
 CommentedDec 12, 2020 at 19:46
Add a comment
27

An improved version of the PabloG code for Python 2/3:

#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import ( division, absolute_import, print_function, unicode_literals )

import sys, os, tempfile, logging

if sys.version_info >= (3,):
    import urllib.request as urllib2
    import urllib.parse as urlparse
else:
    import urllib2
    import urlparse

def download_file(url, dest=None):
    """ 
    Download and save a file specified by url to dest directory,
    """
    u = urllib2.urlopen(url)

    scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
    filename = os.path.basename(path)
    if not filename:
        filename = 'downloaded.file'
    if dest:
        filename = os.path.join(dest, filename)

    with open(filename, 'wb') as f:
        meta = u.info()
        meta_func = meta.getheaders if hasattr(meta, 'getheaders') else meta.get_all
        meta_length = meta_func("Content-Length")
        file_size = None
        if meta_length:
            file_size = int(meta_length[0])
        print("Downloading: {0} Bytes: {1}".format(url, file_size))

        file_size_dl = 0
        block_sz = 8192
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break

            file_size_dl += len(buffer)
            f.write(buffer)

            status = "{0:16}".format(file_size_dl)
            if file_size:
                status += "   [{0:6.2f}%]".format(file_size_dl * 100 / file_size)
            status += chr(13)
            print(status, end="")
        print()

    return filename

if __name__ == "__main__":  # Only run if this file is called directly
    print("Testing with 10MB download")
    url = "http://download.thinkbroadband.com/10MB.zip"
    filename = download_file(url)
    print(filename)
