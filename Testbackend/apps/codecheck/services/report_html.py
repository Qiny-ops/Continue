# -*- coding: utf-8 -*-
"""
代码检查审计报告 —— 后端导出「自包含 HTML」

生成一份不依赖任何外部资源（CSS 全部内联）的 HTML 文件：
- 双击即可在浏览器打开
- 可脱离平台独立转发 / 归档
内容与前端 AuditReport.vue 保持一致，逻辑在后端用 Python 复刻。
"""
import re
import html
from datetime import datetime

from django.utils import timezone

PASS_RESULT = "通过"

EVIDENCE_RE = re.compile(
    r"[\w./\\-]+\.(?:vue|js|ts|jsx|tsx|py|java|go|html|css|scss):\d+"
)

CONCLUSION_LABEL = {"passed": "通过", "blocked": "风险阻断", "failed": "未通过"}
TRIGGER_LABEL = {"manual": "手动触发", "webhook": "Webhook 自动触发"}
CASE_SOURCE_LABEL = {"platform": "平台用例库", "file": "Excel 文件导入", "inline": "内联用例"}
RISK_CLASS = {"高": "high", "中": "medium", "低": "low"}
RESULT_CLASS = {
    "通过": "pass", "失败": "fail", "异常": "error",
    "解析错误": "warn", "解析失败": "warn",
}

# 不同失败类型对应的整改动作（与前端 TYPE_ADVICE 一致）
TYPE_ADVICE = {
    "功能未实现": "对应功能在代码中缺失，需补充实现后重新检查。",
    "实现与预期不符": "实现与用例预期存在具体差异（如跳转目标、提示文案、字段取值），需按预期逐项修正，而非仅保证主流程可用。",
    "部分实现": "仅实现了部分预期项，需对照「预期结果」补齐剩余条目。",
    "无法定位实现": "代码中未找到对应实现，需确认该功能是否已提交、是否位于本次检查的分支与仓库中。",
    "用例与代码库不匹配": "用例描述的业务与本次检查的仓库不匹配，需核对用例归属项目或重新选择正确的代码仓库。",
    "校验执行异常": "AI 校验未获得有效结论，需确认校验服务（模型配额、鉴权）可用后重跑，避免漏判。",
}


# ----------------------- 工具函数 -----------------------

def _esc(value):
    if value is None:
        return ""
    return html.escape(str(value))


def _failure_type_of(item):
    ft = (item.get("failure_type") or "").strip()
    if ft:
        return ft
    if not item or item.get("result") == PASS_RESULT:
        return ""
    return "其他"


def _failure_reason_of(item):
    own = (item.get("failure_reason") or "").strip()
    if own:
        return own
    reason = re.sub(r"\s+", " ", (item.get("reason") or "")).strip()
    if not reason:
        return "未提供失败原因。"
    m = re.match(r"^.{0,120}?[。；;!？?]", reason)
    first = m.group(0) if m else reason[:120]
    return first + "…" if len(first) < len(reason) else first


def _reason_fail_cls(result):
    """失败 / 异常用例的失败原因块加 `fail` 类（红底高亮）；通过用例不加。"""
    return " fail" if result and result != "通过" else ""


def _evidence_list(item):
    raw = (item.get("evidence") or "").strip()
    if raw:
        return [s.strip() for s in re.split(r"[,，]", raw) if s.strip()]
    found = EVIDENCE_RE.findall(item.get("reason") or "")
    seen = []
    for f in found:
        if f not in seen:
            seen.append(f)
    return seen[:6]


def _brief(text, length=90):
    if not text:
        return "-"
    t = re.sub(r"\s+", " ", str(text)).strip()
    return t if len(t) <= length else t[:length] + "…"


def _format_time(value):
    if not value:
        return "-"
    try:
        dt = timezone.localtime(value)
    except Exception:
        dt = value
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ----------------------- 报告数据计算 -----------------------

def _collect(task):
    """复刻 AuditReport.vue 的 computed 逻辑，返回渲染所需的所有字段。"""
    results = list(task.results.all().order_by("id"))
    summary = task.summary or {}

    total = summary.get("total")
    if total is None:
        total = len(results)
    pass_c = summary.get("pass", 0) or 0
    fail_c = summary.get("fail", 0) or 0
    error_c = summary.get("error", 0) or 0

    rate = summary.get("pass_rate")
    if rate in (None, "", " "):
        pass_rate_text = "-"
    elif isinstance(rate, (int, float)):
        pass_rate_text = f"{rate}%"
    else:
        pass_rate_text = str(rate)

    result_dicts = [
        {
            "id": r.id,
            "case_no": r.case_no,
            "testpoint": r.testpoint,
            "steps": r.steps,
            "expectation": r.expectation,
            "result": r.result,
            "reason": r.reason,
            "success": r.success,
            "failure_type": r.failure_type,
            "failure_reason": r.failure_reason,
            "evidence": r.evidence,
        }
        for r in results
    ]

    findings = [r for r in result_dicts if r["result"] != PASS_RESULT]
    failed_items = [r for r in result_dicts if r["result"] == "失败"]
    error_items = [r for r in findings if r["result"] != "失败"]

    # 按失败类型统计
    type_stats = {}
    for r in findings:
        t = _failure_type_of(r)
        if t:
            type_stats[t] = type_stats.get(t, 0) + 1
    failure_type_stats = sorted(type_stats.items(), key=lambda kv: kv[1], reverse=True)

    failure_type_summary = "、".join(f"{t} {n} 条" for t, n in failure_type_stats)

    # diff
    diff_info = task.diff_info or {}
    changed_files = diff_info.get("changed_files")
    changed_file_count = len(changed_files) if isinstance(changed_files, list) else (diff_info.get("changed_files_count") or 0)
    additions = diff_info.get("additions") or 0
    deletions = diff_info.get("deletions") or 0
    commit_after = diff_info.get("commit_after") or task.commit_sha or ""
    commit_short = (str(commit_after)[:8] if commit_after else "-")

    # 风险文件
    risk_files = []
    for f in (task.risk_files or []):
        if isinstance(f, str):
            if f:
                risk_files.append(f)
        elif isinstance(f, dict):
            v = f.get("path") or f.get("file") or ""
            if v:
                risk_files.append(v)

    # 报告头
    now = timezone.localtime()
    report_date = now.strftime("%Y%m%d")
    report_no = f"ACR-{report_date}-{task.id:04d}"
    generated_at = now.strftime("%Y-%m-%d %H:%M")
    date_only = now.strftime("%Y-%m-%d")

    # 提交人 = git commit 作者（优先），回退到"触发检查的人"
    created_by = task.commit_author or (task.created_by.username if task.created_by else "-")

    conclusion = task.conclusion
    c_label = CONCLUSION_LABEL.get(conclusion, "-")

    # 审计结论文案
    if conclusion == "passed":
        verdict = f"本次检查共执行 {total} 条用例，全部通过，通过率 {pass_rate_text}，未发现功能实现与预期不符的情况。"
    elif conclusion == "blocked":
        verdict = f"本次检查因风险评估未达放行标准被阻断：共 {total} 条用例，未通过 {fail_c} 条、异常 {error_c} 条，通过率 {pass_rate_text}。{('未通过项按原因分布：' + failure_type_summary + '。') if failure_type_summary else ''}"
    elif conclusion == "failed":
        cause = f"未通过项按原因分布：{failure_type_summary}。" if failure_type_summary else ""
        verdict = f"本次检查未通过：共 {total} 条用例，未通过 {fail_c} 条、异常 {error_c} 条，通过率 {pass_rate_text}。{cause}各条失败原因详见「审计发现」。"
    else:
        cause = f"未通过项按原因分布：{failure_type_summary}。" if failure_type_summary else ""
        verdict = f"本次检查共执行 {total} 条用例，通过 {pass_c} 条，通过率 {pass_rate_text}。{cause}"

    # 改进建议
    suggestions = []
    for t, n in failure_type_stats:
        advice = TYPE_ADVICE.get(t, "需人工复核该部分未通过项。")
        suggestions.append(f"【{t}】{n} 条 —— {advice}")
    if failed_items:
        suggestions.append(f"共 {len(failed_items)} 条用例未通过，需按「审计发现」中的失败原因逐项修复，并在修复后重新提交代码检查。")
    if error_items:
        suggestions.append(f"有 {len(error_items)} 条用例未获得有效校验结论（执行异常），建议确认 AI 校验服务可用性后重跑，避免漏判。")
    if task.risk_level == "高":
        suggestions.append("本次变更风险等级为「高」，建议由资深开发人工复核后再合入主干。")
    if risk_files:
        head = "、".join(risk_files[:5])
        more = " 等" if len(risk_files) > 5 else ""
        suggestions.append(f"重点关注以下高风险文件：{head}{more}。")
    if not failed_items and not error_items:
        suggestions.append("全部用例通过，未发现功能实现与预期不符的情况，可按流程合入。")
    suggestions.append("若用例内容（步骤/预期）发生变更，需重新触发检查，历史报告结论不再适用。")

    return {
        "task": task,
        "results": result_dicts,
        "total": total,
        "pass_c": pass_c,
        "fail_c": fail_c,
        "error_c": error_c,
        "pass_rate_text": pass_rate_text,
        "findings": findings,
        "failed_items": failed_items,
        "error_items": error_items,
        "failure_type_stats": failure_type_stats,
        "failure_type_summary": failure_type_summary,
        "changed_file_count": changed_file_count,
        "additions": additions,
        "deletions": deletions,
        "commit_after": commit_after or "-",
        "commit_short": commit_short,
        "risk_files": risk_files,
        "report_no": report_no,
        "generated_at": generated_at,
        "date_only": date_only,
        "created_by": created_by,
        "conclusion": conclusion,
        "c_label": c_label,
        "verdict": verdict,
        "suggestions": suggestions,
        "trigger_label": TRIGGER_LABEL.get(task.trigger_source, task.trigger_source or "-"),
        "case_source_label": CASE_SOURCE_LABEL.get(task.case_source, task.case_source or "-"),
        "risk_class": RISK_CLASS.get(task.risk_level, ""),
        "checked_at": _format_time(task.created_at),
    }


# ----------------------- HTML 片段渲染 -----------------------

_CSS = """
* { box-sizing: border-box; }
body { margin: 0; background: #f0f0f0; font-family: -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; color: #1a1a1a; }
.report-wrap { max-width: 920px; margin: 24px auto; background: #fff; border: 1px solid #f0f0f0; }
.report-paper { padding: 48px 56px; font-size: 13px; line-height: 1.7; color: #1a1a1a; }
.mono { font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; }
.break { word-break: break-all; }
.muted { color: #8c8c8c; }

.report-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; padding-bottom: 16px; border-bottom: 2px solid #1a1a1a; }
.report-title { margin: 0; font-size: 24px; font-weight: 600; letter-spacing: 2px; }
.report-subtitle { margin: 4px 0 0; font-size: 11px; letter-spacing: 3px; color: #8c8c8c; text-transform: uppercase; }
.head-right { flex-shrink: 0; min-width: 260px; }
.meta-row { display: flex; align-items: center; gap: 8px; font-size: 12px; line-height: 1.9; }
.meta-label { width: 60px; color: #8c8c8c; }
.meta-value { color: #1a1a1a; }

.report-section { margin-top: 28px; }
.section-heading { display: flex; align-items: center; gap: 8px; margin: 0 0 12px; font-size: 14px; font-weight: 600; }
.heading-no { display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; background: #1a1a1a; color: #fff; font-size: 11px; font-weight: 600; border-radius: 2px; }
.heading-note { margin-left: auto; font-size: 12px; font-weight: 400; color: #8c8c8c; }

.kv-table { width: 100%; border-collapse: collapse; border: 1px solid #e5e5e5; }
.kv-table th, .kv-table td { padding: 8px 12px; border: 1px solid #e5e5e5; font-size: 12px; text-align: left; vertical-align: top; }
.kv-table th { width: 90px; background: #fafafa; color: #8c8c8c; font-weight: 500; white-space: nowrap; }

.summary-table-wrap { border: 1px solid #e5e5e5; }
.summary-table { width: 100%; border-collapse: collapse; }
.summary-table th, .summary-table td { padding: 10px 8px; border-right: 1px solid #e5e5e5; text-align: center; font-size: 12px; }
.summary-table th { background: #fafafa; color: #8c8c8c; font-weight: 500; }
.summary-table th:last-child, .summary-table td:last-child { border-right: none; }
.summary-table .num { font-size: 20px; font-weight: 600; }
.summary-table .num.pass { color: #2e7d32; }
.summary-table .num.fail { color: #c62828; }
.summary-table .num.error { color: #b26a00; }

.risk-chip { display: inline-block; padding: 2px 10px; border-radius: 2px; font-size: 12px; font-weight: 600; }
.risk-chip.high { background: #fdecea; color: #c62828; }
.risk-chip.medium { background: #fff4e5; color: #b26a00; }
.risk-chip.low { background: #e8f5e9; color: #2e7d32; }

.summary-verdict { margin: 12px 0 0; padding: 10px 12px; background: #fafafa; border-left: 2px solid #1a1a1a; font-size: 12px; line-height: 1.8; }

.paragraph { font-size: 12px; line-height: 1.8; white-space: pre-wrap; }
.risk-files { margin-top: 12px; }
.block-label { display: block; font-size: 12px; color: #8c8c8c; margin-bottom: 6px; }
.file-list { display: flex; flex-wrap: wrap; gap: 6px; }
.file-tag { padding: 2px 8px; background: #fdecea; color: #c62828; border-radius: 2px; font-size: 12px; font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; }

.finding { border: 1px solid #e5e5e5; border-radius: 2px; margin-bottom: 12px; }
.finding-head { display: flex; align-items: center; gap: 10px; padding: 8px 12px; background: #fafafa; border-bottom: 1px solid #e5e5e5; }
.finding-no { font-size: 12px; font-weight: 600; color: #8c8c8c; }
.finding-title { flex: 1; min-width: 0; font-size: 13px; font-weight: 600; }
.finding-case { margin-right: 6px; font-weight: 400; color: #8c8c8c; }
.finding-body { padding: 10px 12px; }
.finding-reason { display: flex; gap: 12px; margin-bottom: 10px; padding: 8px 10px; background: #fafafa; border-left: 2px solid #1a1a1a; }
/* 失败原因：失败 / 异常用例用「失败」红底高亮 */
.finding-reason.fail { background: #fdecea; border-left: 2px solid #c62828; }
.finding-reason.fail .reason-label { color: #c62828; }
.finding-reason.fail .reason-text { color: #7a1f1f; }
.reason-label { width: 66px; flex-shrink: 0; font-size: 12px; font-weight: 600; color: #1a1a1a; }
.reason-text { flex: 1; min-width: 0; font-size: 12.5px; line-height: 1.75; white-space: pre-wrap; word-break: break-word; }
.type-badge { display: inline-block; padding: 1px 8px; border: 1px solid #e5e5e5; border-radius: 2px; font-size: 12px; line-height: 18px; white-space: nowrap; color: #404040; }
.evidence-tag { display: inline-block; margin: 0 6px 4px 0; padding: 1px 6px; background: #f5f5f5; border-radius: 2px; font-size: 11.5px; color: #404040; }
.finding-item { display: flex; gap: 12px; margin-bottom: 8px; }
.finding-item:last-child { margin-bottom: 0; }
.finding-label { width: 66px; flex-shrink: 0; font-size: 12px; color: #8c8c8c; }
.finding-text { flex: 1; min-width: 0; font-size: 12px; line-height: 1.8; white-space: pre-wrap; word-break: break-word; }
.finding-text.evidence { color: #404040; }

.suggestion-list { margin: 0; padding-left: 20px; font-size: 12px; line-height: 2; }

.detail-table { width: 100%; border-collapse: collapse; border: 1px solid #e5e5e5; }
.detail-table th, .detail-table td { padding: 7px 10px; border: 1px solid #e5e5e5; font-size: 12px; text-align: left; vertical-align: top; }
.detail-table th { background: #fafafa; color: #8c8c8c; font-weight: 500; }
.detail-table .ellipsis { color: #404040; line-height: 1.6; }
.cell-reason { color: #1a1a1a; }
.evidence-cell { font-size: 11.5px; color: #8c8c8c; }

.conclusion-badge, .result-badge { display: inline-block; padding: 1px 8px; border-radius: 2px; font-size: 12px; line-height: 18px; white-space: nowrap; }
.conclusion-badge.passed { background: #e8f5e9; color: #2e7d32; }
.conclusion-badge.blocked { background: #fff4e5; color: #b26a00; }
.conclusion-badge.failed { background: #fdecea; color: #c62828; }
.conclusion-badge.none { color: #8c8c8c; }
.result-badge.pass { background: #e8f5e9; color: #2e7d32; }
.result-badge.fail { background: #fdecea; color: #c62828; }
.result-badge.error { background: #fdecea; color: #c62828; }
.result-badge.warn { background: #fff4e5; color: #b26a00; }
.result-badge.none { background: #f5f5f5; color: #404040; }

.report-foot { margin-top: 40px; padding-top: 16px; border-top: 1px solid #e5e5e5; }
.foot-note { font-size: 11px; line-height: 1.8; color: #8c8c8c; }
"""



def build_audit_report_html(task):
    """生成自包含 HTML 审计报告字符串。"""
    d = _collect(task)

    # 审计对象
    audit_object = f"""
    <section class="report-section">
      <h2 class="section-heading"><span class="heading-no">一</span>审计对象</h2>
      <table class="kv-table"><tbody>
        <tr>
          <th>所属项目</th><td>{_esc(d['task'].project_name) or '-'}</td>
          <th>代码仓库</th><td class="mono break">{_esc(d['task'].repository_url) or '-'}</td>
        </tr>
        <tr>
          <th>分支</th><td class="mono">{_esc(d['task'].branch) or '-'}</td>
          <th>Commit</th><td class="mono break">{_esc(d['commit_after'])}</td>
        </tr>
        <tr>
          <th>变更文件</th><td>{d['changed_file_count']} 个</td>
          <th>变更规模</th><td>+{d['additions']} / -{d['deletions']} 行</td>
        </tr>
        <tr>
          <th>任务编号</th><td class="mono">#{d['task'].id}</td>
          <th>服务任务</th><td class="mono break">{_esc(d['task'].service_task_id) or '-'}</td>
        </tr>
      </tbody></table>
    </section>"""

    # 审计依据与范围
    basis = f"""
    <section class="report-section">
      <h2 class="section-heading"><span class="heading-no">二</span>审计依据与范围</h2>
      <table class="kv-table"><tbody>
        <tr>
          <th>审计方式</th><td>AI 代码审查（静态阅读源码 + 逐条用例校验）</td>
          <th>触发方式</th><td>{_esc(d['trigger_label'])}</td>
        </tr>
        <tr>
          <th>用例来源</th><td>{_esc(d['case_source_label'])}</td>
          <th>用例总数</th><td>{d['total']} 条</td>
        </tr>
        <tr>
          <th>提交人</th><td>{_esc(d['created_by'])}</td>
          <th>检查时间</th><td>{_esc(d['checked_at'])}</td>
        </tr>
      </tbody></table>
    </section>"""

    # 审计概要
    summary = f"""
    <section class="report-section">
      <h2 class="section-heading"><span class="heading-no">三</span>审计概要</h2>
      <div class="summary-table-wrap">
        <table class="summary-table"><thead><tr>
          <th>用例总数</th><th>通过</th><th>未通过</th><th>异常</th><th>通过率</th><th>风险等级</th>
        </tr></thead><tbody><tr>
          <td class="num">{d['total']}</td>
          <td class="num pass">{d['pass_c']}</td>
          <td class="num fail">{d['fail_c']}</td>
          <td class="num error">{d['error_c']}</td>
          <td class="num">{_esc(d['pass_rate_text'])}</td>
          <td>{_risk_chip(d['task'].risk_level, d['task'].risk_score)}</td>
        </tr></tbody></table>
      </div>
      <p class="summary-verdict">{_esc(d['verdict'])}</p>
    </section>"""

    # 风险评估
    risk = _render_risk(d)

    # 审计发现
    findings = _render_findings(d)

    # 改进建议
    suggestions = _render_suggestions(d)

    # 附件：明细
    attachment = _render_attachment(d)

    report = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>代码检查审计报告 {_esc(d['report_no'])}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="report-wrap">
  <div class="report-paper">
    <header class="report-head">
      <div class="head-left">
        <h1 class="report-title">代码检查审计报告</h1>
        <p class="report-subtitle">CODE REVIEW AUDIT REPORT</p>
      </div>
      <div class="head-right">
        <div class="meta-row"><span class="meta-label">报告编号</span><span class="meta-value mono">{_esc(d['report_no'])}</span></div>
        <div class="meta-row"><span class="meta-label">生成时间</span><span class="meta-value">{_esc(d['generated_at'])}</span></div>
        <div class="meta-row"><span class="meta-label">审计结论</span><span class="meta-value">{_conclusion_badge(d['conclusion'], d['c_label'])}</span></div>
      </div>
    </header>
{audit_object}
{basis}
{summary}
{risk}
{findings}
{suggestions}
{attachment}
    <footer class="report-foot">
      <div class="foot-note">
        本报告由代码检查平台自动生成，结论基于检查当次的仓库快照（{_esc(d['commit_short'])}）与用例版本，
        用例内容如有变更需重新检查。AI 校验结论可能存在偏差，重要变更请结合人工复核。
      </div>
    </footer>
  </div>
</div>
</body>
</html>"""
    return report


def _risk_chip(level, score):
    if not level:
        return "-"
    cls = RISK_CLASS.get(level, "")
    return f'<span class="risk-chip {cls}">{_esc(level)} · {score}</span>'


def _conclusion_badge(conclusion, label):
    return f'<span class="conclusion-badge {conclusion or "none"}">{_esc(label)}</span>'


def _result_badge(result):
    cls = RESULT_CLASS.get(result, "none")
    return f'<span class="result-badge {cls}">{_esc(result)}</span>'


def _render_risk(d):
    if d["task"].risk_level:
        reason = f'<div class="paragraph">{_esc(d["task"].risk_reason)}</div>' if d["task"].risk_reason else ""
        files = ""
        if d["risk_files"]:
            tags = "".join(f'<span class="file-tag">{_esc(f)}</span>' for f in d["risk_files"])
            files = f'<div class="risk-files"><span class="block-label">高风险文件</span><div class="file-list">{tags}</div></div>'
        muted = '<div class="paragraph muted">未识别到高风险文件。</div>' if not d["risk_files"] else ""
        body = reason + files + muted
    else:
        body = '<div class="paragraph muted">本次未产生风险评估结论。</div>'
    return f"""
    <section class="report-section">
      <h2 class="section-heading"><span class="heading-no">四</span>风险评估</h2>
      {body}
    </section>"""


def _render_findings(d):
    items = d["findings"]
    if not items:
        body = '<div class="paragraph muted">本次检查未发现与预期不符的项。</div>'
    else:
        blocks = []
        for idx, r in enumerate(items, 1):
            ft = _failure_type_of(r)
            ft_badge = f'<span class="type-badge">{_esc(ft)}</span>' if ft else ""
            reason = _failure_reason_of(r)
            evs = _evidence_list(r)
            ev_html = ""
            if evs:
                tags = "".join(f'<span class="evidence-tag mono">{_esc(e)}</span>' for e in evs)
                ev_html = f'<div class="finding-item"><span class="finding-label">证据位置</span><div class="finding-text">{tags}</div></div>'
            expect_html = f'<div class="finding-item"><span class="finding-label">预期结果</span><div class="finding-text">{_esc(r["expectation"])}</div></div>' if r["expectation"] else ""
            blocks.append(f"""
        <div class="finding">
          <div class="finding-head">
            <span class="finding-no">{idx:02d}</span>
            <span class="finding-title"><span class="mono finding-case">{_esc(r["case_no"])}</span>{_esc(r["testpoint"]) or "未命名用例"}</span>
            {ft_badge}
            {_result_badge(r["result"])}
          </div>
          <div class="finding-body">
            <div class="finding-reason{_reason_fail_cls(r['result'])}"><span class="reason-label">失败原因</span><div class="reason-text">{_esc(reason)}</div></div>
            {ev_html}
            {expect_html}
            <div class="finding-item"><span class="finding-label">审计证据</span><div class="finding-text evidence">{_esc(r["reason"]) or "无校验理由"}</div></div>
          </div>
        </div>""")
        body = "\n".join(blocks)
    return f"""
    <section class="report-section">
      <h2 class="section-heading"><span class="heading-no">五</span>审计发现<span class="heading-note">未通过 / 异常项共 {len(items)} 条</span></h2>
      {body}
    </section>"""


def _render_suggestions(d):
    if not d["suggestions"]:
        body = '<div class="paragraph muted">无。</div>'
    else:
        items = "".join(f"<li>{_esc(s)}</li>" for s in d["suggestions"])
        body = f'<ol class="suggestion-list">{items}</ol>'
    return f"""
    <section class="report-section">
      <h2 class="section-heading"><span class="heading-no">六</span>改进建议</h2>
      {body}
    </section>"""


def _render_attachment(d):
    results = d["results"]
    if not results:
        body = '<div class="paragraph muted">无用例结果。</div>'
    else:
        rows = []
        for r in results:
            if r["result"] != PASS_RESULT:
                cell = f'<span class="cell-reason">{_esc(_brief(_failure_reason_of(r), 110))}</span>'
            else:
                cell = _esc(_brief(r["reason"]))
            ev = "，".join(_evidence_list(r)) or "-"
            rows.append(f"""<tr>
              <td class="mono">{_esc(r["case_no"])}</td>
              <td>{_esc(r["testpoint"]) or "-"}</td>
              <td>{_result_badge(r["result"])}</td>
              <td class="ellipsis">{cell}</td>
              <td class="ellipsis mono evidence-cell">{_esc(ev)}</td>
            </tr>""")
        body = f"""
        <table class="detail-table"><thead><tr>
          <th style="width:70px">编号</th><th>测试点</th><th style="width:74px">结果</th><th>失败原因 / 结论摘要</th><th style="width:170px">证据位置</th>
        </tr></thead><tbody>{"".join(rows)}</tbody></table>"""
    return f"""
    <section class="report-section">
      <h2 class="section-heading"><span class="heading-no">七</span>附件：用例执行明细<span class="heading-note">共 {len(results)} 条</span></h2>
      {body}
    </section>"""
