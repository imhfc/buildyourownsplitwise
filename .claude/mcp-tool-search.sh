#!/bin/bash
# MCP Tool Search 自動觸發設定
# 用途：當 MCP 工具定義超過 5% context 時，自動載入相關 MCP Server
# 官方文檔：https://code.claude.com/docs/en/mcp.md

export ENABLE_TOOL_SEARCH=auto:5

echo "MCP Tool Search 已啟用 (auto:5)"
echo "   - 當 MCP 工具定義 > 5% context 時自動載入"
echo "   - 節省初始 context 使用量"
echo ""
echo "使用方式："
echo "  source .claude/mcp-tool-search.sh"
echo "  claude"
