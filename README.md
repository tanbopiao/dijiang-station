# 地机驿站（Dijiang Station）

> **命名即种子（Naming as Seed）**：本仓从道统命名生长而来——名字承载「命名 → 逻辑本体 → 架构 → 算子」的映射，架构从名字里长出来。
> 理念全文：《[命名即种子：从道统长出的软件生长范式](https://www.huodouai.com/whitepaper/naming-as-seed-article-20261128.html)》 · 仓库全景：[开源窗户](https://www.huodouai.com/whitepaper/opensource-window-20261128.html)


> **命名即种子**：地机＝大地机关，承载而不显；驿站＝中转停靠，接续而传。
> 一句话架构：**把消息在节点间可靠地接住、存住、传下去——收件有凭、在途有账、送达有印。**

## 命名道统映射

| 命名 | 逻辑本体 | 架构构件 | 算子代码 |
|---|---|---|---|
| **地机**（大地机关） | 承载节点的固定职责：接、存、转，不越权 | `Station`（驿站节点，持有本地账本） | `Station.receive / forward` |
| **驿站**（中转停靠） | 消息的中转与停靠：到站登记、离站销号 | `Waybill`（运单：消息＋凭据） | `Waybill.seal / settle` |
| **接续传递** | 逐跳推进：每跳留痕，断点可续 | `route`（逐跳路由表） | `Station.tick`（推进一步） |
| **驿照**（凭信） | 送达凭证：内容指纹逐跳链式相扣 | `ledger`（链式台账） | `verify_ledger` |

## 设计铁律

1. **收件有凭**：消息进站即封印（内容哈希），无凭不受理。
2. **在途有账**：每跳追加台账，前链哈希相扣，篡改现形。
3. **送达有印**：终站签收后运单销号，重复投递幂等拒绝。
4. **断点可续**：驿站崩溃重启后，从未销号运单继续推进，已完成跳不重走。

## 快速开始

```python
from dijiang_station import Station, Waybill, send

a = Station("函谷驿")   # 起站
b = Station("陈仓驿")   # 中站
c = Station("陇西驿")   # 终站
a.route = [b, c]

wb = send(a, Waybill("军报", "腊月初三，匈奴渡河"))
a.tick()   # → b
b.tick()   # → c（终站签收销号）

print(wb.settled)          # True
```

## 自测与回归

```bash
python3 selftest.py
```

覆盖：封印凭据、逐跳推进、终站销号、幂等拒绝、断点续传、台账验链、篡改现形，以及「军报三驿」回归用例。

## 许可证

Apache-2.0 — 见 [LICENSE](LICENSE)。
