import sys
import json
import uuid
import locale
import psutil
import datetime
import platform
import requests
import functools
import traceback
from enum import Enum
from typing import TypedDict, Optional


class LattaProperties(Enum):
    LATTA_API_URI = "https://recording.latta.ai/v1"
    LATTA_INSTANCE_CACHE_KEY = "latta_instance_id"
    LATTA_RELATION_CACHE_KEY = "latta_relation_id"


class LattaEndpoints(Enum):
    LATTA_PUT_INSTANCE = "instance/generic"
    LATTA_PUT_SNAPSHOT = "snapshot/%s"
    LATTA_PUT_SNAPSHOT_ATTACHMENT = "snapshot/%s/attachment"


class LattaRecordLevels(Enum):
    LATTA_ERROR = "ERROR"
    LATTA_WARN = "WARN"
    LATTA_FATAL = "FATAL"


class LattaOptions(TypedDict, total=False):
    device: Optional[str]
    instance_id: Optional[str]


class LattaSystemInfo(TypedDict):
    cpu_usage: float
    total_memory: int
    free_memory: int


class LattaExceptionData(TypedDict):
    name: str
    message: str
    stack: str


class Latta:
    relation_id = uuid.uuid4()

    def __init__(self, api_key: str, options: Optional[LattaOptions] = None):
        self.exceptions = []
        self.api_key = api_key
        self.options: LattaOptions = options if options else {}

    def wrap(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                stack_trace = traceback.format_exception(
                    exc_type, exc_value, exc_traceback
                )
                if exc_type and exc_value:
                    error_data: LattaExceptionData = {
                        "name": str(exc_type.__name__),
                        "message": str(exc_value),
                        "stack": "\n".join(stack_trace),
                    }
                    instance_id = self.get_instance_id()
                    snapshot_id = self.put_snapshot(instance_id)
                    self.put_snapshot_data(snapshot_id, error_data)

                raise

        return wrapper

    def get_instance_id(self) -> str:
        id = ""
        if not hasattr(self.options, "instance_id"):
            id = self.put_instance()
            self.options["instance_id"] = id
        else:
            id = getattr(self.options, "instance_id")
        return id

    def get_headers(self):
        return {
            "content-type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def put_instance(self) -> str:
        loc = locale.getdefaultlocale()
        body = {
            "os_version": platform.version(),
            "os": platform.system().lower(),
            "lang": loc[0] if loc[0] else "en-us",
            "device": getattr(self.options, "device", "desktop")
            if self.options
            else "desktop",
        }

        uri = f"{LattaProperties.LATTA_API_URI.value}/{LattaEndpoints.LATTA_PUT_INSTANCE.value}"

        response = requests.put(uri, headers=self.get_headers(), data=json.dumps(body))

        data = response.json()

        if not response.ok:
            raise Exception(data)

        if "id" not in data:
            raise Exception("Latta did not return id", data)

        return str(data["id"])

    def put_snapshot(self, instance_id: str) -> str:
        uri = f"{LattaProperties.LATTA_API_URI.value}/{LattaEndpoints.LATTA_PUT_SNAPSHOT.value % (instance_id)}"

        data = {
            "message": "",
            "relation_id": instance_id,
            "related_to_relation_id": None,
        }

        snapshot_response = requests.put(
            uri, headers=self.get_headers(), data=json.dumps(data)
        )

        if not snapshot_response.ok:
            raise Exception("Latta did not respond correctly!")

        self.relation_id = uuid.uuid4()

        return snapshot_response.json()["id"]

    def put_snapshot_data(
        self, snapshot_id: str, exception: LattaExceptionData
    ) -> bool:
        timestamp = int(datetime.datetime.now().timestamp() * 1000)

        attachment = {
            "type": "record",
            "data": {
                "timestamp": timestamp,
                "level": LattaRecordLevels.LATTA_ERROR.value,
                "name": exception["name"],
                "message": exception["message"],
                "stack": exception["stack"],
                "system_info": self.get_system_info(),
            },
        }

        uri = f"{LattaProperties.LATTA_API_URI.value}/{LattaEndpoints.LATTA_PUT_SNAPSHOT_ATTACHMENT.value % (snapshot_id)}"
        data_response = requests.put(
            uri, headers=self.get_headers(), data=json.dumps(attachment)
        )

        return data_response.ok

    @staticmethod
    def get_system_info() -> LattaSystemInfo:
        cpu_usage = psutil.cpu_percent(interval=1)

        memory = psutil.virtual_memory()

        return {
            "cpu_usage": cpu_usage,
            "total_memory": memory.total,
            "free_memory": memory.free,
        }
