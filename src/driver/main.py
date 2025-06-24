import json
import os

from typing import Literal
from uuid import uuid5, NAMESPACE_DNS
from datetime import datetime, date
from collections import OrderedDict


class DataManager:
    def __init__(self, directory: str = r"src\databases") -> None:
        self.file_path = directory + r"\data.json"
        self.lp_cache = OrderedDict()
        self.hp_cache = OrderedDict()

    def setup(self) -> None:
        if not os.path.exists(self.file_path):
            with open(file=self.file_path, mode="w+") as f:
                pass
        with open(file=self.file_path, mode="r+") as f:
            try:
                data = json.load(f)
            except Exception:
                data = {"L": {}, "H": {}}
        self.lp_cache = OrderedDict(data["L"].items())
        self.hp_cache = OrderedDict(data["H"].items())

    def sync(self) -> None:
        struct = {"L": self.lp_cache, "H": self.hp_cache}
        with open(file=self.file_path, mode="w+") as f:
            json.dump(struct, f, indent=4)


class Driver:
    def __init__(
        self, priority_maxsize: int = 5, datamanager: DataManager = DataManager()
    ) -> None:
        self.priority_maxsize = priority_maxsize
        self.data_manager = datamanager
        self.data_manager.setup()
        self.low_priority_tasks = datamanager.lp_cache
        self.high_priority_tasks = datamanager.hp_cache

    @property
    def is_full(self) -> bool:
        if (len(self.low_priority_tasks) == self.priority_maxsize * 2) and (len(self.high_priority_tasks) == self.priority_maxsize):
            return True
        return False

    def add_task(self, name: str, details: str | None, priority: Literal["L", "H"], *, expire: date | None = None) -> bool: 
        if priority in ["L", "H"]:
            datastore = None
            maxsize = self.priority_maxsize
            uid = str(uuid5(NAMESPACE_DNS, name.lower()))
            if priority == "L":
                datastore = self.low_priority_tasks
                maxsize = maxsize * 2
            elif priority == "H":
                datastore = self.high_priority_tasks
            if uid in datastore:
                return False
            if len(datastore) == maxsize:
                return False
            datastore[uid] = {
                "name": name,
                "details": details,
                "date_added": datetime.now().date().strftime(r"%d-%m-%Y"),
                "is_complete": False,
                "completed_at": None,
                "is_expired": datetime.now().date() >= expire if expire else False,
                "expires_at": expire.strftime(r"%d-%m-%Y") if expire else expire
            }
            self.data_manager.sync()
            return True
        else:
            return False

    def complete_task(self, name: str, priority: Literal["L", "H"]) -> bool:
        if priority in ["L", "H"]:
            datastore = None
            uid = str(uuid5(NAMESPACE_DNS, name.lower()))
            if priority == "L":
                datastore = self.low_priority_tasks
            elif priority == "H":
                datastore = self.high_priority_tasks
            if uid in datastore:
                datastore[uid]["is_complete"] = True
                datastore[uid]["completed_at"] = datetime.now().date().strftime(
                    r"%d-%m-%Y"
                )
                self.data_manager.sync()
                return True
            else:
                return False
        else:
            return False

    def remove_task(self, name: str, priority: Literal["L", "H"]) -> bool | dict:
        if priority in ["L", "H"]:
            datastore = None
            uid = str(uuid5(NAMESPACE_DNS, name.lower()))
            if priority == "L":
                datastore = self.low_priority_tasks
            elif priority == "H":
                datastore = self.high_priority_tasks
            if uid in datastore:
                item = datastore.pop(uid)
                self.data_manager.sync()
                return item
            else:
                return False
        else:
            return False

    def check_expiry(self) -> None:
        has_updated = False
        for task in self.low_priority_tasks:
            if self.low_priority_tasks[task]["expires_at"] and (datetime.now().date() > datetime.strptime(self.low_priority_tasks[task]["expires_at"], r"%d-%m-%Y").date()):
                if self.low_priority_tasks[task]["is_expired"] != True:
                    self.low_priority_tasks[task]["is_expired"] = True
                    has_updated = True
            elif self.low_priority_tasks[task]["expires_at"] and (datetime.now().date() <= datetime.strptime(self.low_priority_tasks[task]["expires_at"], r"%d-%m-%Y").date()):
                if self.low_priority_tasks[task]["is_expired"] != False:
                    self.low_priority_tasks[task]["is_expired"] = False
                    has_updated = True
            elif not self.low_priority_tasks[task]["expires_at"] and self.low_priority_tasks[task]["is_expired"] == True:
                self.low_priority_tasks[task]["is_expired"] = False
                has_updated = True
        for task in self.high_priority_tasks:
            if self.high_priority_tasks[task]["expires_at"] and (datetime.now().date() > datetime.strptime(self.high_priority_tasks[task]["expires_at"], r"%d-%m-%Y").date()):
                if self.high_priority_tasks[task]["is_expired"] != True:
                    self.high_priority_tasks[task]["is_expired"] = True
                    has_updated = True
            elif self.high_priority_tasks[task]["expires_at"] and (datetime.now().date() <= datetime.strptime(self.high_priority_tasks[task]["expires_at"], r"%d-%m-%Y").date()):
                if self.high_priority_tasks[task]["is_expired"] != False:
                    self.high_priority_tasks[task]["is_expired"] = False
                    has_updated = True
            elif not self.high_priority_tasks[task]["expires_at"] and self.high_priority_tasks[task]["is_expired"] == True:
                self.high_priority_tasks[task]["is_expired"] = False
                has_updated = True
        if has_updated:
            self.data_manager.sync()
