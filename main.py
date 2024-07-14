#==============================================================================
# Copyright (C) 2024  Emmanuel Mazurier <contact@bibliob.us>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#==============================================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import devices, books, positions, requests

app = FastAPI(title="Bibliobus API",
              summary="Rest API to manage item positions from and to \"Bibus\" devices",
              version="0.1.0",
              contact={
                "name":"Bibliobus",
                "url":"https://bibliob.us/fr",
                "email":"contact@bibliob.us"
              },
              license_info={
                    "name": "GPLv3",
                    "url": "https://www.gnu.org/licenses/quick-guide-gplv3.html",
            })

origins = [
    "http://localhost",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to Bibliobus API"}

app.include_router(books.router)
app.include_router(devices.router)
app.include_router(positions.router)
app.include_router(requests.router)

