# MVP 验收指南

## 1. 文档定位

本文件用于固定当前项目达到 `MVP` 验收线时的判断依据。

`MVP` 在当前项目中的含义是：

- 一套可运行的事件驱动回合制引擎
- 已具备最小 battle slice
- 已具备控制台 client
- 已具备 predictive / replay / resync
- 已具备最小物理 C/S 切片

---

## 2. 自动化验收

当前 `MVP` 的自动化验收基础包括：

- `tests/acceptance/test_m0_acceptance.py`
- `tests/acceptance/test_m1_acceptance.py`
- `tests/acceptance/test_m2_acceptance.py`
- `tests/acceptance/test_m3_acceptance.py`
- `tests/acceptance/test_m4_acceptance.py`
- `tests/acceptance/test_m5_acceptance.py`
- `tests/acceptance/test_mvp_acceptance.py`

同时应保持：

```bash
python3.12 -m pytest -q
python3.12 -m compileall core standard_components server client demo transport tests project_config.py project_setup.py
```

持续通过。

---

## 3. 手动验收建议

当前建议至少覆盖以下手测入口：

1. `M1 Manual Console Test Guide.md`
2. `M3 Manual Predictive Console Test Guide.md`
3. `M4 Manual Network Simulation Test Guide.md`
4. `M5 Manual Physical Client-Server Test Guide.md`

若只做一轮聚焦型最终手测，建议优先运行：

```bash
python3.12 -m client.console_app --predictive --transport subprocess
```

并验证：

- `help attack`
- `rally`
- `poison slime`
- `sync`
- `resync`
- `quit`

---

## 4. 当前验收判断

当以下条件同时成立时，可视为当前项目达到 `MVP` 验收线：

1. 最小 `basic_combat` 战斗链可运行
2. `RALLY / ATTACK_UP / POISON` 已可观察
3. predictive client 可执行 accepted / resync / replay 主链
4. 本地 loopback network 可验证多 pending / send / deliver / flush
5. subprocess transport 已证明最小物理 C/S 切片成立
6. CLI 命令帮助与命令参考文档保持同步

---

## 5. 当前结论

截至当前版本，以上条件已满足，因此：

- **项目已到达当前定义下的 `MVP` 验收线**
