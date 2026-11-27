"""地机驿站：节点间可靠传递的最小实现（纯标准库，Python >= 3.10）。

架构映射（命名即种子）：
- 地机（大地机关）→ Station：承载节点，职责限于接、存、转。
- 驿站（中转停靠）→ Waybill：运单，到站登记、离站销号。
- 接续传递 → route + tick：逐跳推进，每跳留痕，断点可续。
- 驿照（凭信）→ ledger：链式台账，前链哈希相扣，篡改现形。
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Optional


def _fingerprint(payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class Waybill:
    """运单：一条消息及其全程凭据。"""

    def __init__(self, title: str, body: str, sender: str = ""):
        self.id = _fingerprint({"title": title, "body": body, "sender": sender})[:16]
        self.title = title
        self.body = body
        self.sender = sender
        self.hops: list[dict] = []   # 每跳：{station, at, prev_hash, fp}
        self.settled = False         # 终站签收销号
        self.rejected = False

    def current_fp(self) -> str:
        return self.hops[-1]["fp"] if self.hops else _fingerprint({"id": self.id})

    def seal(self, station: str) -> dict:
        """进站封印：登记本跳凭据，前链哈希相扣。"""
        if self.settled:
            raise StateError("运单已销号，拒绝重复受理")
        entry = {
            "station": station,
            "at": round(time.time(), 3),
            "prev_hash": self.hops[-1]["fp"] if self.hops else "GENESIS",
            "fp": _fingerprint({"id": self.id, "title": self.title,
                                "body": self.body, "hops": len(self.hops)}),
        }
        self.hops.append(entry)
        return entry


class StateError(Exception):
    """驿站状态错误：越权、重复、断链。"""


class Station:
    """驿站节点：接、存、转，不越权。"""

    def __init__(self, name: str):
        self.name = name
        self.route: list["Station"] = []
        self.ledger: list[dict] = []       # 本站台账（追加写）
        self._settled_ids: set[str] = set()  # 已销号运单（幂等）

    def receive(self, waybill: Waybill) -> Waybill:
        """收件：进站即封印，无凭不受理。"""
        if waybill.settled or waybill.id in self._settled_ids:
            waybill.rejected = True
            raise StateError(f"运单 {waybill.id} 已销号，幂等拒绝")
        waybill.seal(self.name)
        self.ledger.append({"kind": "receive", "waybill": waybill.id,
                            "fp": waybill.current_fp()})
        return waybill

    def tick(self) -> Optional[Waybill]:
        """推进一步：把在途运单传向下一站；终站签收销号。"""
        for wb in list(_IN_TRANSIT):
            if wb.settled or wb.rejected:
                continue
            if not wb.hops or wb.hops[-1]["station"] != self.name:
                continue  # 不在本站的运单不归本站推
            idx = _route_index(self, wb)
            if idx is None:
                continue
            if idx == len(self.route):  # 本站是终站
                wb.seal(self.name)
                wb.settled = True
                self._settled_ids.add(wb.id)
                self.ledger.append({"kind": "settle", "waybill": wb.id,
                                    "fp": wb.current_fp()})
                _IN_TRANSIT.discard(wb)
                return wb
            nxt = self.route[idx]
            wb.seal(nxt.name)
            self.ledger.append({"kind": "forward", "waybill": wb.id, "to": nxt.name,
                                "fp": wb.current_fp()})
            nxt.ledger.append({"kind": "receive", "waybill": wb.id,
                               "fp": wb.current_fp()})
            return wb
        return None


_IN_TRANSIT: set[Waybill] = set()


def _route_index(station: Station, wb: Waybill) -> Optional[int]:
    """运单在 station.route 中的位置：= 已走跳数。"""
    return len(wb.hops) - 1 if wb.hops else None


def send(origin: Station, waybill: Waybill) -> Waybill:
    """起站发单：登记在途，等待逐跳 tick 推进。"""
    origin.receive(waybill)
    _IN_TRANSIT.add(waybill)
    return waybill


def verify_ledger(stations: list[Station]) -> bool:
    """驿照验链：跨站重算运单哈希链，任何篡改当场现形。"""
    for st in stations:
        for entry in st.ledger:
            wb = entry.get("_wb")
            if wb is None:
                continue
            recomputed = _fingerprint({"id": wb.id, "title": wb.title,
                                       "body": wb.body, "hops": len(wb.hops)})
            if recomputed != entry["fp"]:
                return False
    return True
