# 代码审查 × 用例测试结果 —— 关系结果方案

> 状态：方案（待确认，未实施）。本文档为交付物本身，确认后才会进入代码改动。

## 一、核心洞察（一句话）

当前系统交付的是**两个脱节的结论**——AI 代码审查给的 `risk_level`（度量改动风险，前置于用例）、用例执行给的 `conclusion`（度量质量风险）——用户看到的是两条并排信息，但**没有"本次提交该不该放行"的统一判断**。而 `gate_state`（门禁状态）字段、序列化器、前端展示位早已预留却从未被后端填充。

**主线**：把「静态审查风险 × 动态验证结果」融合为单一 `gate_state`（放行 / 阻断 / 关注），填回已预留的字段，前端收敛为单一综合结论条。既解决"风险与用例不挂钩"，又复用已建好的 gate 基础设施，改动最小、价值最大。

## 二、当前事实（证据，服务于结论）

- `aicheck/.../task_manager.py` 阶段3-4：`RiskAnalyzer.assess(diff)` 出 `risk_level`（高/中/低）+ `risk_score` + `risk_reason`；仅 `risk_level=="高"` → `conclusion="blocked"`、用例不跑（`summary` 全 0）、`return`。
- 阶段5-7：跑用例，`fail_count/error_count` 由 `r.result` 统计；`conclusion = "passed" if (fail==0 and error==0 and total>0) else "failed"`；`summary={total,pass,fail,error,pass_rate}`。
- 三处分支都只调 `self._gate_report(...)` 上报**外部**门禁，但**没有** `self.store.update(task_id, gate_state=...)` —— 所以后端返回的 task 里 `gate_state` 恒为空。
- `Testbackend/.../models.py:85`：`gate_state = CharField(blank=True)` 已存在；`serializers.py` 已暴露 `gate_state`；`Detail.vue:187` 已写 `v-if="task.gate_state"` + `gateType()` 映射 —— 全链路"等数据"，唯独后端没产。
- Django `codecheck_service.py:179` 落库逻辑写的是 `task.gate_state = gate.get("state","")`，但 aicheck 返回里没有 `gate` 键 → 落库恒为空。

## 三、关系结果矩阵（融合规则，纯 Python 确定性规则，不调 LLM）

| risk_level | conclusion | gate_state | 综合结论文案 |
|---|---|---|---|
| 高 | blocked | `blocked` | 改动风险高，阻断合入，需资深开发人工复核后放行 |
| 中 / 低 | passed | `success` | 静态审查 + 用例验证双通过，可放行 |
| 中 / 低 | failed | `review` | 改动风险可控，但用例暴露 `fail/error` 项，需修复或人工关注 |
| 中 / 低 | failed(纯异常) | `review` | 同上，异常项计入关注 |

> `gate_state` 取值约定：`success`(放行) / `review`(关注) / `blocked`(阻断)。model 为 `CharField(blank=True)` 无 choices 约束，直接写 `review` 即可；前端 `gateType` 映射补 `review: 'warning'`。

## 四、落地三步（每步停手都有价值）

### 步骤 1 — 后端融合（纯规则，无 LLM）
- **aicheck**：`task_manager.py` 新增 `_combine_gate(risk_level, conclusion) -> (gate_state, gate_reason)` 纯函数（上表即规则，可单测）。
  - 阶段4 blocked 分支：`self.store.update(task_id, ..., gate_state="blocked", gate_reason=...)`。
  - 阶段7 passed/failed 分支：`self.store.update(task_id, ..., gate_state=_, gate_reason=_)`。
- **Django**：`codecheck_service.py:179` 附近补 `task.gate_state = data.get("gate_state") or task.gate_state` 与 `task.gate_reason = data.get("gate_reason") or ""`（aicheck 返回补齐这两个键）。
- **停手价值**：API 返回即含统一综合结论、数据库有值。即便前端不改，接口层已可见"风险×用例"的关系结果。

### 步骤 2 — 前端收敛为单一综合结论条
- `Detail.vue`：
  - 结论条 `verdict-bar` 由 `conclusion` 驱动改为由 `gate_state` 驱动着色（`success`=绿/灰、`review`=橙、`blocked`=黑），展示 `gate_reason` 作为主文案。
  - 「风险等级」卡从"并列主维度"降为**支撑明细**（保留，不再与结论脱节展示）；通过率/未通过数仍作明细卡。
  - 复用已有 `Detail.vue:187` 的 `task.gate_state` 展示位 + `gateType()`（补 `review: 'warning'`），避免新增 DOM。
- **停手价值**：页面从"两条脱节线"变成"一条综合放行结论"，用户一眼看到风险与用例的关系。

### 步骤 3 — 导出 HTML 闭环
- `report_html.py` 新增「综合放行结论」章节：展示 `gate_state` 徽标 + `gate_reason` + 关系矩阵简述，与页面口径一致。
- **停手价值**：导出留档与在线页面一致，关系结果闭环可审计。

## 五、后续优化方向（非主线，确认后酌情）
1. `risk_analyzer` 长 diff 截断到 5000 字符 → 改增量/分段评估，降低长变更漏判。
2. **真正的双向挂钩**：让用例失败分布回灌 `risk_score`（fail/error 多时抬升风险分），实现"用例越差风险越高"，而非仅"高风险阻断用例"的单向关系。
3. `gate_state` 接入 CI 门禁策略（当前仅存库展示），可按项目配置 `review` 是否阻断流水线。

## 六、验收标准
- [ ] 任一任务 API 返回含非空 `gate_state` 与 `gate_reason`；DB 落库非空。
- [ ] 高/中低×passed/failed 四种组合分别映射到 blocked/success/review 正确。
- [ ] 前端详情页显示单一综合结论条（颜色 + 文案），风险等级、通过率为其下明细。
- [ ] 导出 HTML 含「综合放行结论」章节且口径与页面一致。
- [ ] 步骤1 完成后即可独立验收接口层（前端未改也有值）。
