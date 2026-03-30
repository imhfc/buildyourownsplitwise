# Memory Bank

> 動態記憶系統 — Skill 引用的結構化配置 + 進度追蹤

---

## 目錄結構

```
memory-bank/
├── project-context/
│   ├── preferences.yaml     # Skill 引用的結構化配置（git-ops、parallel-develop）
│   ├── decisions.yaml       # 非 ADR 等級的決策記錄
│   ├── progress.yaml        # 當前衝刺與進行中任務
│   └── README.md
└── parallel-sessions/       # 並行開發會話管理
    ├── active/
    └── completed/
```

---

## 相關文檔

- [CLAUDE.md](../../CLAUDE.md) — AI 主配置
- [Skills 索引](../skills/README.md) — 可用 Skills
